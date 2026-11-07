# SPARQL — Euskadi (Open Data Euskadi, RDF/DCAT-AP)

Endpoint: `https://api.euskadi.eus/sparql` (SPARQL 1.1, público, sin clave).
El grafo es DCAT-AP: ~127 000 distribuciones, 20 000 formatos, más vocabularios
propios (`id.euskadi.eus`), schema.org y geonames.

## Recetas

```bash
# 1. Explorar clases (verificado: devuelve dcat#Distribution, dc/terms#IMT, …)
curl -sG "https://api.euskadi.eus/sparql" \
  -H "Accept: application/sparql-results+json" \
  --data-urlencode 'query=SELECT ?type (COUNT(?s) AS ?n) WHERE { ?s a ?type } GROUP BY ?type ORDER BY DESC(?n) LIMIT 10'

# 2. Buscar datasets por título (dcat:Dataset)
curl -sG "https://api.euskadi.eus/sparql" \
  -H "Accept: application/sparql-results+json" \
  --data-urlencode 'query=
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX dct:  <http://purl.org/dc/terms/>
SELECT ?ds ?title WHERE {
  ?ds a dcat:Dataset ; dct:title ?title .
  FILTER(CONTAINS(LCASE(STR(?title)), "poblacion"))
} LIMIT 20'
```

Con el script:

```bash
python3 scripts/opendata.py sparql "SELECT ?s WHERE { ?s a ?o } LIMIT 5"
python3 scripts/opendata.py sparql "PREFIX dcat: <http://www.w3.org/ns/dcat#> SELECT (COUNT(?d) AS ?n) WHERE { ?d a dcat:Dataset }"
```

## Pitfalls

- **Siempre `Accept: application/sparql-results+json`**, si no devuelve XML/JSON-LD y el
  parseo se complica. El script ya lo pone.
- Usa `POST` con `query` en el cuerpo (form-encoded): las queries largas no caben en URL.
- Declara los prefijos en la query (`dcat:`, `dct:`, `foaf:`, `vcard:`); el endpoint **no**
  trae prefijos por defecto.
- Sin `LIMIT` una query sobre 127 k distribuciones puede tardar minutos o cortar por
  timeout: empieza siempre con `LIMIT` y cuenta antes de volcar.
- Los títulos suelen estar en euskera y castellano como literales con `@eu`/`@es`; filtra
  con `FILTER(LANG(?title)="es")` si necesitas uno solo.
