---
name: datos-abiertos-espana
description: "Datos abiertos de España: CCAA y catálogo estatal."
version: 1.0.0
author: ivanpl82, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [opendata, espana, ckan, socrata, sparql, dcat-ap, datos-gob-es]
    related_skills: []
---

# Datos abiertos de España

Localiza, consulta y descarga datasets de los portales de datos abiertos españoles: los
8 autonómicos con API viva (6 CKAN + Socrata Cataluña + SPARQL Euskadi) y el catálogo
estatal agregado `datos.gob.es`. Todo HTTP público, sin API keys. Las recetas están
probadas contra las APIs reales y el script `scripts/opendata.py` (solo stdlib, sin
dependencias) envuelve las cuatro familias de API.

## When to Use

- "datos abiertos de <comunidad>", "datasets sobre <tema> en España", "descarga el CSV de…"
- Menciones de `datos.gob.es`, CKAN, Socrata, SPARQL, DCAT-AP, NTI, distribuciones
- Necesitas localizar un conjunto de datos público, sus recursos o su publicador

**No usar para**: series estadísticas del INE/ISTAC/Eustat (usar sus propias APIs), datos
que no sean públicos, ni portales fuera de `references/portales.md`.

## Decisión: qué API usar

| Situación | Vía | Referencia |
|---|---|---|
| Comunidad con API viva (Madrid, Aragón, Navarra, Valencia, Murcia, Andalucía) | CKAN `package_search` | `references/ckan.md` |
| Cataluña | Socrata SODA | `references/socrata.md` |
| Euskadi / datos enlazados RDF | SPARQL | `references/sparql.md` |
| Portal caído, comunidad sin API, o tema transversal / no sabes la comunidad | catálogo estatal | `references/datosgob.md` |
| Dudas sobre qué host y qué ruta usa cada comunidad | tabla verificada | `references/portales.md` |

Regla: **primero el portal autonómico** (metadatos más ricos y búsqueda que funciona);
**`datos.gob.es` como red de seguridad** para Asturias, Cantabria, Extremadura, Galicia,
La Rioja, Baleares, Canarias, Castilla y León, Ceuta y Melilla (sin API abierta
confirmada) y para temas transversales.

## Prerequisites

- `python3` ≥ 3.8. Nada más: el script usa solo stdlib.
- El script vive en `scripts/opendata.py` de esta skill:

```bash
SKILL_DIR="${HERMES_HOME:-$HOME/.hermes}/skills/research/datos-abiertos-espana"
python3 "$SKILL_DIR/scripts/opendata.py" portales --check
```

Si no está ahí (otra categoría u otro perfil):
`find "$HOME/.hermes" /opt/data -name opendata.py -path '*datos-abiertos*' 2>/dev/null | head -1`

## Quick Reference

```bash
python3 "$SKILL_DIR/scripts/opendata.py" portales [--check]           # portales y estado en vivo
python3 "$SKILL_DIR/scripts/opendata.py" ckan madrid search "calidad del aire" --rows 10
python3 "$SKILL_DIR/scripts/opendata.py" ckan aragon orgs --limit 15
python3 "$SKILL_DIR/scripts/opendata.py" ckan navarra dataset <id> [--json]
python3 "$SKILL_DIR/scripts/opendata.py" socrata search "covid" --limit 10
python3 "$SKILL_DIR/scripts/opendata.py" socrata rows <dataset-id> --limit 20 [--where] [--select]
python3 "$SKILL_DIR/scripts/opendata.py" sparql "SELECT ?s WHERE { ?s ?p ?o } LIMIT 5"
python3 "$SKILL_DIR/scripts/opendata.py" gob datasets --grep "ruido" --pages 3
python3 "$SKILL_DIR/scripts/opendata.py" gob dataset <slug-o-URL-_about>
python3 "$SKILL_DIR/scripts/opendata.py" gob publishers --pages 1
python3 "$SKILL_DIR/scripts/opendata.py" gob themes
```

Todos los subcomandos aceptan `--json` para la respuesta cruda. Salida por defecto:
tabla compacta (pensada para no inundar el contexto).

## Procedure

1. **Identifica el portal** en `references/portales.md` (o pregunta al usuario la
   comunidad). Si no hay portal vivo, ve al catálogo estatal.
