# datos-abiertos-espana — skill para Hermes Agent

Skill de datos abiertos de España: 8 portales autonómicos con API viva (6 CKAN +
Socrata Cataluña + SPARQL Euskadi) y el catálogo estatal `datos.gob.es`. Incluye
`scripts/opendata.py`, un cliente de las cuatro familias de API **sin dependencias**
(solo stdlib de Python ≥ 3.8).

```
datos-abiertos-espana/
├── SKILL.md                  # router + recetas + pitfalls
├── references/
│   ├── portales.md           # tabla verificada de los 19 portales
│   ├── ckan.md               # CKAN v3 (Madrid, Aragón, Navarra, Valencia, Murcia, Andalucía)
│   ├── socrata.md            # Socrata / Cataluña
│   ├── sparql.md             # SPARQL / Euskadi
│   └── datosgob.md           # linked-data-api del catálogo estatal
└── scripts/opendata.py       # CLI: portales · ckan · socrata · sparql · gob
```

## Requisitos

- Hermes Agent (cualquier superficie: CLI, TUI, gateway, desktop).
- `python3` ≥ 3.8 en la máquina donde corre Hermes. **Nada más**: no hay pip, ni pandas,
  ni click, ni API keys.

## Instalación

### Opción 1 — script (recomendada)

```bash
tar xzf datos-abiertos-espana-1.0.0.tar.gz
cd datos-abiertos-espana-1.0.0
./install.sh
```

`install.sh` detecta `HERMES_HOME` (o `~/.hermes` si no está definida), copia la skill a
`<skills>/research/datos-abiertos-espana/` y hace una comprobación local + de red.

Opciones:

| Flag | Efecto |
|---|---|
| `--profile NOMBRE` | instala en `$HERMES_HOME/profiles/NOMBRE/skills` |
| `--dest RUTA` | destino explícito (la carpeta que contiene las skills) |
| `--category CAT` | subcarpeta de categoría (`research` por defecto) |
| `--force` | sobrescribe una instalación previa |
| `--no-check` | no hace la comprobación de red |

### Opción 2 — copia manual

```bash
tar xzf datos-abiertos-espana-1.0.0.tar.gz
cp -R datos-abiertos-espana-1.0.0/datos-abiertos-espana \
      "${HERMES_HOME:-$HOME/.hermes}/skills/research/"
```

La estructura importa: Hermes indexa `<skills>/<categoría>/<nombre>/SKILL.md`. Si copias
solo el `SKILL.md` suelto, pierdes `references/` y el script.

### Opción 3 — directorio externo (varias herramientas, sin copiar)

1. Copia la carpeta donde quieras, p. ej. `~/skills-compartidas/datos-abiertos-espana/`.
2. En `config.yaml`:

```yaml
skills:
  external_dirs:
    - ~/skills-compartidas
```

Los `external_dirs` son de **solo lectura** para Hermes (no se pueden editar con
`skill_manage`), pero se listan y se cargan igual.

## Verificación

```bash
hermes skills list | grep datos-abiertos      # aparece en el catálogo
python3 <skills>/research/datos-abiertos-espana/scripts/opendata.py portales --check
```

Salida esperada de `portales --check`: 6 CKAN + Socrata + SPARQL + estatal en `ok`
(Castilla-La Mancha puede fallar por WAF; es normal).

## Cómo invocarla

**1. Lenguaje natural** — Hermes la carga sola cuando detecta el tema:

> "busca datasets de calidad del aire en la Comunidad de Madrid"
> "¿qué datos abiertos hay de empleo en Navarra?"
> "descarga el CSV de paro registrado del catálogo estatal"
> "datos.gob.es, datasets sobre ruido"

**2. Explícita en la conversación**:

> "usa la skill datos-abiertos-espana para buscar…"

**3. Forzando la carga** (si no la detecta o quieres asegurarte):

```
skill_view(name="datos-abiertos-espana")
```

Y desde el CLI de Hermes, la skill también queda como comando con barra: `/datos-abiertos-espana`.

**4. El script directamente** (sin pasar por el modelo, útil en cron o scripts):

```bash
SK="${HERMES_HOME:-$HOME/.hermes}/skills/research/datos-abiertos-espana/scripts/opendata.py"

python3 "$SK" portales --check
python3 "$SK" ckan madrid search "calidad del aire" --rows 10
python3 "$SK" ckan aragon orgs --limit 15
python3 "$SK" ckan navarra dataset <id>
python3 "$SK" socrata search "covid" --limit 10
python3 "$SK" socrata rows <dataset-id> --limit 20 --where "sexe='Dona'"
python3 "$SK" sparql "SELECT ?s WHERE { ?s a ?o } LIMIT 5"
python3 "$SK" gob datasets --grep "ruido" --pages 3
python3 "$SK" gob dataset e05068001-mapas-estrategicos-de-ruido
```

Todos aceptan `--json` para la respuesta cruda. Salida por defecto: tabla compacta.

## Dónde viven las skills en cada instalación

| Instalación | `HERMES_HOME` | Ruta final |
|---|---|---|
| CLI/TUI normal | `~/.hermes` | `~/.hermes/skills/research/datos-abiertos-espana/` |
| Docker (este entorno) | `/opt/data` | `/opt/data/skills/research/datos-abiertos-espana/` |
| Perfil concreto | `$HERMES_HOME/profiles/<perfil>` | `…/profiles/<perfil>/skills/research/…` |

Comprueba el tuyo con `echo "$HERMES_HOME"`; si sale vacío, es `~/.hermes`.

## Desinstalar

```bash
rm -rf "${HERMES_HOME:-$HOME/.hermes}/skills/research/datos-abiertos-espana"
```

## Notas

- **No la instales con `hermes skills install <url-del-SKILL.md>`**: ese modo solo trae el
  `SKILL.md` y perderías `references/` y `scripts/`, que es donde está el valor.
- El índice de skills del prompt se construye al inicio de sesión: si acabas de instalar,
  abre una sesión nueva (`/new`) o reinicia el gateway para verla listada.
- Contenido verificado el 2026-11-07 contra las APIs reales. Si un portal cambia de host,
  `portales --check` lo delata y `references/portales.md` es el único sitio a corregir.
