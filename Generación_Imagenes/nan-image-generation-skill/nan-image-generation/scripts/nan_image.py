#!/usr/bin/env python3
"""Genera y edita imagenes con la API de NaN (compatible con OpenAI).

Solo stdlib: funciona sin pip install en cualquier instalacion de Hermes.

    nan_image.py generate --prompt-file p.txt --aspect 3:2 --long-side 1280
    nan_image.py edit --prompt-file p.txt --image ref1.png --image ref2.png
    nan_image.py models
    nan_image.py brief

Salida: imagenes en disco + un .json hermano con los parametros exactos
(prompt, modelo, size, seed) para poder reproducir o repetir la tirada.
"""

import argparse
import base64
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
import uuid

DEFAULT_MODEL = "qwen-image-2.1"
BASE_URL = os.environ.get("NAN_BASE_URL", "https://api.nan.builders/v1").rstrip("/")
KEY_ENVS = (
    "NAN_API_KEY",
    "NAN_BUILDERS_API_KEY",
    "HERMES_CUSTOM_API_NAN_BUILDERS_API_KEY",
    "OPENAI_API_KEY",
)

# Limites documentados por modelo (docs/models).
MODELS = {
    "qwen-image-2.1": {"min_side": 512, "max_side": 1280, "edits": False, "guidance": False},
    "flux-2-klein": {"min_side": 256, "max_side": 1536, "edits": True, "guidance": True},
}

STEP = 16
MAX_RATIO = 3.0

# Ultima linea de defensa, no la politica: solo terminos de altisima precision.
# La decision etica la toma el agente antes de llegar aqui (ver SKILL.md).
HARD_BLOCK = re.compile(
    r"(csam|child\s*porn|child\s*sexual|loli|shotacon|underage\s*nude"
    r"|menor(?:es)?\s+de\s+edad\s+(?:desnud|en\s+postura\s+sexual|en\s+actitud\s+sexual))",
    re.I,
)


class ApiError(Exception):
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload
        super().__init__(f"HTTP {status}: {payload}")


def eprint(*a):
    print(*a, file=sys.stderr)


def read_prompt(args):
    if args.prompt_file:
        if args.prompt_file == "-":
            text = sys.stdin.read()
        else:
            with open(args.prompt_file, "r", encoding="utf-8") as fh:
                text = fh.read()
    else:
        text = args.prompt or ""
    text = " ".join(text.split())
    if not text:
        eprint("error: prompt vacio. Usa --prompt o --prompt-file.")
        sys.exit(2)
    if HARD_BLOCK.search(text):
        eprint(
            "error: la peticion entra en una categoria bloqueada (contenido sexual con menores). "
            "No se puede reformular ni reintentar. Explica al usuario que no es posible."
        )
        sys.exit(3)
    if len(text) > 1400:
        eprint(
            f"aviso: prompt de {len(text)} caracteres. Por encima de ~1000 el detalle se diluye: "
            "quita adjetivos y deja los sustantivos concretos."
        )
    return text


def api_key(explicit=None):
    if explicit:
        return explicit
    for name in KEY_ENVS:
        val = os.environ.get(name)
        if val:
            return val.strip()
    eprint(
        "error: falta la clave. Exporta NAN_API_KEY=sk-... "
        "(o pasa --api-key). Se obtiene en cloud.nan.builders -> Settings -> API Keys."
    )
    sys.exit(2)


def snap(value, lo, hi):
    v = int(round(value / STEP)) * STEP
    return max(lo, min(hi, v))


def parse_aspect(text):
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*[:x/]\s*(\d+(?:\.\d+)?)\s*", text)
    if not m:
        eprint(f"error: aspect ratio no valido: {text!r}. Ejemplos: 1:1, 3:2, 16:9, 9:16.")
        sys.exit(2)
    a, b = float(m.group(1)), float(m.group(2))
    if a <= 0 or b <= 0:
        eprint("error: aspect ratio debe ser positivo.")
        sys.exit(2)
    return a, b


