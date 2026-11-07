Hecho y verificado contra las APIs reales.

## Qué hay ahora

Instalada y activa en este Hermes (`hermes skills list` → `datos-abiertos-espana | research | local | enabled`, y `skill_view` la carga con sus 5 referencias y el script):

```
/opt/data/skills/research/datos-abiertos-espana/
├── SKILL.md                 137 líneas · router + recetas + 12 pitfalls verificados
├── references/
│   ├── portales.md          tabla de los 19 portales, con estado medido hoy
│   ├── ckan.md              CKAN v3 (6 CCAA)
│   ├── socrata.md           Cataluña
│   ├── sparql.md            Euskadi
│   └── datosgob.md          catálogo estatal (linked-data-api)
└── scripts/opendata.py      522 líneas, solo stdlib (sin click, sin pandas, sin pip)
```

Los 21 ficheros originales quedan en 1 skill + 5 referencias (68 KB). Y todo lo que estaba roto está corregido: `q=*:*` en CKAN, Aragón `/aod/`, Navarra `datosabiertos.`, Socrata `/api/catalog/v1` (0,3 s en vez de 12 s), modelo de datos real de datos.gob.es, y **el detalle por slug** que en el repo era imposible (`dataset/{uuid}.json` devuelve vacío; funciona `dataset/{slug}.json`).

## Comprobación real

```
portales --check  → 9 ok (madrid 2275 · aragon 2428 · navarra 2098 · valencia 1318
                          murcia 980 · andalucia 848 · cataluña · euskadi · estatal)
                          CLM falla por WAF, como documenta la skill
ckan madrid search "calidad del aire"  → total=49, títulos reales
ckan aragon orgs                       → 47 orgs (IAEST 1575 datasets)
socrata search covid / rows            → 250 datasets, filas reales
sparql (Euskadi)                       → 127k distribuciones DCAT
gob datasets --grep ruido              → 100 examinados, 2 coincidencias
gob dataset e05068001-mapas-…          → título, publisher, licenses, accessURL
```

Rutas de error probadas también: portal inexistente, dataset que no existe y UUID en lugar de slug devuelven un mensaje accionable (exit 2), no un traceback.

## El paquete

**`/opt/data/datos-abiertos-espana-1.0.0.tar.gz`** · 18 KB · `sha256 33592ce5d89102c6106327842e454d072006f84823941a75752b4042da49fa03`

Contiene `datos-abiertos-espana-1.0.0/` con `INSTALL.md`, `install.sh` y la carpeta `datos-abiertos-espana/` (esta última es la que se copia a `skills/`). Recién probado: descomprimido en limpio y ejecutado el script desde dentro del tar, funciona.

## Instalarlo en otra instalación de Hermes

**1. Script (recomendado):**

```bash
tar xzf datos-abiertos-espana-1.0.0.tar.gz
cd datos-abiertos-espana-1.0.0
./install.sh
```

Detecta `HERMES_HOME` (o `~/.hermes`) y copia a `<skills>/research/datos-abiertos-espana/`. Flags: `--profile trabajo`, `--dest /ruta/skills`, `--category opendata`, `--force`, `--no-check`. Si ya existe no toca nada (probado).

**2. Manual:** `cp -R datos-abiertos-espana-1.0.0/datos-abiertos-espana "$HERMES_HOME/skills/research/"`. La estructura `<skills>/<categoría>/<nombre>/SKILL.md` es obligatoria: Hermes solo indexa ficheros llamados `SKILL.md`.

**3. Compartida con `external_dirs`** (sin copiar, solo lectura): poner la carpeta donde quieras y en `config.yaml`:

```yaml
skills:
  external_dirs:
    - ~/skills-compartidas
```

Dónde cae en cada tipo de instalación: CLI normal → `~/.hermes/skills/...`; Docker → `/opt/data/skills/...` (este caso); perfil concreto → `$HERMES_HOME/profiles/<perfil>/skills/...`. Se comprueba con `echo "$HERMES_HOME"` (vacío = `~/.hermes`).

**No la instales con `hermes skills install <url>`**: ese modo solo baja el `SKILL.md` y se perdería el script y las referencias.

## Cómo invocarla allí

- **Natural** (se autocarga por descripción): *"busca datasets de calidad del aire en Madrid"*, *"¿qué datos abiertos hay de empleo en Navarra?"*, *"descarga el CSV de ruido del catálogo estatal"*.
- **Explícita**: *"usa la skill datos-abiertos-espana para…"*.
- **Forzada**: `skill_view(name="datos-abiertos-espana")`, o el comando `/datos-abiertos-espana` en el CLI.
- **Directa, sin modelo** (cron, scripts):

```bash
SK="${HERMES_HOME:-$HOME/.hermes}/skills/research/datos-abiertos-espana/scripts/opendata.py"
python3 "$SK" portales --check
python3 "$SK" ckan madrid search "calidad del aire" --rows 10
python3 "$SK" socrata rows <id> --limit 20 --where "sexe='Dona'"
python3 "$SK" gob datasets --grep "ruido" --pages 3
```

Todos aceptan `--json`. Tras instalar en una máquina con sesión abierta, hace falta `/new` (o reiniciar el gateway) para que aparezca en el índice del prompt.

**Mantenimiento:** si un portal cambia de host, `portales --check` lo delata y solo hay que tocar `references/portales.md` y el diccionario `CKAN`/`SOCRATA` de `scripts/opendata.py` (arriba del fichero).