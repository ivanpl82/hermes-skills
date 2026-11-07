#!/usr/bin/env python3
"""opendata.py — Consultas a portales de datos abiertos de España (solo stdlib).

Cubre las cuatro familias de API verificadas:

  CKAN     Madrid, Aragón, Navarra, Valencia, Murcia, Andalucía, Castilla-La Mancha
  Socrata  Cataluña (analisi.transparenciacatalunya.cat)
  SPARQL   Euskadi (api.euskadi.eus)
  Estatal  datos.gob.es (linked-data-api v0.2, catálogo agregado de toda España)

Ejemplos:
  python3 opendata.py portales --check
  python3 opendata.py ckan madrid search "calidad del aire" --rows 5
  python3 opendata.py ckan aragon orgs --limit 10
  python3 opendata.py ckan navarra dataset <dataset-id>
  python3 opendata.py socrata search "covid" --limit 5
  python3 opendata.py socrata rows xuwf-dxjd --limit 3
  python3 opendata.py sparql "SELECT ?s WHERE { ?s a ?o } LIMIT 5"
  python3 opendata.py gob datasets --grep "ruido" --pages 3
  python3 opendata.py gob dataset https://datos.gob.es/catalogo/e05068001-mapas-estrategicos-de-ruido

Salida: tabla compacta por defecto; --json para la respuesta cruda.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "hermes-agent-opendata/1.0"
TIMEOUT = 25
RETRIES = 2

CKAN = {
    "madrid": "https://datos.comunidad.madrid/api/3/action",
    "aragon": "https://opendata.aragon.es/aod/api/3/action",
    "navarra": "https://datosabiertos.navarra.es/api/3/action",
    "valencia": "https://dadesobertes.gva.es/api/3/action",
    "murcia": "https://datosabiertos.regiondemurcia.es/api/3/action",
    "andalucia": "https://www.juntadeandalucia.es/datosabiertos/portal/api/3/action",
    "clm": "https://datosabiertos.castillalamancha.es/api/3/action",
}

SOCRATA = {"cataluna": "https://analisi.transparenciacatalunya.cat"}
SPARQL = {"euskadi": "https://api.euskadi.eus/sparql"}
GOB = "https://datos.gob.es/apidata"

# Portales sin API abierta confirmada: se consultan vía datos.gob.es (ver references/portales.md).
SIN_API = ("asturias", "cantabria", "extremadura", "galicia", "rioja", "baleares",
           "canarias", "castillayleon", "ceuta", "melilla")


class ApiError(RuntimeError):
    pass


# --------------------------------------------------------------------------- http

def _request(url: str, params: dict | None = None, data: bytes | None = None,
             accept: str = "application/json", timeout: int = TIMEOUT) -> bytes:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    last: Exception | None = None
    for attempt in range(RETRIES + 1):
        req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Accept": accept})
        if data is not None:
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code < 500:
                body = exc.read()[:300].decode("utf-8", "replace")
                raise ApiError(f"HTTP {exc.code} en {url} — {body}") from None
            last = exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
        if attempt < RETRIES:
            time.sleep(1.5 * (attempt + 1))
    raise ApiError(f"sin respuesta de {url} ({last})")


def get_json(url: str, params: dict | None = None, timeout: int = TIMEOUT):
    raw = _request(url, params=params, timeout=timeout)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ApiError(f"respuesta no-JSON de {url} ({exc}); ¿falta la extensión .json?") from None


# --------------------------------------------------------------------------- output

def out_json(data) -> None:
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2, default=str)
    sys.stdout.write("\n")


def out_table(rows: list[list], headers: list[str], max_col: int = 58) -> None:
    if not rows:
        print("(sin resultados)")
        return
    rows = [[("" if c is None else str(c))[:max_col] for c in r] for r in rows]
    widths = [max(len(headers[i]), *(len(r[i]) for r in rows)) for i in range(len(headers))]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(line)
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)))


def _first(value) -> str:
    """Campo de datos.gob.es: str, {'_value':..}, o lista de ambos."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("_value") or value.get("title") or "")
    if isinstance(value, list):
        return _first(value[0]) if value else ""
    return str(value)