def compute_size(aspect, long_side, model):
    """Devuelve 'WxH' encajado en los limites del modelo, lados multiplos de 16."""
    cfg = MODELS[model]
    lo, hi = cfg["min_side"], cfg["max_side"]
    a, b = parse_aspect(aspect)
    ratio = a / b
    if ratio > MAX_RATIO or ratio < 1 / MAX_RATIO:
        eprint(f"error: relacion de aspecto {aspect} fuera de 1:3-3:1 (limite de la API).")
        sys.exit(2)
    long_side = max(lo, min(hi, int(long_side)))
    if a >= b:
        w, h = long_side, long_side * b / a
    else:
        h, w = long_side, long_side * a / b
    w, h = snap(w, lo, hi), snap(h, lo, hi)
    if w < lo or h < lo:
        eprint(f"error: con {aspect} no se puede respetar el minimo de {lo}px por lado. Usa un ratio menos extremo.")
        sys.exit(2)
    real = w / h
    if not (0.94 < real / ratio < 1.06):
        eprint(f"aviso: el ratio real es {w}x{h} ({real:.3f}), no exactamente {aspect}.")
    return f"{w}x{h}"


def validate_explicit_size(size, model):
    m = re.fullmatch(r"(\d+)x(\d+)", size.strip())
    if not m:
        eprint(f"error: --size debe ser WxH, no {size!r}.")
        sys.exit(2)
    w, h = int(m.group(1)), int(m.group(2))
    cfg = MODELS[model]
    lo, hi = cfg["min_side"], cfg["max_side"]
    problems = []
    for label, v in (("ancho", w), ("alto", h)):
        if v % STEP:
            problems.append(f"{label} {v} no es multiplo de 16")
        if not (lo <= v <= hi):
            problems.append(f"{label} {v} fuera de {lo}-{hi} para {model}")
    if not (1 / MAX_RATIO <= w / h <= MAX_RATIO):
        problems.append(f"ratio {w/h:.2f} fuera de 1:3-3:1")
    if problems:
        eprint("error: size invalido: " + "; ".join(problems))
        sys.exit(2)
    return f"{w}x{h}"


def request_json(method, path, key, body=None, timeout=300):
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        method=method,
        headers=headers,
    )
    return _send(req, timeout)


def request_multipart(path, key, fields, files, timeout=300):
    boundary = "----nan" + uuid.uuid4().hex
    chunks = []
    for name, value in fields:
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        chunks.append(f"{value}\r\n".encode())
    for name, (filename, payload) in files:
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        chunks.append(f"Content-Type: {guess_mime(payload)}\r\n\r\n".encode())
        chunks.append(payload + b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=b"".join(chunks),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
    )
    return _send(req, timeout)


def _send(req, timeout):
    """POST/GET con reintentos para 429/5xx. No reintenta cuota agotada."""
    attempts, last = 4, None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            try:
                payload = json.loads(raw)
            except Exception:
                payload = {"raw": raw[:400]}
            code = (payload.get("error") or {}).get("code")
            last = ApiError(exc.code, payload)
            if code in ("quota_exceeded", "insufficient_quota"):
                raise last
            if exc.code in (400, 401, 403, 404) or attempt == attempts - 1:
                raise last
            suggested = float(exc.headers.get("Retry-After") or 0)
            wait = min(suggested or 2 ** attempt * 2, 30)
            eprint(f"aviso: HTTP {exc.code}, reintento en {wait:.0f}s ({attempt + 1}/{attempts})")
            time.sleep(wait)
        except urllib.error.URLError as exc:
            last = exc
            if attempt == attempts - 1:
                raise
            wait = min(2 ** attempt * 2, 20)
            eprint(f"aviso: red ({exc.reason}), reintento en {wait}s ({attempt + 1}/{attempts})")
            time.sleep(wait)
    raise last


