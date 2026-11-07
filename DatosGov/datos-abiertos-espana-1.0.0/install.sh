#!/usr/bin/env bash
# install.sh — instala la skill "datos-abiertos-espana" en una instalación de Hermes.
#
# Uso:
#   ./install.sh                      # en el perfil activo (HERMES_HOME o ~/.hermes)
#   ./install.sh --profile trabajo     # en $HERMES_HOME/profiles/trabajo/skills
#   ./install.sh --dest /ruta/skills   # destino explícito (el que contiene SKILL.md de las skills)
#   ./install.sh --category opendata   # subcarpeta de categoría (por defecto: research)
#   ./install.sh --force               # sobrescribe si ya existe
#   ./install.sh --no-check            # no comprueba los portales por red
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/datos-abiertos-espana"
NAME="datos-abiertos-espana"
CATEGORY="research"
DEST=""
PROFILE=""
FORCE=false
CHECK=true

info() { printf '\033[0;32m✓\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m⚠\033[0m %s\n' "$*"; }
err()  { printf '\033[0;31m✗\033[0m %s\n' "$*" >&2; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest)      DEST="${2:?falta la ruta}"; shift 2 ;;
    --profile)   PROFILE="${2:?falta el nombre del perfil}"; shift 2 ;;
    --category)  CATEGORY="${2:?falta la categoría}"; shift 2 ;;
    --force)     FORCE=true; shift ;;
    --no-check)  CHECK=false; shift ;;
    -h|--help)   sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)           err "opción desconocida: $1"; exit 2 ;;
  esac
done

[[ -f "$SRC/SKILL.md" ]] || { err "no encuentro $SRC/SKILL.md (¿descomprimiste el tar.gz entero?)"; exit 1; }

python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' \
  || { err "hace falta python3 >= 3.8"; exit 1; }

HH="${HERMES_HOME:-$HOME/.hermes}"
if [[ -z "$DEST" ]]; then
  if [[ -n "$PROFILE" ]]; then
    DEST="$HH/profiles/$PROFILE/skills"
    [[ -d "$HH/profiles/$PROFILE" ]] || warn "el perfil '$PROFILE' aún no existe en $HH/profiles — se creará la carpeta"
  else
    DEST="$HH/skills"
  fi
fi

TARGET="$DEST/$CATEGORY/$NAME"

echo "origen:  $SRC"
echo "destino: $TARGET"
echo

if [[ -e "$TARGET" && "$FORCE" != true ]]; then
  warn "ya existe $TARGET — no se toca nada."
  warn "vuelve a ejecutar con --force para sobrescribir."
  exit 0
fi

mkdir -p "$DEST/$CATEGORY"
rm -rf "$TARGET"
cp -R "$SRC" "$TARGET"
chmod +x "$TARGET/scripts/opendata.py" 2>/dev/null || true
info "instalada en $TARGET"

echo
echo "── comprobación local ──"
python3 "$TARGET/scripts/opendata.py" portales >/dev/null \
  && info "el script responde (subcomando portales)" \
  || { err "el script no arranca; revisa python3"; exit 1; }

if [[ "$CHECK" == true ]]; then
  echo
  echo "── comprobación en vivo (red) ──"
  python3 "$TARGET/scripts/opendata.py" portales --check || warn "alguna comprobación falló (normal si hay WAF o sin red)"
fi

cat <<EOF

── siguiente paso ──
Hermes indexa las skills al construir el prompt de sesión. Para verla y usarla:
  1. si tienes una sesión abierta, ejecuta /new (o reinicia el CLI/gateway)
  2. comprueba que aparece:  skills_list  →  "$NAME"
  3. cárgala a mano la primera vez:  skill_view(name="$NAME")

Prueba rápida:
  python3 "$TARGET/scripts/opendata.py" portales --check
  python3 "$TARGET/scripts/opendata.py" ckan madrid search "calidad del aire" --rows 5
EOF