# --------------------------------------------------------------------------- CKAN

def _ckan_api(portal: str) -> str:
    key = portal.rstrip("/")
    if key in CKAN:
        return CKAN[key]
    if key.startswith("http"):
        return key if "/action" in key else key.rstrip("/") + "/api/3/action"
    raise ApiError(f"portal CKAN desconocido: {portal}. Válidos: {', '.join(CKAN)}")


def ckan_call(portal: str, action: str, params: dict | None = None):
    data = get_json(f"{_ckan_api(portal)}/{action}", params)
    if not data.get("success"):
        raise ApiError(f"CKAN {action} falló: {data.get('error')}")
    return data["result"]


def _fmt_formats(resources: list) -> str:
    fmts = sorted({_short_format(r) for r in resources if isinstance(r, dict)})
    return ",".join(fmts)[:40]


def _short_format(obj: dict) -> str:
    """`format` puede ser 'CSV' o una URI de vocabulario (…/file-type/CSV)."""
    value = str(obj.get("format") or "")
    if value.startswith("http"):
        value = value.rstrip("/").rsplit("/", 1)[-1]
    return (value or "?").upper()


def cmd_ckan_search(args) -> None:
    res = ckan_call(args.portal, "package_search",
                    {"q": args.query or "*:*", "rows": args.rows, "start": args.start})
    if args.json:
        return out_json(res)
    rows = []
    for ds in res.get("results", []):
        rows.append([
            str(ds.get("title") or ds.get("name")),
            (ds.get("organization") or {}).get("title", ""),
            len(ds.get("resources") or []),
            _fmt_formats(ds.get("resources") or []),
            ds.get("name", ""),
        ])
    print(f"total={res.get('count', 0)}  mostrados={len(rows)}  portal={args.portal}")
    out_table(rows, ["titulo", "organizacion", "n", "formatos", "id"])


def cmd_ckan_orgs(args) -> None:
    orgs = ckan_call(args.portal, "organization_list", {"all_fields": "true"})
    if args.json:
        return out_json(orgs)
    rows = [[str(o.get("title") or o.get("name")), o.get("package_count", 0), o.get("name", "")]
            for o in sorted(orgs, key=lambda o: -(o.get("package_count") or 0))[: args.limit]]
    print(f"organizaciones={len(orgs)}  portal={args.portal}")
    out_table(rows, ["organizacion", "datasets", "slug"])


def cmd_ckan_dataset(args) -> None:
    ds = ckan_call(args.portal, "package_show", {"id": args.id})
    if args.json:
        return out_json(ds)
    print(f"# {ds.get('title')}\n")
    print(f"org:      {(ds.get('organization') or {}).get('title', '')}")
    print(f"id:       {ds.get('name')}")
    print(f"modif:    {ds.get('metadata_modified', '')}")
    print(f"tags:     {', '.join(t.get('display_name', '') for t in ds.get('tags') or [])}")
    print(f"\n{str(ds.get('notes') or '')[:800]}\n")
    out_table([[r.get("format", ""), str(r.get("name") or "")[:40], r.get("url", "")]
               for r in ds.get("resources") or []], ["formato", "recurso", "url"], max_col=80)


def cmd_ckan_dispatch(args) -> None:
    """`ckan <portal> <acción> [opciones]` — el portal va antes que la acción."""
    parser = argparse.ArgumentParser(prog=f"opendata.py ckan {args.portal}")
    subs = parser.add_subparsers(dest="action", required=True)
    s = subs.add_parser("search", help="búsqueda textual (q)")
    s.add_argument("query", nargs="?", default="*:*")
    s.add_argument("--rows", type=int, default=10)
    s.add_argument("--start", type=int, default=0)
    s.add_argument("--json", action="store_true")
    s = subs.add_parser("orgs", help="organizaciones publicadoras")
    s.add_argument("--limit", type=int, default=15)
    s.add_argument("--json", action="store_true")
    s = subs.add_parser("dataset", help="detalle de un dataset por id/slug")
    s.add_argument("id")
    s.add_argument("--json", action="store_true")
    parsed = parser.parse_args(args.rest)
    args.action = parsed.action
    for key, value in vars(parsed).items():
        if key not in ("action",):
            setattr(args, key, value)
    {"search": cmd_ckan_search, "orgs": cmd_ckan_orgs, "dataset": cmd_ckan_dataset}[args.action](args)


