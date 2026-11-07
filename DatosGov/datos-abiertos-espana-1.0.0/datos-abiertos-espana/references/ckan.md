# CKAN v3 (6 portales autonómicos)

Vale para Madrid, Aragón, Navarra, Valencia, Murcia y Andalucía. API pública, sin API key,
respuestas JSON con `success` + `result`. No requiere el script: cualquier `curl` sirve.

## Endpoints

| Acción | Endpoint | Notas |
|---|---|---|
| buscar datasets | `GET /package_search?q=&rows=&start=&fq=` | `q=*:*` para todo el catálogo |
| detalle dataset | `GET /package_show?id=<name-o-id>` | el `name` del listado es el id |
| organizaciones | `GET /organization_list?all_fields=true` | incluye `package_count` |
| grupos/temas | `GET /group_list`, `/group_show?id=` | |
| lista de ids | `GET /package_list` | solo slugs |

Base de cada portal en `references/portales.md` (Aragón: `/aod/api/3/action`; el resto
`/api/3/action`).

## Recetas

```bash
API=https://datos.comunidad.madrid/api/3/action

# 1. Buscar (q=*:* = todo). rows máximo razonable 50-100.
curl -sG "$API/package_search" --data-urlencode "q=calidad del aire" -d rows=10 \
  | python3 -c 'import json,sys; d=json.load(sys.stdin)["result"]; print(d["count"]); [print("-",x["title"]) for x in d["results"]]'

# 2. Detalle
curl -sG "$API/package_show" -d id=calidad_aire_estaciones | python3 -m json.tool | head -40

# 3. Filtrar por organización (fq)
curl -sG "$API/package_search" --data-urlencode "q=*:*" --data-urlencode "fq=organization:comunidad-de-madrid" -d rows=5

# 4. Descargar un recurso
curl -sL -o datos.csv "<resources[0].url>"
```

Con el script (salida compacta):

```bash
python3 scripts/opendata.py ckan madrid search "calidad del aire" --rows 10
python3 scripts/opendata.py ckan aragon orgs --limit 15
python3 scripts/opendata.py ckan navarra dataset <id> --json
```

## Estructura de la respuesta

```json
{"success": true,
 "result": {"count": 49,
   "results": [{"name": "calidad_aire_estaciones", "title": "…",
     "organization": {"title": "Comunidad de Madrid"},
     "tags": [{"display_name": "Aire"}],
     "resources": [{"url": "https://…", "format": "CSV", "name": "…"}]}]}}
```

`top-level` de un dataset: `name` (slug/id), `title`, `notes` (descripción),
`metadata_modified`, `organization.title`, `groups[].display_name`, `tags[].display_name`,
`resources[]` con `url`/`format`/`name`.

## Pitfalls

- **`q=*` devuelve 0**. Usa `q=*:*`. Es el error que traían los 7 skills originales.
- `rows` > 100 lo ignoran algunos portales; pagina con `start`.
- El `id` de `package_show` es el `name` del listado (slug), no un UUID.
- `fq` usa slugs: `organization:<name>`, `groups:<name>` o `tags:<tag>`.
- Respeta 0,2 s entre peticiones; hay portales con rate limit agresivo.
- Los recursos pueden apuntar a otro dominio (Aragón sirve CSV desde `servicios3.aragon.es`);
  comprueba que la descarga es lo que esperas antes de parsearla.