def guess_mime(payload):
    if payload.startswith(b"\x89PNG"):
        return "image/png"
    if payload.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if payload[:4] == b"RIFF" and payload[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


def image_dims(payload):
    try:
        if payload.startswith(b"\x89PNG\r\n\x1a\n"):
            w = int.from_bytes(payload[16:20], "big")
            h = int.from_bytes(payload[20:24], "big")
            return w, h, "png"
        if payload.startswith(b"\xff\xd8"):
            i = 2
            while i < len(payload) - 9:
                if payload[i] != 0xFF:
                    i += 1
                    continue
                marker = payload[i + 1]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h = int.from_bytes(payload[i + 5:i + 7], "big")
                    w = int.from_bytes(payload[i + 7:i + 9], "big")
                    return w, h, "jpg"
                if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                    i += 2
                else:
                    i += 2 + int.from_bytes(payload[i + 2:i + 4], "big")
            return None
        if payload[:4] == b"RIFF" and payload[8:12] == b"WEBP":
            chunk = payload[12:16]
            if chunk == b"VP8X":
                w = 1 + int.from_bytes(payload[24:27], "little")
                h = 1 + int.from_bytes(payload[27:30], "little")
                return w, h, "webp"
            if chunk == b"VP8 ":
                w = int.from_bytes(payload[26:28], "little") & 0x3FFF
                h = int.from_bytes(payload[28:30], "little") & 0x3FFF
                return w, h, "webp"
            if chunk == b"VP8L":
                bits = int.from_bytes(payload[21:25], "little")
                return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1, "webp"
    except Exception:
        return None
    return None


def download(url, attempts=3):
    last = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "hermes-nan-image/1.0"})
            with urllib.request.urlopen(req, timeout=180) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001 - la URL caduca, reintentar es la norma
            last = exc
            time.sleep(1 + attempt * 2)
    raise RuntimeError(f"no se pudo descargar la imagen temporal: {last}")


def slugify(text, limit=40):
    ascii_text = (
        text.replace("á", "a").replace("é", "e").replace("í", "i")
        .replace("ó", "o").replace("ú", "u").replace("ñ", "n").replace("ü", "u")
    )
    s = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    return (s[:limit].rstrip("-") or "imagen")