# --------------------------------------------------------------------------- Socrata

def _socrata(domain: str) -> str:
    return SOCRATA.get(domain.rstrip("/"), domain.rstrip("/"))


def cmd_socrata_search(args) -> None:
    data = get_json(f"{_socrata(args.domain)}/api/catalog/v1",
                    {"q": args.query, "limit": args.limit})
    if args.json:
        return out_json(data)
    rows = []
    for hit in data.get("results", []):
        r = hit.get("resource", {})
        rows.append([str(r.get("name", ""))[:60], r.get("id", ""), str(r.get("updatedAt", ""))[:10]])
    print(f"resultados={data.get('resultSetSize', len(rows))}  dominio={args.domain}")
    out_table(rows, ["dataset", "id", "actualizado"])


def cmd_socrata_rows(args) -> None:
    params = {"$limit": args.limit}
    if args.where:
        params["$where"] = args.where
    if args.select:
        params["$select"] = args.select
    if args.order:
        params["$order"] = args.order
    data = get_json(f"{_socrata(args.domain)}/resource/{args.dataset}.json", params)
    if args.json:
        return out_json(data)
    if not isinstance(data, list) or not data:
        return print("(sin filas)")
    cols = list(data[0])
    out_table([[r.get(c, "") for c in cols] for r in data], cols, max_col=32)


# --------------------------------------------------------------------------- SPARQL

def cmd_sparql(args) -> None:
    endpoint = SPARQL.get(args.endpoint.rstrip("/"), args.endpoint)
    raw = _request(endpoint, data=urllib.parse.urlencode({"query": args.query}).encode(),
                   accept="application/sparql-results+json", timeout=args.timeout)
    data = json.loads(raw)
    if args.json:
        return out_json(data)
    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        return print("(0 filas)")
    cols = data.get("head", {}).get("vars", list(bindings[0]))
    rows = [[str(b.get(c, {}).get("value", ""))[:68] for c in cols] for b in bindings]
    print(f"filas={len(rows)}  endpoint={args.endpoint}")
    out_table(rows, cols, max_col=70)


# --------------------------------------------------------------------------- datos.gob.es

GOB_FIELDS = ("title", "description", "keyword", "publisher", "theme", "spatial")


def gob_paginate(endpoint: str, params: dict, pages: int, page_size: int, delay: float):
    """Recorre `next` hasta agotar o `pages` páginas. La API no da totalCount."""
    params = dict(params, _pageSize=str(min(page_size, 50)))
    for page in range(pages):
        params["_page"] = str(page)
        data = get_json(f"{GOB}/{endpoint}.json", params)
        result = data.get("result", {})
        items = result.get("items") or []
        if items:
            yield items
        if "next" not in result:
            return
        time.sleep(delay)


def cmd_gob_datasets(args) -> None:
    params: dict[str, str] = {}
    if args.publisher:
        params["publisher"] = args.publisher
    if args.format:
        params["format"] = args.format
    if args.modified_begin:
        params["modified"] = ">=" + args.modified_begin

    items: list[dict] = []
    for page in gob_paginate("catalog/dataset", params, args.pages, args.page_size, args.delay):
        items.extend(page)

    scanned = len(items)
    if args.grep:
        needle = args.grep.lower()
        items = [i for i in items
                 if any(needle in _first(i.get(f)).lower() for f in GOB_FIELDS)]

    if args.json:
        return out_json(items)

    rows = []
    for i in items[: args.limit]:
        dist = i.get("distribution")
        dists = dist if isinstance(dist, list) else ([dist] if dist else [])
        fmts = ",".join(sorted({_short_format(d) for d in dists if isinstance(d, dict)}))[:28]
        slug = str(i.get("_about") or "").rstrip("/").rsplit("/", 1)[-1]
        rows.append([str(_first(i.get("title")))[:56], _first(i.get("publisher"))[-24:],
                     len(dists), fmts, slug])
    print(f"examinados={scanned}  coincidencias={len(items)}  (páginas={args.pages}, tamaño={args.page_size})")
    out_table(rows, ["titulo", "publicador", "dist", "formatos", "slug"])


