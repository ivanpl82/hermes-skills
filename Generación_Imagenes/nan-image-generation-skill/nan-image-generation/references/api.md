# Contrato de la API (NaN)

Base URL: `https://api.nan.builders/v1` (Helmcode: `https://api.helmcode.com/v1`, idéntico).
Auth: `Authorization: Bearer sk-...`. Solo HTTPS. Todos los endpoints de inferencia exigen tier `inference`.

## POST /images/generations — text-to-image

Cuerpo JSON. `prompt` es el único campo obligatorio.

| Campo | Tipo | Límites / notas |
|---|---|---|
| `prompt` | string | descripción de la imagen |
| `model` | string | `qwen-image-2.1` o `flux-2-klein`; desconocido → 404 `model_not_found` |
| `n` | int | 1–4 (por defecto 1); >4 → 400 |
| `size` | string | `"ANCHOxALTO"`, lados múltiplos de 16; `auto` u omitido → `1024x1024` |
| `response_format` | string | `url` (por defecto, caduca ~60 min) o `b64_json` |
| `seed` | int | extensión NaN, 0–2147483647; reproducible por modelo |
| `guidance` | number | extensión NaN, solo FLUX |

Rango de `size` por modelo: **qwen-image-2.1 512–1280**; **flux-2-klein 256–1536**. Ratio permitido 1:3–3:1.

Se aceptan y **se ignoran**: `quality`, `style`, `background`, `moderation`, `output_format`, `output_compression`, `user`. `stream: true` no está soportado.

Respuesta:

```json
{"created": 1778258200,
 "data": [{"url": "https://...r2.../image.png"}]}
```

Con `b64_json`, cada elemento trae `b64_json` en lugar de `url`. El formato real del archivo puede ser PNG, JPEG o WebP: no lo asumas por la extensión, mira los bytes.

## POST /images/edits — image-to-image

`multipart/form-data`. Solo `flux-2-klein`. `image` obligatorio: 1–4 referencias en PNG/JPEG/WebP, <25 MB cada una; para varias, repite el campo como `image[]`. `prompt`, `n`, `size`, `response_format`, `seed`, `guidance` igual que arriba. `mask` **no** está soportado (400).

## GET /models

Lista los modelos disponibles para la clave. Sirve de comprobación previa: si `qwen-image-2.1` no aparece, el problema es de tier o de clave, no del script.

## Errores

Envoltorio estándar de OpenAI:

```json
{"error": {"message": "...", "type": null, "param": null, "code": "..."}}
```

| HTTP | `code` típico | Significado |
|---|---|---|
| 400 | `invalid_request_error` | size/n mal, o rechazo de contenido |
| 401 | `invalid_api_key` | clave inválida o revocada |
| 403 | — | falta tier `inference`; clave de workspace rechazada |
| 404 | `model_not_found` | id de modelo mal escrito |
| 429 | `rate_limit_exceeded` | >20 peticiones/min |
| 429 | `quota_exceeded`, `insufficient_quota` | 100 imágenes/mes agotadas (no reintentar) |
| 502/503 | — | clúster saturado; reintentar con espera |

Los errores de 400 por política de contenido **no** se reintentan reformulando el prompt.

## Límites de uso

- **20 peticiones/minuto** y **100 imágenes/mes** por usuario, contador propio (no consume tokens de chat) y **compartido** entre `qwen-image-2.1` y `flux-2-klein`.
- La URL de salida caduca en ~60 minutos: descarga inmediata o `b64_json`.

## curl equivalente

Sin script (útil para depurar a mano; no imprime la clave):

```bash
curl -sS https://api.nan.builders/v1/images/generations \
  -H "Authorization: Bearer $NAN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-image-2.1","prompt":"a lighthouse at dusk","size":"1280x720","n":1,"seed":42}' \
  | tee /tmp/resp.json
python3 -c "import json;print(json.load(open('/tmp/resp.json'))['data'][0]['url'])"
```

Edición:

```bash
curl -sS https://api.nan.builders/v1/images/edits \
  -H "Authorization: Bearer $NAN_API_KEY" \
  -F model=flux-2-klein \
  -F prompt="Change only the sky to dusk" \
  -F size=1024x1024 \
  -F "image[]=@ref1.png" -F "image[]=@ref2.png"
```

Con SDK de OpenAI: mismo endpoint y mismos campos; `seed` y `guidance` van por `extra_body`.

## Notas de operación

- El proveedor devuelve 502 esporádicos con `Retry-After: 60` aunque la cuenta esté bien. El script reintenta limitando la espera a 30 s por intento; si tras eso falla, es saturación real.
- La API es síncrona: no hay polling ni job id. Una llamada tarda decenas de segundos.
- `response_format: "url"` es lo que usa el script por defecto; si la descarga falla, se puede repetir con `b64_json` (misma cuota, otra llamada).
