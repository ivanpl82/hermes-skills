# Socrata SODA — Cataluña

Portal: `https://analisi.transparenciacatalunya.cat` (Generalitat de Catalunya).
API pública, sin token.

## Endpoints

| Acción | Endpoint | Notas |
|---|---|---|
| buscar datasets | `GET /api/catalog/v1?q=<texto>&limit=` | **rápido (~0,3 s)** |
| filas de un dataset | `GET /resource/{id}.json?$limit=&$where=&$select=&$order=` | SoQL |
| metadatos de un dataset | `GET /api/views/{id}.json` | lento, evítalo |
| catálogo completo | `GET /api/views.json` | **12 s**: no lo uses para buscar |

## Recetas

```bash
# 1. Buscar datasets
curl -sG "https://analisi.transparenciacatalunya.cat/api/catalog/v1" \
  --data-urlencode "q=covid" -d limit=5 \
  | python3 -c 'import json,sys; [print(r["resource"]["id"], "-", r["resource"]["name"]) for r in json.load(sys.stdin)["results"]]'

# 2. Filas (SoQL)
curl -sG "https://analisi.transparenciacatalunya.cat/resource/623z-r97q.json" \
  --data-urlencode '$limit=5' --data-urlencode '$where=sexe="Dona"'

# 3. Agregado
curl -sG "https://analisi.transparenciacatalunya.cat/resource/623z-r97q.json" \
  --data-urlencode '$select=count(*)'
```

Con el script:

```bash
python3 scripts/opendata.py socrata search "covid" --limit 5
python3 scripts/opendata.py socrata rows xuwf-dxjd --limit 3
python3 scripts/opendata.py socrata rows <id> --select "col1,col2" --where "col='x'"
```

## Parámetros SoQL

| Parámetro | URL | Ejemplo |
|---|---|---|
| límite | `$limit` | máx 50000 (por defecto 1000) |
| offset | `$offset` | 0-based |
| filtro | `$where` | `any_calendari=2024` |
| columnas | `$select` | `municipi,comarca` |
| orden | `$order` | `data DESC` |
| texto | `$q` | búsqueda full-text dentro del dataset |

## Pitfalls

- **`/api/views.json` tarda ~12 s** y devuelve el catálogo entero: para buscar usa
  `/api/catalog/v1?q=`.
- Los **nombres de columna son en catalán** (`any_calendari`, `descripcio`, `municipi`):
  consúltalos primero con `curl .../resource/{id}.json?$limit=1` en vez de inventarlos.
- Un `$select` con columna inexistente devuelve HTTP 400 `query.soql.no-such-column`.
- Las fechas vienen como `2022-07-25T00:00:00.000` (texto, no ISO con zona).
- `resultSetSize` del catálogo se topa en 10000: no lo uses como censo real.
