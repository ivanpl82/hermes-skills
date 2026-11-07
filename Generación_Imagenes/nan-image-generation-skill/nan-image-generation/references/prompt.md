# Construcción del prompt

## Orden canónico

Los modelos dan más peso a lo que va primero. Escribe en este orden, en un solo párrafo o dos:

1. **Sujeto + acción** — la frase que define la imagen. Concreta, con un detalle que solo existe ahí.
2. **Entorno** — dónde, cuándo, qué hay alrededor que importe.
3. **Composición y cámara** — plano, ángulo, altura, distancia focal, profundidad de campo.
4. **Estilo y medio** — fotografía/ilustración/3D/grabado, referencias de época o género.
5. **Luz y atmósfera** — dirección, dureza, hora, temperatura, emoción.
6. **Paleta** — tres o cuatro colores dominantes, mejor con nombre que con hex.
7. **Acabado** — película, grano, textura, defectos ópticos (o su ausencia).
8. **Texto literal**, si lo hay — entre comillas, con idioma, tipografía y ubicación.
9. **Restricciones**, cortas — al final y en positivo cuando se pueda.

Longitud útil: 40–90 palabras. Por encima de ~120, el detalle se diluye y el modelo empieza a inventar.

## Reglas de escritura

- **Sustantivos concretos antes que adjetivos.** "Cuchara de madera gastada" > "cuchara rústica bonita".
- **Nada de meta-instrucciones.** Fuera "genera una imagen de", "por favor", "alta calidad, 8k, obra maestra". No aportan y desplazan lo que sí importa.
- **Una luz dominante**, no tres. "Luz cálida rasante desde la izquierda" es accionable; "luz dramática y suave y natural" se contradice.
- **Negativos en positivo y en corto.** "Fondo liso, sin objetos" mejor que "sin nada, sin fondo, sin elementos, sin distracciones". Máximo dos o tres.
- **Personas**: describe edad aparente, complexión y ropa. Si es contenido adulto legítimo, deja explícito "adulto/a" o una edad claramente adulta, y que la persona es ficticia cuando lo sea.
- **Manos y texto** son los dos puntos flacos: si salen en plano, o los justificas en la composición o los evitas ("manos fuera de plano").
- **Idioma del prompt: inglés.** El brief y la conversación, en español.

## Notas por modelo

**qwen-image-2.1** (por defecto)
- Adherencia alta: obedece instrucciones literales, así que sé preciso y no contradictorio.
- El mejor para **texto legible**: comillas, idioma y ubicación ("the word ABIERTO in clean sans-serif, centred on the glass door").
- Tolera prompts más largos, pero pierde matices si hay muchos elementos secundarios.
- Máximo 1280 px por lado; sin `guidance`; solo text-to-image.

**flux-2-klein**
- Mejor grano fotográfico y estética cinematográfica; `guidance` (heurística habitual 2.5–4.5) sube o baja la fidelidad al prompt.
- Es el único que edita, con hasta 4 referencias.
- En edición, el prompt describe **el cambio**, no la escena entera; y lo que debe quedarse se nombra explícitamente (no hay máscara).

## Plantillas

**Texto a imagen**

```
<Subject + action, con un detalle concreto>. <Setting: lugar, hora, qué rodea>.
<Plano y cámara: medium shot at eye level, 35mm, shallow depth of field>.
<Estilo: documentary photography / two-colour woodcut / clean vector illustration>.
<Luz: warm low sunlight from the left, long shadows, calm mood>.
<Paleta: terracotta, ochre, leaf green>. <Acabado: Fujifilm Portra 400, fine grain>.
<Texto, si lo hay>. <Restricciones, cortas>.
```

**Edición**

```
Change only <lo que cambia>. Keep <lo que debe permanecer: subject, framing, palette, lighting>.
Same composition and same depth of field. <Restricciones>.
```

## Del brief al prompt: ejemplo

Brief:

```
Use Case: cabecera de artículo de gastronomía
Subject: una panadera de unos 60 años sacando hogazas del horno
Action: a media acción, con la pala de madera
Setting: obrador de barrio, madrugada
Art Style: fotografía documental
Composition: plano medio, a la altura del pecho, tercios
Lighting: luz cálida del horno desde abajo, resto en penumbra
Palette: pan dorado, harina, azul de delantal
Lens: 35 mm, grano fino
Ratio: 16:9  ·  Resolution: 1280  ·  Background: contextual
Negative: sin texto, sin marca de agua, sin manos deformes
```

Prompt:

```
A baker in her sixties pulling loaves from a brick oven with a long wooden peel, mid-motion, flour dust in the air. Small neighbourhood bakery at 4 a.m., trays and cloth-lined baskets around her. Medium shot at chest height, slightly off-centre, 35mm lens, shallow depth of field. Documentary photography, available light only. Warm orange glow from the oven mouth lighting her from below, the rest of the room in cool shadow. Golden crust, flour white, faded blue apron. Fine film grain, natural colour. No text, no watermark, hands out of frame.
```

## Iteración: qué tocar para qué síntoma

| Síntoma | Qué cambiar (una cosa) |
|---|---|
| Ignora el estilo | mueve el estilo al principio y quita la mitad de las referencias |
| Composición centrada y sosa | añade "off-centre, negative space on the left" |
| Luz plana | especifica dirección y fuente ("single window on the right") |
| Texto mal escrito | acorta el texto, ponlo entre comillas y en qwen |
| Fondo con ruido | "plain seamless background" y baja el número de elementos |
| Manos raras | reencuadra para sacarlas de plano |
| Demasiado limpio, plástico | "natural skin texture, slight imperfections, no retouching" |
| Colores apagados | nombra 3 colores y quita "muted" |
| Cambia lo que debía preservar (edit) | repite la lista de preservación en la primera frase |
| No hay forma de acertar | baja el número de elementos del prompt a la mitad |

Cada iteración: mismo seed o distinto según lo que busques (mismo seed = compara solo el cambio del prompt; seed distinto = busca otra tirada). Guarda siempre el `.json` de la imagen buena.
