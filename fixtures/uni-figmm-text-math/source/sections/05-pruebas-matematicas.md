# Pruebas matemáticas suplementarias

Esta sección contiene datos y ecuaciones creados para probar el formateador;
no forma parte de la tesis original ni presenta resultados de investigación.

## Expresiones en línea

La variable $x_i^2$ prueba subíndices y exponentes. El área $A = 12.4$ se usa
únicamente como dato sintético.

## Ecuaciones numeradas

La expresión @eq:promedio prueba una referencia anterior a su destino.

:::equation {#eq:promedio}
\bar{x} = \frac{1}{n}\sum_{i=1}^{n} x_i
:::

La ecuación @eq:promedio contiene una fracción y una sumatoria.

## Expresión sin numeración

Esta expresión no debe consumir un número de la secuencia.

$$
a^2 + b^2 = c^2
$$

## Segunda ecuación numerada

:::equation {#eq:raiz}
r = \sqrt{\frac{x_1^2 + x_2^2}{2}}
:::

La ecuación @eq:raiz prueba raíces, fracciones y subíndices. Su número debe
seguir inmediatamente al de @eq:promedio aunque haya una expresión sin número
entre ambas.
