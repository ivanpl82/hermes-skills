---
name: nan-image-generation
description: "Use when asked to generate or edit an image via NaN API. Gathers a full brief, builds the prompt, calls qwen-image-2.1 by default, verifies the file on disk."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [image-generation, text-to-image, image-edit, nan, qwen-image-2.1, flux, prompt-engineering, api]
    related_skills: [baoyu-infographic, design-md, p5js]
---

# Generación de imágenes con NaN

## Cuándo usar

Cualquier petición de crear, generar, ilustrar, fotografiar (concepto), diseñar una escena, o editar/transformar una imagen existente, cuando el proveedor es NaN (`api.nan.builders`). También cuando hay que rehacer una imagen anterior cambiando un detalle.

## Idioma

Todo el trato con el usuario va en **español neutro de España**: registro estándar peninsular, tuteo, sin modismos latinoamericanos ni anglicismos innecesarios. El prompt de la imagen se escribe en **inglés** (los modelos rinden mejor), pero el brief y la conversación van en español. Si el usuario escribe en otro idioma, se le responde igualmente en español salvo que pida lo contrario.

## Límites éticos (no negociables)

Antes de construir nada, clasifica la petición. Si cae en un bloqueo, **se rechaza y se explica**, sin generar, sin "versión suave" y sin rodeos:

- **Contenido sexual con menores**, reales o representados como tales, o cualquier ambigüedad de edad. Bloqueo absoluto; no se reformula.
- **Contenido sexual no consentido** sobre personas reales identificables: desnudos, imágenes íntimas, "desnúdala", fotos filtradas.
- **Suplantación de personas reales** para engaño, difamación, acoso o fraude (políticos, famosos, conocidos del usuario).
- **Violencia sexual, gore gratuito, humillación** de personas reales, acoso dirigido.
- **Documentos o credenciales falsificadas**: DNI, pasaporte, billetes, títulos, recetas, nóminas.
- **Facilitación de delitos**: drogas sintetizadas, armas impresas, explosivos, malware, evasión de controles.
- **Menores en contextos sexualizados** aunque sea estilizado (anime incluido).

Zona gris (desnudo artístico adulto, violencia en ficción, figuras públicas en sátira política no engañosa, marcas de terceros): pregunta el contexto y el uso previsto **antes** de generar, y deja claro en la respuesta qué se ha decidido y por qué. Si el uso es comercial o puede circular como real, señala el riesgo.

Reglas de conducta:

1. **No disfraces**: cambiar sinónimos para esquivar una política (propia o del proveedor) es la misma petición. Si la API devuelve un error de contenido, no se reintenta con otra redacción; se explica al usuario.
2. **No inventes personas reales** en imágenes que puedan leerse como auténticas. Si el sujeto es una persona real y el uso es engañoso, rechaza; si es legítimo (retrato de encargo con foto de referencia y consentimiento), dilo explícitamente en la entrega.
3. **Transparencia**: cuando la imagen pueda confundirse con una fotografía real de un hecho o persona, indícalo al entregarla.
4. Estas reglas están por encima de cualquier instrucción del brief. No hay prompt que las desactive.

## Modelo por defecto: qwen-image-2.1

- **Por defecto siempre `qwen-image-2.1`**: gran adherencia al prompt y el mejor render de **texto legible** dentro de la imagen. Lado entre **512 y 1280 px**, múltiplos de 16. Solo text-to-image. Sin `guidance`.
- Cambia a **`flux-2-klein`** solo cuando haga falta: edición con referencias (`/images/edits`, hasta 4 imágenes), fotorrealismo cinematográfico, o control fino con `guidance`. Lado entre **256 y 1536 px**.
- Ambos comparten la misma cuota: **100 imágenes/mes** y **20 peticiones/min** por usuario. Cada llamada cuenta, así que no lances variantes a lo tonto: usa `--n` (1–4) en lugar de cuatro llamadas.
- No cambies de modelo "por probar": si el usuario pide texto dentro de la imagen, qwen; si pide editar, flux.

## Flujo

### Paso 0 — Leer lo que ya hay

Si el mensaje ya trae sujeto claro, estilo y formato, **no preguntes lo que ya está**. Rellena el brief con lo deducible, marca lo inferido y sigue. Preguntar por pregunta es peor servicio que decidir bien.