def cmd_gob_dataset(args) -> None:
    ref = args.identifier.rstrip("/").rsplit("/", 1)[-1]
    data = get_json(f"{GOB}/catalog/dataset/{ref}.json")
    items = data.get("result", {}).get("items") or []
    if not items:
        raise ApiError(f"sin resultado para '{ref}'. Usa el slug de _about "
                       "(p. ej. e05068001-mapas-estrategicos-de-ruido), no el UUID.")
    ds = items[0]
    if args.json:
        return out_json(ds)
    print(f"# {_first(ds.get('title'))}\n")
    print(f"publicador: {_first(ds.get('publisher'))}")
    print(f"temas:      {', '.join(_first(t) for t in (ds.get('theme') or []))}")
    print(f"spatial:    {_first(ds.get('spatial'))}")
    print(f"modificado: {_first(ds.get('modified'))}")
    print(f"licencia:   {_first(ds.get('license'))}")
    print(f"\n{_first(ds.get('description'))[:900]}\n")
    dist = ds.get("distribution")
    dists = dist if isinstance(dist, list) else ([dist] if dist else [])
    out_table([[_short_format(d)[:18], str(d.get("accessURL") or "")[:70]]
               for d in dists if isinstance(d, dict)], ["formato", "accessURL"], max_col=80)


def cmd_gob_publishers(args) -> None:
    items: list = []
    for page in gob_paginate("catalog/publisher", {}, args.pages, 50, 0.2):
        items.extend(page)
    if args.json:
        return out_json(items)
    uris = [_first(i) for i in items]
    print(f"publicadores={len(uris)} (páginas={args.pages})")
    for uri in uris[: args.limit]:
        print("  " + uri)


def cmd_gob_themes(args) -> None:
    data = get_json(f"{GOB}/catalog/theme.json")
    items = data.get("result", {}).get("items") or []
    if args.json:
        return out_json(items)
    # La API alterna URI suelta y objeto {"prefLabel", "_about"}: se emparejan por _about.
    labels: dict[str, str] = {}
    for it in items:
        if isinstance(it, dict) and it.get("prefLabel"):
            labels[str(it.get("_about") or it.get("prefLabel"))] = str(it["prefLabel"])
    lines = []
    for it in items:
        key = str(it.get("_about")) if isinstance(it, dict) else str(it)
        if labels.get(key):
            line = f"{labels[key]}  [{key.rstrip('/').rsplit('/', 1)[-1]}]"
        elif isinstance(it, dict):
            line = str(it.get("prefLabel") or it.get("_about"))
        else:
            line = it
        if line not in lines:
            lines.append(line)
    labelled = [ln for ln in lines if "[" in ln]
    bare = [ln.rstrip("/").rsplit("/", 1)[-1] for ln in lines if "[" not in ln]
    print(f"temas={len(labelled)} etiquetados | {len(bare)} URIs sin etiqueta")
    for line in labelled[: args.limit]:
        print(f"  {line}")
    if bare:
        print("  sin etiqueta (vocabularios DCAT/INSPIRE): " + ", ".join(bare[:12]))


# --------------------------------------------------------------------------- portales

