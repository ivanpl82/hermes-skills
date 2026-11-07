# Catálogo estatal — datos.gob.es (linked-data-api v0.2, DCAT-AP)

Base: `https://datos.gob.es/apidata` · público, sin clave · JSON.
Agrega el catálogo de la Administración General del Estado **y cosecha portales
autonómicos y locales** (~2500 datasets). Es la red de seguridad para las comunidades sin
API propia.

## Endpoints que funcionan

| Recurso | URL | Formato |
|---|---|---|
| datasets | `/catalog/dataset.json` | `result.items[]` + `next` |
| un dataset | `/catalog/dataset/{slug}.json` | `result.items[0]` |
| distribuciones | `/catalog/distribution.json` | `result.items[]` |
| publicadores | `/catalog/publisher.json` | `result.items[]` (URIs) |
| temas | `/catalog/theme.json` | `result.items[]` (URIs + `{prefLabel}`) |

## Endpoints que NO funcionan

| Recurso | Resultado |
|---|---|
| `/catalog/nti` o `nti.json` | **404** |
| `/catalog/spatial` | **500** |
| `catalog/dataset/{uuid}.json` | 200 pero `items: []` (no hay lookup por UUID) |
| filtros `q`, `_search`, `keyword`, `theme` | **0 resultados** (no hay búsqueda libre) |

## Recetas

```bash
# 1. Paginar el catálogo (page 0, tamaño máx 50)
curl -s "https://datos.gob.es/apidata/catalog/dataset.json?_pageSize=50&_page=0" \
  | python3 -c 'import json,sys; r=json.load(sys.stdin)["result"]; print(len(r["items"]), "hay más:", "next" in r)'

# 2. Recorrer todo (para y avanza mientras exista "next")
python3 - <<'EOF'
import json, urllib.request, time
page = 0
while True:
    u = f"https://datos.gob.es/apidata/catalog/dataset.json?_pageSize=50&_page={page}"
    r = json.load(urllib.request.urlopen(u, timeout=30))["result"]
    for it in r["items"]:
        print(it.get("_about"))
    if "next" not in r: break
    page += 1; time.sleep(0.3)
EOF

# 3. Detalle por slug (desde el final de _about)
curl -s "https://datos.gob.es/apidata/catalog/dataset/e05068001-mapas-estrategicos-de-ruido.json"
```

Con el script (recomendado: trae paginación con tope, filtro local y campos normalizados):

```bash
python3 scripts/opendata.py gob datasets --grep "ruido" --pages 3
python3 scripts/opendata.py gob datasets --format text/csv --pages 2
python3 scripts/opendata.py gob dataset e05068001-mapas-estrategicos-de-ruido
python3 scripts/opendata.py gob publishers --pages 1
python3 scripts/opendata.py gob themes
```

## Modelo de datos (tal como llega, no como lo documentan los repos originales)

```json
{"result": {
  "items": [{
    "_about": "https://datos.gob.es/catalogo/e05068001-mapas-estrategicos-de-ruido",
    "title":       [{"_value": "Mapas estratégicos de Ruido", "_lang": "es"}],
    "description": [{"_value": "…", "_lang": "es"}],
    "keyword":     [{"_value": "environment", "_lang": "es"}],
    "identifier":  "b0da07b8-6856-4af2-91f7-20a7531d6b6f",
    "publisher":   "http://datos.gob.es/recurso/sector-publico/org/Organismo/E05068001",
    "spatial":     "http://datos.gob.es/recurso/sector-publico/territorio/Pais/España",
    "theme":       ["http://datos.gob.es/kos/sector-publico/sector/medio-ambiente"],
    "distribution": {"format": "http://publications.europa.eu/…/file-type/HTML",
                     "accessURL": "https://catalogo.datosabiertos.miteco.gob.es/…"}
  }],
  "itemsPerPage": 50, "page": 0, "startIndex": 1, "next": "…"}}
```

Reglas de normalización obligatorias:

- `title` / `description` / `keyword` → **lista** de `{_value,_lang}` (coge `[0]["_value"]`).
- `identifier` / `publisher` / `spatial` → **string** o `null` (no listas).
- `distribution` → **objeto o lista** (comprueba el tipo antes de iterar).
- `format` es una URI de vocabulario: el formato real es el último segmento (`…/CSV`).
- No hay `totalCount`: itera mientras exista `result.next`.

## Paginación

| Propiedad | Valor |
|---|---|
| `_page` | empieza en **0** |
| `_pageSize` | máx **50** |
| fin | cuando falta `result.next` |
| coste | ~2500 datasets ≈ 50 páginas ≈ 60-90 s con 0,3 s de espera |

## Pitfalls

- **Sin búsqueda libre.** Cualquier "búscame datos de X" exige paginar y filtrar en local
  (`--grep`). No inventes parámetros: `q`, `_search`, `keyword` y `theme` devuelven 0.
- **`dataset/{uuid}.json` devuelve vacío.** El detalle se pide con el **slug** del final de
  `_about` (`e05068001-mapas-estrategicos-de-ruido`).
- La extensión `.json` es obligatoria en los endpoints de catálogo.
- Respuestas de varias MB: si parseas a mano con `requests`, un corte de red produce
  `JSONDecodeError: Unterminated string`. Usa timeout amplio y reintentos.
- `spatial` no es fiable para filtrar por comunidad: mezcla `idee.es`, `datos.gob.es`,
  `geonames` y nulos.