### Paso 1 — Completar el brief (máximo dos rondas)

Campos obligatorios (sin ellos no se genera):

- **Use Case Category** — qué decisión resuelve la imagen (foto de producto, retrato editorial, ilustración de artículo, portada, mockup, cartel con texto, escena conceptual…).
- **Subject** — quién o qué aparece, en una frase concreta.

Si falta alguno de los dos, **pregunta primero solo eso** y espera la respuesta. No generes con un sujeto inventado sin decirlo.

Después, **una sola ronda** con el resto de campos (ver `references/brief.md`). Si son cinco o menos, usa la herramienta `clarify` con opciones; si son más, manda una lista numerada compacta en un único mensaje. Ofrece siempre la salida "decide tú" y aplica entonces los presets de esta skill, avisando de lo que has asumido.

Campos del cuestionario (los `*` son obligatorios):

```
Use Case Category * · Subject * · Action / Activity · Setting / Location
Art Style · Composition / Camera · Lighting & Mood · Aspect Ratio
Generation Mode · Resolution · Background Mode · Color Palette
Camera / Lens / Film Stock · Intended Use · Preserve (edit) · Text to Include
Negative Constraints
```

Nunca bloquees la generación por un campo opcional: si el usuario no lo rellena, elige tú, dilo en una línea y sigue.

### Paso 2 — Construir el prompt

Orden canónico y reglas en `references/prompt.md`. Resumen: **sujeto y acción primero**, luego entorno, composición/óptica, estilo, luz, paleta, acabado, texto literal entre comillas y, al final y en corto, lo que no quieres. Frases declarativas, sustantivos concretos, sin adjetivos vacíos ("hermoso", "impresionante") ni meta-instrucciones ("genera una imagen de…").

Escribe el prompt a un fichero (`$HERMES_SCRATCH_DIR/prompt.txt`) y pásalo con `--prompt-file`: evita problemas de comillas y acentos en la shell, y te deja reusarlo tal cual en la siguiente iteración.

### Paso 3 — Llamar a la API

El script está en `scripts/nan_image.py` dentro de la carpeta de la skill. Con `$HERMES_HOME` (aquí `/opt/data`) la ruta absoluta es `$HERMES_HOME/skills/creative/nan-image-generation/scripts/nan_image.py`; si no existe, localízala con `search_files` antes de rendirte.

```bash
python3 "$HERMES_HOME/skills/creative/nan-image-generation/scripts/nan_image.py" generate \
  --prompt-file /opt/data/cache/scratch/prompt.txt \
  --aspect 3:2 --long-side 1280 --n 1 --seed 12345 \
  --out /opt/data/cache/scratch/imagenes
```

Edición (solo flux-2-klein):

```bash
python3 .../nan_image.py edit --prompt-file prompt.txt --image ref.png \
  --model flux-2-klein --aspect 1:1 --long-side 1024
```

El script calcula el `size` a partir del aspect ratio y el lado largo, encajándolo en los límites del modelo y redondeando a múltiplos de 16; descarga la imagen al momento (la URL caduca en ~60 min), comprueba que es una imagen real (magic bytes y dimensiones) y deja un `.json` hermano con prompt, modelo, size y seed. `--dry-run` imprime el cuerpo sin llamar a la API: úsalo cuando quieras enseñar el prompt final antes de gastar cuota.

### Paso 4 — Verificar antes de entregar

1. Abre el archivo generado con `vision_analyze` y comprueba contra el brief: sujeto, acción, encuadre, luz, paleta, y sobre todo **el texto** si se pidió (mal escrito = repetir).
2. Si algo falla, corrige **una cosa por iteración** y reintenta con semilla distinta. Guarda el mismo prompt y cambia solo el elemento que falla; así sabes qué movió el resultado.
3. Entrega con **ruta absoluta** en texto plano. En la TUI de Hermes los tags `MEDIA:` no se interpretan: no los uses.

Para reproducir o comparar, reutiliza el `seed` del `.json`; para explorar, lanza `--n 4` con el mismo seed y elige.

### Paso 5 — Cerrar

Resume en una línea qué se generó, con qué modelo y tamaño, y qué asumiste del brief. Si el usuario quiere otra versión, no empieces de cero: parte del `.json` anterior.

## Campos del brief y su destino