def cmd_portales(args) -> None:
    rows = []
    for name, api in CKAN.items():
        status = ""
        if args.check:
            try:
                r = ckan_call(name, "package_search", {"q": "*:*", "rows": 0}) if api else {}
                status = f"ok {r.get('count', 0)} datasets"
            except ApiError as exc:
                status = f"ERROR {str(exc)[:50]}"
        rows.append(["ckan", name, api, status])
    for name, dom in SOCRATA.items():
        status = ""
        if args.check:
            try:
                d = get_json(f"{dom}/api/catalog/v1", {"limit": 1})
                status = f"ok ({d.get('results', [{}])[0].get('resource', {}).get('id', '')[:8]}…)"
            except ApiError as exc:
                status = f"ERROR {str(exc)[:50]}"
        rows.append(["socrata", name, dom, status])
    for name, ep in SPARQL.items():
        status = ""
        if args.check:
            try:
                _request(ep, data=urllib.parse.urlencode({"query": "SELECT * WHERE {?s ?p ?o} LIMIT 1"}).encode(),
                         accept="application/sparql-results+json")
                status = "ok"
            except ApiError as exc:
                status = f"ERROR {str(exc)[:50]}"
        rows.append(["sparql", name, ep, status])
    if args.check:
        try:
            d = get_json(f"{GOB}/catalog/theme.json")
            status = f"ok {len(d.get('result', {}).get('items') or [])} temas"
        except ApiError as exc:
            status = f"ERROR {str(exc)[:50]}"
        rows.append(["estatal", "datos.gob.es", GOB, status])
    out_table(rows, ["tipo", "clave", "endpoint", "estado"] if args.check
              else ["tipo", "clave", "endpoint"], max_col=64)
    print(f"\nsin API abierta confirmada (usar datos.gob.es): {', '.join(SIN_API)}")


# --------------------------------------------------------------------------- main

def main() -> None:
    p = argparse.ArgumentParser(
        prog="opendata.py", description="Datos abiertos de España (CKAN · Socrata · SPARQL · datos.gob.es)")
    p.add_argument("--timeout", type=int, default=TIMEOUT, help="timeout por petición (s)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("portales", help="lista portales y su endpoint")
    sp.add_argument("--check", action="store_true", help="comprueba cada portal en vivo")
    sp.set_defaults(func=cmd_portales)

    ck = sub.add_parser("ckan", help="portales CKAN (6 CCAA): ckan <portal> <search|orgs|dataset>")
    ck.add_argument("portal", help="madrid, aragon, navarra, valencia, murcia, andalucia, clm o una URL")
    ck.add_argument("rest", nargs=argparse.REMAINDER, help="acción y sus opciones")
    ck.set_defaults(func=cmd_ckan_dispatch)

    so = sub.add_parser("socrata", help="Socrata (Cataluña)")
    sos = so.add_subparsers(dest="sub", required=True)
    s = sos.add_parser("search", help="busca datasets en el catálogo")
    s.add_argument("query")
    s.add_argument("--domain", default="cataluna")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_socrata_search)
    s = sos.add_parser("rows", help="filas de un dataset")
    s.add_argument("dataset")
    s.add_argument("--domain", default="cataluna")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--where")
    s.add_argument("--select")
    s.add_argument("--order")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_socrata_rows)

    spq = sub.add_parser("sparql", help="consulta SPARQL (Euskadi)")
    spq.add_argument("query")
    spq.add_argument("--endpoint", default="euskadi")
    spq.add_argument("--timeout", type=int, default=60)
    spq.add_argument("--json", action="store_true")
    spq.set_defaults(func=cmd_sparql, timeout=60)

    gb = sub.add_parser("gob", help="catálogo estatal datos.gob.es")
    gbs = gb.add_subparsers(dest="sub", required=True)
    s = gbs.add_parser("datasets", help="pagina el catálogo y filtra en local")
    s.add_argument("--grep", help="filtra en local por título/descripción/keyword/publicador")
    s.add_argument("--publisher", help="URI de publicador (filtro del servidor)")
    s.add_argument("--format", help="formato del recurso, p. ej. text/csv")
    s.add_argument("--modified-begin", help="AAAA-MM-DD")
    s.add_argument("--pages", type=int, default=3, help="máx. páginas de 50 (def. 3)")
    s.add_argument("--page-size", type=int, default=50)
    s.add_argument("--delay", type=float, default=0.3)
    s.add_argument("--limit", type=int, default=15, help="filas a mostrar")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_gob_datasets)
    s = gbs.add_parser("dataset", help="detalle por slug o URL de _about")
    s.add_argument("identifier")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_gob_dataset)
    s = gbs.add_parser("publishers", help="publicadores del catálogo")
    s.add_argument("--pages", type=int, default=2)
    s.add_argument("--limit", type=int, default=20)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_gob_publishers)
    s = gbs.add_parser("themes", help="temas/taxonomías")
    s.add_argument("--limit", type=int, default=30)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_gob_themes)

    args = p.parse_args()
    try:
        args.func(args)
    except ApiError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
