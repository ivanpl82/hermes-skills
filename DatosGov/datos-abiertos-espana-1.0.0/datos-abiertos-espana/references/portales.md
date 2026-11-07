# Portales de datos abiertos de España — tabla verificada

Estado comprobado el **2026-11-07** contra las APIs reales desde una red europea
(HTTP status + recuento de datasets). Vuelve a comprobarlo con
`python3 scripts/opendata.py portales --check` antes de fiarte de un informe.

## Con API viva

| Comunidad | Host | Tipo | Ruta base | Datasets |
|---|---|---|---|---|
| Comunidad de Madrid | `datos.comunidad.madrid` | CKAN v3 | `/api/3/action` | 2275 |
| Aragón | `opendata.aragon.es` | CKAN v3 | **`/aod/api/3/action`** | 2428 |
| Navarra | **`datosabiertos.navarra.es`** | CKAN v3 | `/api/3/action` | 2098 |
| Comunidad Valenciana | `dadesobertes.gva.es` | CKAN v3 | `/api/3/action` | 1318 |
| Región de Murcia | `datosabiertos.regiondemurcia.es` | CKAN v3 | `/api/3/action` | 980 |
| Andalucía | `www.juntadeandalucia.es/datosabiertos/portal` | CKAN v3 | `/api/3/action` | 848 |
| Cataluña | `analisi.transparenciacatalunya.cat` | Socrata SODA | `/api/catalog/v1`, `/resource/{id}.json` | ~10⁴ |
| Euskadi | `api.euskadi.eus` | SPARQL 1.1 | `/sparql` | (grafo RDF) |
| **Estado (agregado)** | `datos.gob.es` | linked-data-api v0.2 (DCAT-AP) | `/apidata/catalog/...json` | ~2500 |

Nota: los recuentos son los que devuelve `package_search?q=*:*` en esa fecha; sirven de
orden de magnitud, no como censo.

## Sin API abierta confirmada

Usa el catálogo estatal (`references/datosgob.md`): cosecha estos portales, así que sus
datasets suelen estar ahí aunque el host local no exponga API.

| Comunidad | Host probado | Resultado |
|---|---|---|
| Castilla-La Mancha | `datosabiertos.castillalamancha.es` | DNS ok, TLS ok, **corte al recibir datos** (WAF) |
| Galicia | `datos.xunta.gal` → NXDOMAIN; `abertos.xunta.gal` → portal web sin API en rutas estándar | sin API |
| Castilla y León | `datosabiertos.jcyl.es` | 301 al catálogo HTML; `/api/3/action` → 404 |
| Illes Balears | `catalegdades.caib.cat` | 404 en `/api/views`, `/api/catalog/v1`, `/api/3/action` |
| Canarias | `datos.canarias.es` | 302; `/api/3/action` y `/reutilizacion/api/` → 404 |
| Asturias | `datos.asturias.es` | **NXDOMAIN** (confirmado por DoH) |
| Cantabria | `datos.cantabria.es` | **NXDOMAIN** (confirmado por DoH) |
| Extremadura | `datosabiertos.juntaex.es` | **NXDOMAIN** (confirmado por DoH) |
| La Rioja | `www.larioja.org/datos-abiertos` | 403 (WAF), sin API conocida |
| Ceuta | — | sin portal de datos abiertos |
| Melilla | — | sin portal de datos abiertos |

`NXDOMAIN` significa que el dominio **no existe**, no que esté caído: no insistas ni
pruebes variantes de ruta.

## Correcciones respecto a los repos originales

| Dato del repo original | Realidad verificada |
|---|---|
| Aragón `api_path = /ckan/api/3/action` | `/aod/api/3/action` (el viejo da 301 y rompe los POST) |
| Navarra `datos.navarra.es` | `datosabiertos.navarra.es` |
| Galicia "error de transporte" | el host del repo no existe; el portal es `abertos.xunta.gal` (sin API REST) |
| CKAN `q='*'` en todos los ejemplos | devuelve 0; hay que usar `q=*:*` |
| "`api_status: transport_error`" en 5 CCAA | son nombres de host equivocados (NXDOMAIN), no caídas |
| Asturias/Cantabria/Extremadura/La Rioja "stub" | confirmado sin API; se cubren vía `datos.gob.es` |
| `spatial` "la mayoría usa idee.es" | en una muestra de 150: 59 `idee.es`, 35 `datos.gob.es`, 15 `geonames`, 41 nulo |