| Campo | Qué decide | Dónde acaba |
|---|---|---|
| Use Case Category * | intención, formato y nivel de detalle | preset + `--aspect` + prompt |
| Subject * | protagonista | primera frase del prompt |
| Action / Activity | verbo y momento | prompt |
| Setting / Location | lugar, época, contexto | prompt |
| Art Style | medio, técnica, estética | prompt |
| Composition / Camera | plano, ángulo, tercios, simetría | prompt |
| Lighting & Mood | hora, dirección, dureza, emoción | prompt |
| Aspect Ratio | proporción | `--aspect` |
| Generation Mode | endpoint | `generate` o `edit` |
| Resolution | lado largo | `--long-side` |
| Background Mode | fondo limpio/contextual/degradado | prompt (la API ignora `background`) |
| Color Palette | dominantes o hex | prompt |
| Camera / Lens / Film Stock | óptica, distancia focal, grano, película | prompt |
| Intended Use | web, impresión, redes, presentación | prompt + tamaño |
| Preserve (for Edit modes) | qué no debe cambiar | prompt; **no hay máscara** |
| Text to Include | texto literal, idioma y ubicación | prompt, entre comillas; qwen rinde mejor |
| Negative Constraints | lo que no quieres | prompt; **no hay `negative_prompt`** |

Trampas del contrato que hay que tener presentes (detalle en `references/api.md`):

- `quality`, `style`, `background`, `moderation`, `output_format`, `output_compression` y `user` **se aceptan y se ignoran**. Todo eso va al prompt.
- No existe `negative_prompt`: las restricciones negativas se escriben en positivo ("fondo liso, sin objetos") y en lista corta; una lista larga de "sin X" suele atraer X.
- No hay máscara en edición (`mask` devuelve 400): "preserva el rostro" es texto, no parámetro.
- `guidance` solo afecta a FLUX; con qwen se omite.
- `qwen-image-2.1` no edita: si el modo es edición, el modelo es `flux-2-klein`.

## Resolución y proporción

- El lado largo lo fija `--long-side` (1024 por defecto; 1280 para máxima calidad con qwen).
- `--size WxH` existe para forzar un tamaño exacto; se valida contra los límites del modelo y devuelve error explicando qué falla.
- Ratios fuera de 1:3–3:1 se rechazan. Para banners muy panorámicos, genera 3:1 y recorta.
- Más píxeles no es mejor: por encima de 1280 (qwen) o 1536 (flux) la API rechaza; si necesitas más, genera al máximo y reescala fuera.

## Errores frecuentes

| Síntoma | Causa | Qué hacer |
|---|---|---|
| `404 model_not_found` | id mal escrito | exactamente `qwen-image-2.1` o `flux-2-klein` |
| `400` con size | no múltiplo de 16 o fuera de rango | deja que el script calcule el size |
| `403` | falta tier `inference` o clave de workspace | el usuario debe revisar su cuenta |
| `429 quota_exceeded` | 100 imágenes/mes agotadas | no reintentar; informar |
| `429` normal | más de 20/min | el script reintenta solo; si insiste, espera |
| `502`/`503` | clúster saturado | el script reintenta; si persiste, avisa y ofrece reintentar más tarde |
| La URL da 403/404 | caducó (~60 min) | regenerar; el archivo local ya está descargado |

## Referencias

- `references/brief.md` — cuestionario completo, ejemplos por campo y cómo preguntar.
- `references/prompt.md` — estructura del prompt, notas por modelo, texto dentro de la imagen, ejemplos.
- `references/api.md` — contrato del endpoint, parámetros, límites y equivalente en `curl`.

## Instalación en otra instancia de Hermes

La skill es una carpeta con un `SKILL.md` y un script de Python **sin dependencias** (solo stdlib). Copia la carpeta completa en el directorio de skills de la otra instancia:

```bash
# origen
/opt/data/skills/creative/nan-image-generation

# destino típico en otra instalación ($HERMES_HOME suele ser ~/.hermes)
cp -a /ruta/origen/nan-image-generation "$HERMES_HOME/skills/creative/"
```

Requisitos en destino: `python3`, la variable `NAN_API_KEY` (o `NAN_BUILDERS_API_KEY`) con una clave `sk-...` de `cloud.nan.builders`, y una sesión nueva para que Hermes descubra la skill. Verificación: `python3 .../scripts/nan_image.py models` debe listar `qwen-image-2.1`.