def save_outputs(result, prompt, meta, outdir):
    os.makedirs(outdir, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    base = f"{stamp}_{slugify(prompt)}"
    written, problems = [], []
    for idx, item in enumerate(result.get("data") or []):
        if item.get("b64_json"):
            payload = base64.b64decode(item["b64_json"])
        elif item.get("url"):
            try:
                payload = download(item["url"])
            except RuntimeError as exc:
                problems.append(str(exc))
                continue
        else:
            problems.append("la respuesta no traia ni url ni b64_json")
            continue
        dims = image_dims(payload)
        if not dims or len(payload) < 1024:
            problems.append(f"el item {idx + 1} no parece una imagen valida ({len(payload)} bytes)")
            continue
        w, h, ext = dims
        path = os.path.join(outdir, f"{base}_{idx + 1}.{ext}")
        with open(path, "wb") as fh:
            fh.write(payload)
        record = dict(meta)
        record.update({"file": os.path.abspath(path), "width": w, "height": h, "bytes": len(payload),
                       "created": result.get("created")})
        sidecar = os.path.splitext(path)[0] + ".json"
        with open(sidecar, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False, indent=2)
        written.append((path, w, h, len(payload)))
    return written, problems


def fail(exc):
    if isinstance(exc, ApiError):
        err = exc.payload.get("error") or {}
        msg = err.get("message") or json.dumps(exc.payload)[:300]
        code = err.get("code") or "?"
        hints = {
            400: "Revisa size (multiplos de 16, dentro del rango del modelo), n (1-4) y el prompt.",
            401: "Clave invalida o revocada: genera una nueva en cloud.nan.builders -> API Keys.",
            403: "Falta el tier 'inference' en la cuenta (o la clave es de workspace).",
            404: "model_not_found: el id debe ser exactamente qwen-image-2.1 o flux-2-klein.",
            429: "Limite de imagenes: 20/min y 100/mes por usuario (cuota compartida entre los dos modelos).",
        }
        print(f"ERROR {exc.status} [{code}]: {msg}", file=sys.stderr)
        if exc.status in hints:
            print(f"  -> {hints[exc.status]}", file=sys.stderr)
        return 1
    print(f"ERROR: {exc}", file=sys.stderr)
    return 1


def cmd_generate(args):
    model = args.model
    if model not in MODELS:
        eprint(f"error: modelo desconocido {model!r}. Disponibles: {', '.join(MODELS)}.")
        return 2
    prompt = read_prompt(args)
    if args.size:
        size = validate_explicit_size(args.size, model)
    else:
        size = compute_size(args.aspect, args.long_side, model)
    seed = args.seed if args.seed is not None else random.randint(0, 2147483647)
    body = {
        "model": model,
        "prompt": prompt,
        "n": args.n,
        "size": size,
        "response_format": "url",
        "seed": seed,
    }
    if args.guidance is not None:
        if not MODELS[model]["guidance"]:
            eprint("aviso: guidance es extension de FLUX; se omite con " + model)
        else:
            body["guidance"] = args.guidance
    meta = {"endpoint": "/images/generations", "body": body}
    if args.dry_run:
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        return 0
    key = api_key(args.api_key)
    try:
        result = request_json("POST", "/images/generations", key, body)
    except Exception as exc:  # noqa: BLE001
        return fail(exc)
    return report(result, prompt, meta, args)


def cmd_edit(args):
    model = args.model
    if model not in MODELS:
        eprint(f"error: modelo desconocido {model!r}. Disponibles: {', '.join(MODELS)}.")
        return 2
    if not MODELS[model]["edits"]:
        eprint(
            f"error: {model} no tiene endpoint de edicion (solo text-to-image). "
            "Para editar usa --model flux-2-klein."
        )
        return 2
    if not args.image:
        eprint("error: --image es obligatorio en modo edicion (hasta 4, repetible).")
        return 2
    prompt = read_prompt(args)
    if args.size:
        size = validate_explicit_size(args.size, model)
    else:
        size = compute_size(args.aspect, args.long_side, model)
    seed = args.seed if args.seed is not None else random.randint(0, 2147483647)
    fields = [("model", model), ("prompt", prompt), ("n", str(args.n)), ("size", size),
              ("response_format", "url"), ("seed", str(seed))]
    if args.guidance is not None:
        fields.append(("guidance", str(args.guidance)))
    files = []
    for path in args.image[:4]:
        with open(path, "rb") as fh:
            payload = fh.read()
        if len(payload) > 25 * 1024 * 1024:
            eprint(f"error: {path} supera 25 MB (limite por referencia).")
            return 2
        files.append(("image[]", (os.path.basename(path), payload)))
    if len(args.image) > 4:
        eprint("aviso: solo se envian las 4 primeras referencias.")
    meta = {"endpoint": "/images/edits",
            "body": {"model": model, "prompt": prompt, "n": args.n, "size": size,
                     "seed": seed, "images": [os.path.abspath(p) for p in args.image[:4]]}}
    if args.dry_run:
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        return 0
    key = api_key(args.api_key)
    try:
        result = request_multipart("/images/edits", key, fields, files)
    except Exception as exc:  # noqa: BLE001
        return fail(exc)
    return report(result, prompt, meta, args)


def report(result, prompt, meta, args):
    written, problems = save_outputs(result, prompt, meta, args.out)
    for msg in problems:
        eprint("aviso: " + msg)
    if not written:
        eprint("error: la API respondio 200 pero no se guardo ninguna imagen.")
        return 1
    if args.json:
        print(json.dumps({"images": [
            {"file": os.path.abspath(p), "width": w, "height": h, "bytes": b} for p, w, h, b in written
        ]}, ensure_ascii=False, indent=2))
        return 0
    print(f"OK: {len(written)} imagen(es) con {meta['body']['model']} a {meta['body']['size']}, "
          f"seed {meta['body']['seed']}")
    for p, w, h, b in written:
        print(f"  {os.path.abspath(p)}  ({w}x{h}, {b / 1024:.0f} KB)")
    print(f"  parametros: {os.path.splitext(os.path.abspath(written[0][0]))[0]}.json")
    print("  (la URL de origen caduca en ~60 min; el archivo ya esta en disco)")
    return 0


def cmd_models(args):
    key = api_key(args.api_key)
    try:
        data = request_json("GET", "/models", key, None)
    except Exception as exc:  # noqa: BLE001
        return fail(exc)
    ids = sorted(m.get("id", "") for m in data.get("data") or [])
    for mid in ids:
        mark = "  <- por defecto" if mid == DEFAULT_MODEL else ""
        print(mid + mark)
    missing = [m for m in MODELS if m not in ids]
    if missing:
        eprint("aviso: no aparecen en tu lista: " + ", ".join(missing) + " (¿tier o clave?)")
    return 0 if ids else 1


def cmd_brief(args):
    print(BRIEF)
    return 0


BRIEF = """\
Cuestionario de brief (los * son obligatorios; el resto se pide igualmente)

usecase      * Use Case Category ...... que decision resuelve la imagen
subject      * Subject ................. quien o que aparece, en una frase
action         Action / Activity ...... que esta pasando
setting        Setting / Location ..... donde y cuando
style          Art Style .............. fotografia, ilustracion, 3D, grabado...
composition    Composition / Camera ... plano, angulo, regla de tercios
lighting       Lighting & Mood ........ hora, direccion, temperatura, emocion
bg             Background Mode ........ limpio / contextual / degradado / transparente
palette        Color Palette .......... colores dominantes o hex
lens           Camera / Lens / Film ... 35mm, macro, Portra 400
ratio          Aspect Ratio ........... 1:1, 3:2, 16:9, 9:16, 4:5
resolution     Resolution ............. lado largo en px (1024 por defecto)
mode           Generation Mode ........ text-to-image o image-to-image
preserve       Preserve (edit) ........ que no debe cambiar
text           Text to Include ........ texto literal, idioma y ubicacion
unwanted       Negative Constraints ... lo que no quieres ver
use            Intended Use ........... web, impresion, redes, presentacion
"""


def main():
    p = argparse.ArgumentParser(description="Genera y edita imagenes con la API de NaN.")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp, edit=False):
        sp.add_argument("--prompt", help="texto del prompt")
        sp.add_argument("--prompt-file", help="fichero con el prompt ('-' para stdin)")
        sp.add_argument("--model", default=DEFAULT_MODEL, help=f"por defecto {DEFAULT_MODEL}")
        sp.add_argument("--aspect", default="1:1", help="1:1, 3:2, 16:9, 9:16, 4:5...")
        sp.add_argument("--long-side", type=int, default=1024, help="lado largo en px")
        sp.add_argument("--size", help="WxH exacto (tiene prioridad sobre --aspect)")
        sp.add_argument("--n", type=int, default=1, choices=[1, 2, 3, 4])
        sp.add_argument("--seed", type=int)
        sp.add_argument("--guidance", type=float, help="solo flux-2-klein")
        sp.add_argument("--out", default=".", help="directorio de salida")
        sp.add_argument("--api-key")
        sp.add_argument("--dry-run", action="store_true", help="muestra el cuerpo y no llama a la API")
        sp.add_argument("--json", action="store_true", help="salida JSON")

    g = sub.add_parser("generate", help="text-to-image")
    common(g)
    g.set_defaults(func=cmd_generate)

    e = sub.add_parser("edit", help="image-to-image (solo flux-2-klein)")
    common(e, edit=True)
    e.add_argument("--image", action="append", help="referencia local (repetible, max 4)")
    e.set_defaults(func=cmd_edit)

    m = sub.add_parser("models", help="lista los modelos de tu clave")
    m.add_argument("--api-key")
    m.set_defaults(func=cmd_models)

    b = sub.add_parser("brief", help="imprime el cuestionario de campos")
    b.set_defaults(func=cmd_brief)

    args = p.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
