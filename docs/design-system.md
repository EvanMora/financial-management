# Sistema de diseño

Los tokens viven en `app/static/css/tokens.css`. Este documento explica de dónde salen y cómo usarlos.

## Referencia

`docs/design-referencia.md` es una ficha de [Refero](https://styles.refero.design/style/a4f123f2-cd4b-4d26-998f-a3d3ee158024) que describe el estilo de la página del iPhone Duo en apple.com. Es una **inspiración**, no una marca que copiamos: la app no usa el nombre, el logo, la fuente SF Pro ni imágenes de Apple.

**Qué conservamos de la referencia**

- Fondo gris `#f5f5f7` con tarjetas blancas de 28px de radio y **sin sombras**: la profundidad sale del contraste entre blanco y gris.
- Texto casi negro `#1d1d1f` y un único azul de acción. La interfaz es monocromática y el color es escaso.
- Botones e inputs en forma de píldora.
- Títulos en peso 600, nunca 700, y tracking negativo en el texto.
- Barra de navegación de 44px, blanca translúcida con desenfoque.

**Qué adaptamos al dashboard**

| Referencia (página de producto) | En la app | Por qué |
|---|---|---|
| Titular de 80px y secciones a pantalla completa | Máximo 40px (saldo total); 48px solo en login | Un dashboard muestra datos, no cuenta una historia |
| 90px entre secciones | 40px entre grupos de tarjetas | Más información visible sin hacer scroll |
| Sin colores de estado | Verde, naranja y rojo con fondo propio | Ingresos, alertas y excesos de presupuesto |
| Fotografía de producto como protagonista | Las cifras y gráficas son las protagonistas | No hay producto físico que mostrar |
| SF Pro | Inter en todos los dispositivos | SF Pro no tiene licencia para uso web; Inter es libre, muy parecida y se ve igual en cualquier equipo |

## Reglas de color

- `--color-primary` (`#0071e3`) se usa **solo** como relleno del botón primario. Nunca como fondo de sección, texto o icono.
- `--color-link` (`#0066cc`) se usa para enlaces y acciones de texto.
- **Los gastos van en `--color-text` con signo "−"; no en rojo.** El rojo (`--color-danger`) se reserva para presupuestos excedidos, errores y acciones destructivas. Así el rojo conserva su fuerza como alerta y la app no parece estar siempre en problemas.
- Los ingresos van en `--color-income` con signo "+".
- `--color-warning` se usa cuando un presupuesto llega al 80 %.
- Cada color semántico tiene su fondo (`*-bg`). Los dos se usan juntos en avisos y etiquetas de estado.
- `--color-border` es decorativo (1.4:1). Si un borde es lo único que permite ver un control, usa `--color-border-strong`.

## Contraste (WCAG AA: 4.5:1 en texto normal)

| Token | Sobre blanco | Sobre `--color-canvas` |
|---|---|---|
| `--color-text` | 16.8 | 15.5 |
| `--color-text-secondary` | 4.95 | 4.55 |
| `--color-link` | 5.57 | 5.11 |
| `--color-income` | 5.19 | 4.77 |
| `--color-warning` | 5.28 | 4.85 |
| `--color-danger` | 5.38 | 4.94 |
| Blanco sobre `--color-primary` | 4.70 | — |

Los colores de estado también cumplen sobre su propio fondo `*-bg` (4.7:1 o más).

## Números

- **En columnas** (tablas, listas de movimientos, ejes) los montos usan `font-variant-numeric: var(--numeric);` (clase `.num`). Las cifras tabulares tienen el mismo ancho, así que los dígitos quedan alineados.
- **Cifras grandes sueltas** (el saldo total) usan números proporcionales, los normales de la fuente. Con tabulares, en tamaños grandes se ven separadas.

## Gráficas

- Una sola escala por gráfica. Si hay dos medidas distintas (ahorro mensual y saldo acumulado), van en dos gráficas.
- Columnas de máximo 24px, con esquinas de 4px arriba y rectas en la base. Líneas de 2px. Puntos de 8px con un aro de 2px del color de la superficie.
- El periodo actual va en el color fuerte (`--color-income` o `--color-text`) y los anteriores en el suave (`--chart-income-muted`, `--chart-ink-muted`).
- **No usamos colores categóricos.** Verde, naranja y rojo ya significan ingreso, alerta y exceso. Para comparar categorías se usan barras de un solo tono, con la mayor resaltada.
- Los estados (alerta, excedido) llevan siempre ícono y texto, nunca solo color.
- Con dos o más series hay leyenda. Con una sola, el título la nombra.
- El texto de las gráficas usa colores de texto, no el color de la serie.
- Las gráficas del dashboard real llevan tooltip al pasar el mouse. La vista previa del login no, porque es decorativa.

## Vidrio líquido

Solo para paneles que **flotan sobre contenido** (como la vista previa del login sobre su fondo de barras): `--glass-bg`, `--glass-blur` y `--glass-edge`. Sobre un fondo plano no aporta nada, porque no hay nada que se vea a través. Es un desvío consciente de la referencia, que es plana; aun así no lleva sombras. Los formularios y las tarjetas de datos principales siguen siendo blancos y sólidos para que se lean bien.

El fondo del login usa además **barras de vidrio verde** (cápsulas translúcidas con brillo en el borde superior). Son decoración, no una gráfica: no tienen ejes ni etiquetas, así que no siguen las reglas de la sección Gráficas. Se eligieron entre cinco variantes (verde sólido, degradado, grafito, azul y vidrio).

## Movimiento

- Duraciones: `--duration-fast` (hover y foco), `--duration-default` (cambios de estado), `--duration-slow` (entradas de paneles).
- Las entradas usan `--ease-emphasized` y se escalonan entre 40 y 90 ms por elemento.
- Todo se desactiva con `prefers-reduced-motion: reduce`: se muestra el estado final al instante.

## Tipografía

Inter se sirve desde `app/static/fonts/` (declarada con `@font-face` en `styles.css`), no desde Google Fonts: carga sin internet y no envía datos a terceros.

Inter va **primera** en la lista de fuentes. Si se pone `-apple-system` o `BlinkMacSystemFont` antes, Chrome en Linux (comprobado; posiblemente también en Windows) los toma como "fuente del sistema" y nunca llega a usar Inter.

`--font-display` va en títulos de 21px o más y `--font-text` en todo lo demás.

## No hacer

- Sombras en tarjetas, botones o modales.
- Degradados.
- Radios distintos a los definidos (nada de 8px ni 12px en tarjetas).
- Peso 700.
- Más de un color de acento en la misma vista.
