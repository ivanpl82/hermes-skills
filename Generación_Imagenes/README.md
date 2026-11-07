Skill creada y **probada contra la API real**, no solo escrita.

## Dónde está

```
/opt/data/skills/creative/nan-image-generation/
├── SKILL.md                 (flujo, ética, modelo por defecto, errores)
├── references/brief.md      (cuestionario de los 17 campos + presets)
├── references/prompt.md     (orden canónico del prompt, notas por modelo, iteración)
├── references/api.md        (contrato del endpoint, límites, curl)
└── scripts/nan_image.py     (21 KB, solo stdlib, sin pip)
```

Paquete listo para copiar: `/opt/data/cache/scratch/nan-image-generation-skill.tar.gz`

## Lo que hace

- **Modelo por defecto `qwen-image-2.1`**, y cambia a `flux-2-klein` solo cuando toca (edición con referencias, `guidance`, fotorrealismo). No es un cambio a ciegas: `qwen-image-2.1` es el único que renderiza texto limpio y el único que no edita, según su propia documentación.
- **Brief en dos rondas como máximo**: primero solo los obligatorios (`Use Case Category`, `Subject`) y espera respuesta; después una única ronda con los 15 restantes, con salida "decide tú" y presets por caso de uso. No pregunta lo que ya está en el mensaje ni bloquea por un campo opcional.
- **Ética**: bloqueo absoluto (menores, contenido sexual no consentido, suplantación de personas reales para engaño, documentos falsificados, facilitación de delitos), zona gris con pregunta previa, y la regla de no disfrazar prompts para esquivar políticas —ni las propias ni las del proveedor.
- **Español neutro de España** en todo el trato; el prompt se escribe en inglés porque los modelos rinden mejor.
- **Mapeo campo → parámetro** documentado, incluidas las trampas del contrato: `background`, `style`, `moderation` y compañía **se aceptan y se ignoran**; no existe `negative_prompt` ni máscara en edición; `guidance` no hace nada en qwen.
- El script calcula el `size` desde aspect ratio y lado largo, lo encaja en los límites del modelo y redondea a múltiplos de 16; descarga la imagen al instante (la URL caduca en ~60 min), valida los bytes y dimensiones reales, y deja un `.json` hermano con prompt, modelo, `size` y `seed` para reproducir.

## Verificación real (gastadas 2 de tus 100 imágenes/mes)

- `models` → lista correcta, `qwen-image-2.1` presente.
- Generación con qwen, 3:2 @1280 → `1280x848`, 1,5 MB, y la escena cumple el brief al mirarla con visión. `/opt/data/nan-ejemplos/20261102-212246_photograph-of-a-small-fruit-stall-in-a-v_1.png`
- Edición con flux y una referencia → preserva sujeto y cambia solo la luz. `/opt/data/nan-ejemplos/20261102-212423_manten-intactos-la-mujer-el-puesto-los-c_1.jpg`
- Validaciones: ratio 5:1 rechazado, `size` no múltiplo de 16 rechazado, edición con qwen rechazada con mensaje útil, `guidance` avisado y omitido.
- Incidencia real encontrada y tratada: el clúster devuelve **502 con `Retry-After: 60`** de forma esporádica; el script reintenta limitando la espera a 30 s por intento en vez de colgarse.

## Instalarla en otra instalación de Hermes

```bash
# 1. copiar la carpeta (o descomprimir el tar.gz) en el directorio de skills
cp -a nan-image-generation "$HERMES_HOME/skills/creative/"

# 2. dar la clave
export NAN_API_KEY=sk-...
# o dejarla en el entorno del servicio / config de esa instalación

# 3. abrir una sesión nueva (Hermes descubre skills al arrancar) y comprobar
python3 "$HERMES_HOME/skills/creative/nan-image-generation/scripts/nan_image.py" models
```

`$HERMES_HOME` es `/opt/data` aquí y normalmente `~/.hermes` en una instalación estándar. En destino solo hacen falta `python3` y la clave: el script no tiene dependencias. Si prefieres no copiar nada, esa instalación puede leerla desde fuera añadiendo la ruta padre a `skills.external_dirs` en su `config.yaml` (los directorios externos son de solo lectura).