2. **Comprueba que responde**: `portales --check`. Criterio: la fila del portal dice
   `ok <n> datasets`. Si falla, cae al catálogo estatal y dilo.
3. **Busca** con `ckan <portal> search "<texto>"`. Criterio: `total>0`; si `total=0`,
   prueba sinónimos antes de concluir que no hay datos.
4. **Abre el dataset** (`ckan <portal> dataset <id>`) y elige el recurso por `format`.
5. **Descarga** el recurso con `terminal(command="curl -sL -o datos.csv '<url>'")` —
   las URLs de `resources[].url` / `accessURL` son descargas directas.
6. **Verifica la descarga**: tamaño > 0 y primeras líneas con cabecera
   (`read_file` o `head` equivalentes). No anuncies un dataset sin haberlo abierto.
7. **Cita**: título, portal, URL del dataset y fecha de consulta.

## Pitfalls (verificados, no teóricos)

- **CKAN `q=*` devuelve 0 resultados.** Usa `q=*:*` para "todo el catálogo". El script ya
  lo hace por defecto.
- **Aragón no usa `/api/3/action`**: es `https://opendata.aragon.es/aod/api/3/action`
  (la ruta antigua redirige con 301 y rompe los POST).
- **Navarra es `datosabiertos.navarra.es`**, no `datos.navarra.es` (ese host no existe).
- **Castilla-La Mancha** resuelve por DNS pero corta la conexión desde muchas redes
  (TLS/WAF): trátalo como no disponible y usa el catálogo estatal.
- **No hay API abierta confirmada** para Asturias, Cantabria, Extremadura, Galicia, La
  Rioja, Baleares, Canarias, Castilla y León, Ceuta ni Melilla. Sus datasets aparecen en
  `datos.gob.es` (cosecha de portales autonómicos y locales).
- **`datos.gob.es` no tiene búsqueda por texto libre**: `q`, `_search`, `keyword` y
  `theme` devuelven 0 resultados. Pagina con `_page`/`_pageSize` (máx 50, empieza en 0,
  sin `totalCount`) y **filtra en local** (`gob datasets --grep`).
- **`datos.gob.es` no tiene lookup por UUID**: `catalog/dataset/{uuid}.json` devuelve
  `items: []`. El detalle se pide con el **slug** de `_about`
  (`catalog/dataset/{slug}.json`).
- **Modelo de datos inconsistente** en `datos.gob.es`: `title`/`description`/`keyword`
  son listas de `{_value,_lang}`, pero `identifier`, `publisher` y `spatial` son strings
  (o `None`), y `distribution` a veces es objeto y a veces lista. Normaliza siempre.
- **Socrata: usa `/api/catalog/v1`** (0,3 s), no `/api/views.json` (12 s).
- **Respeta el rate limit**: 0,2–0,5 s entre páginas. `datos.gob.es` completo son ~2500
  datasets / 50 páginas: usa `--pages` y no lo recorras entero sin motivo.
- El endpoint `spatial` de `datos.gob.es` y `catalog/nti` no existen (500 y 404).

## Verification

```bash
python3 "$SKILL_DIR/scripts/opendata.py" portales --check    # 8 portales "ok" (CLM puede fallar)
python3 "$SKILL_DIR/scripts/opendata.py" ckan madrid search "calidad del aire" --rows 3
python3 "$SKILL_DIR/scripts/opendata.py" gob dataset e05068001-mapas-estrategicos-de-ruido
```

Éxito: `total>0` con títulos reales, y el detalle del dataset muestra distribuciones con
`accessURL`. Si `portales --check` falla en todos, el problema es de red/DNS del entorno,
no de la skill.

## Procedencia

Consolida y corrige dos repos de skills para OpenCode: `ivanpl82/api_comunicades_ia`
(19 skills autonómicas, 7 de ellas stubs) y `ivanpl82/datos_gob_es_ia` (CLI `datosgob`).
Los 21 ficheros originales se han reducido a 1 skill + 5 referencias, y todas las rutas,
filtros y modelos de datos se han vuelto a verificar contra las APIs reales (noviembre
2026). Los fallos corregidos están en `references/portales.md`.
