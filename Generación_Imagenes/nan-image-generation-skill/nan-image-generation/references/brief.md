# Brief: qué preguntar y cómo

## Regla general

Preguntar es un medio, no el objetivo. Antes de preguntar, rellena con lo que ya sabes del mensaje. Solo se pregunta lo que cambia el resultado de forma visible. Máximo dos rondas: una para los obligatorios, otra para el resto.

## Ronda 1 — obligatorios (bloquea)

**Use Case Category.** No es decorativo: fija formato, nivel de detalle y qué se considera éxito. Si el usuario dice "una imagen de mi producto", falta saber si es para la ficha de la tienda (fondo limpio, cuadrado), para un anuncio (16:9, espacio para copy) o para una presentación (16:9, estilo coherente con la diapositiva).

Pregunta tipo: *"¿Para qué es la imagen? Ficha de producto, anuncio en redes, cabecera de artículo, presentación, concepto…"*

**Subject.** Concreto y en una frase. "Un perro" es insuficiente; "un galgo viejo con un jersey de lana" da al modelo algo que dibujar. Si el sujeto es una persona real, aquí se aplica la política de suplantación.

Pregunta tipo: *"¿Quién o qué aparece? Descríbelo en una frase."*

## Ronda 2 — el resto (una sola vez, opcional)

Se piden todos, se aceptan vacíos. Orden recomendado (de más a menos impacto visual):

| Campo | Para qué sirve | Ejemplo |
|---|---|---|
| Action / Activity | evita poses genéricas y de maniquí | "sirviendo café, a media acción" |
| Setting / Location | da contexto y coherencia de fondo | "cocina de bar a las 7 de la mañana" |
| Art Style | medio y estética | "fotografía documental", "grabado a dos tintas" |
| Composition / Camera | plano, ángulo, aire | "plano medio a la altura de los ojos, tercios" |
| Lighting & Mood | hora, dirección, emoción | "luz cálida rasante desde la izquierda, tranquilo" |
| Aspect Ratio | proporción final | "4:5 para Instagram", "16:9" |
| Generation Mode | generar o editar | "editar esta foto" |
| Resolution | lado largo en px | "1280 para impresión pequeña" |
| Background Mode | fondo | "liso", "contextual", "degradado", "transparente" |
| Color Palette | dominantes | "terracota, ocre, verde hoja" |
| Camera / Lens / Film Stock | óptica y textura | "35 mm, Portra 400, grano fino" |
| Intended Use | web, impresión, redes | "impresión A3" |
| Preserve (edit) | qué no debe cambiar | "el rostro, el logotipo, el encuadre" |
| Text to Include | texto literal | "'ABIERTO', español, en el cartel" |
| Negative Constraints | lo que no quieres | "sin marcas de agua, sin manos deformes" |

### Cómo preguntar

- **Cinco campos o menos** → herramienta `clarify`, una entrada por campo, opciones cortas y una salida tipo "decide tú" implícita en el texto de la pregunta si procede.
- **Más de cinco** → un único mensaje con lista numerada y una línea de instrucciones: *"Responde solo los que te importen; el resto lo decido yo."* Nunca una pregunta por mensaje.
- No repitas la pregunta si el usuario ya la contestó de forma implícita ("fondo blanco" cubre Background Mode y parte de Lighting).
- Si responde "lo que veas", aplica los presets y di en una frase qué has asumido.

## Presets por caso de uso

Cuando el usuario delega o no contesta, estos son los valores por defecto razonables:

| Use Case | Estilo | Aspect / lado largo | Fondo | Notas |
|---|---|---|---|---|
| Ficha de producto | foto de estudio, luz suave difusa | 1:1, 1280 | liso claro o transparente | sin sombras duras; deja aire arriba |
| Anuncio en redes | editorial, color saturado | 4:5, 1280 | contextual | espacio negativo para copy arriba |
| Cabecera de artículo | documental o ilustración | 16:9, 1280 | contextual | tercios, no centrar el sujeto |
| Presentación | ilustración limpia, paleta sobria | 16:9, 1280 | liso o degradado suave | coherencia entre diapositivas |
| Retrato editorial | foto 85 mm, luz ventana | 4:5, 1280 | contextual desenfocado | piel sin retoque plástico |
| Cartel con texto | gráfico, alto contraste | 3:4, 1280 | liso o color plano | qwen-image-2.1 obligatorio |
| Escena conceptual | ilustración cinematográfica | 3:2, 1280 | contextual | luz motivada, no genérica |
| Infografía / diagrama | vector limpio, plano | 1:1, 1280 | liso | mejor generar la base y montar texto aparte |

## Lo que no se pregunta

- Detalles técnicos del endpoint (modelo, seed, `n`): los decide el agente.
- Cosas que ya están en el mensaje.
- Preferencias que no cambian la imagen (p. ej. el nombre del archivo).

## Ejemplo de ronda corta

> **Usuario:** "Hazme una foto de mi cafetería para Instagram."
>
> **Agente:** *"Para acertar: ¿qué quieres que se vea —la barra con el barista trabajando, un primer plano del café, o el local vacío y ordenado? ¿Y prefieres a primera hora con luz cálida o a media tarde? Con eso genero; el resto (4:5, fondo contextual, tonos cálidos) lo decido yo salvo que me digas otra cosa."*
