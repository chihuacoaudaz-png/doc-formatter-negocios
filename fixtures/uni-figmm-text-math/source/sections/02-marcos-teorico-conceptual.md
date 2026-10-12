# Marcos teórico y conceptual

## Marco teórico

### Sobrerotura en minería subterránea

La sobrerotura en la minería subterránea es un fenómeno que se presenta tras la voladura, cuando la sección real ostenta mayor dimensión que la sección planificada, el material fragmentado en exceso comparado con el material fragmentado deseado se identifica como sobrerotura.

Matemáticamente la sobrerotura se puede expresar mediante la siguiente fórmula:

:::equation {#eq:sobrerotura}
\text{Sobrerotura}\% = \frac{\text{Sección real volada} - \text{Sección planificada}}{\text{Sección planificada}} \times 100
:::

:::figure {#fig:sobrerotura}
src: assets/sobrerotura.png
title: Imagen representativa de la sobrerotura.
note: El grafico resalta la zona roja como la sobrerotura de la sección planificada. Fuente propia.
width: 60%
:::

Si no se controla la sobrerotura, las operaciones mineras pueden suplir de muchas deficiencias, entre la cuales tenemos: inestabilidad estructural del macizo rocoso circundante, incremento en los costos de sostenimiento, interrupciones en el ciclo de minado, aumento de riesgo de accidentes, etc. El MINEM enfatiza en sus regulaciones aplicar buenas prácticas en el diseño y ejecución de voladuras para mitigar riesgos y optimizar la estabilidad del macizo rocoso (DS N.º 024-2016-EM), entonces se puede mitigar o reducir la sobrerotura si es que se tiene un diseño de malla de perforación adecuada, sin embargo, para ostentar ello se deben tener en cuenta factores como la calidad de roca circundante, el tipo de explosivo que se desea utilizar, técnicas de voladura controlada y una supervisión constante, con este cuidado la sobrerotura disminuye aumentando la eficiencia en la realización de tareas y la productividad de la unidad minera.

### Sostenimiento en minería subterránea

Debido a los constantes accidentes presentados a lo largo de la historia en las minas subterráneas una de las áreas más desarrolladas e implementadas actualmente es el área de geomecánica el cual se encarga del estudio y supervisión del sostenimiento de las labores subterráneas. Son distintos los tipos de sostenimiento que se utilizan en las minas subterráneas esto depende de las condiciones geomecánicas y geoestructurales que presenta la roca, entre ellas tenemos:

#### Sostenimiento con uso de madera

El sostenimiento con madera se utilizaba desde la edad media (alrededor del sigo X), cuando las primeras minas se desarrollaban en Europa, esto debido a su fácil disponibilidad con las cual formaban andamios y soportes dentro de las minas. Conforme las minas subterráneas se fueron sofisticando más y profundizaban en los cuerpos mineralógicos era necesario crear blocks de madera donde se utilizaba barricas de madera, vigas de madera y andamiajes, con ello asegurar el avance y seguridad de la labor, sin embargo, este método en la actualidad es mal visto por los constantes incendios que se generaban en las minas de carbón y también en algunas minas con alta presencia de pirita.

#### Sostenimiento con uso de metales

A mediados del siglo XIX, las labores que presentaban las minas subterráneas eran más complicadas de manejar, las cargas que soportaban eran cada vez más pesadas y las calidades de roca en el interior de la mina estaban más dañadas, es por ello que se optó por el uso de cerchas y arcos metálicos para crear las famosas cimbras lo cual fue una útil herramienta de sostenimiento para esa época, en la actualidad se usan muy poco debido a su alto costo y su afectación con el medio ambiente.

#### Sostenimiento moderno

En la actualidad los principales métodos de sostenimiento que se utilizan son pernos de anclaje, mallas electrosoldadas y concreto lanzado (shotcrete); los cuales han presentado resultados satisfactorios para labores con larga vida, generan seguridad y confianza al trabajador para su desarrollo laboral.

##### Pernos de anclaje

Se utilizan para aportar tensión a bancos sueltos hacia un sistema más estable, el cual ayuda principalmente a prevenir el deslizamiento de rocas, existen distintos tipos de pernos de rocas según su necesidad:

- **Pernos Helicoidal:** Este perno ostenta un cuerpo en forma de espiral el cual proporciona un agarre mucho más efectivo entre los cuerpos rocosos para proporcionar mayor estabilidad, se complementan con inyecciones de resina y cemento.
- **Pernos Split Set:** Es una alternativa al perno helicoidal, pero con un costo mucho más barato debido a que se utilizan para labores con mejor calidad de roca y no necesitan mucho agarre.
- **Pernos Swellex:** Son pernos que ostentan la misma forma del Split set, pero se utiliza cuando la condición de roca circundante está muy fragmentada, este perno se infla con ayuda de aire comprimido y compacta los fragmentos de la roca remanente.

:::figure {#fig:perno-helicoidal}
src: assets/perno-helicoidal.png
title: Perno Helicoidal.
note: fuente https://images.app.goo.gl/JsgPujqjqGNF4Gs57 (Sistemas de Anclaje, DSI).
width: 55%
:::

##### Mallas electrosoldadas

Es un tipo de malla soldada formada de varillas de acero que están unidas mediante el proceso de soldadura eléctrica en forma de rejilla, a pesar de que ostentan una resistencia considerable, son muy flexibles y previenen la caída de bancos, se instalan con ayuda de pernos de anclaje y complementan la sostenibilidad en las minas subterráneas.

##### Concreto lanzado (shotcrete)

El shotcrete es una clase de sostenimiento versátil altamente utilizado en la minería subterránea, es una combinación de cemento, agua, arena y aditivos (acelerante de fraguado, retardantes y plastificantes) que es proyectado con ayuda de aire comprimido a las paredes las labores subterráneas, el shotcrete puede presentar resistencia de 25 a 45 MPa. El método de lanzado también ha ido evolucionando a lo largo del tiempo, actualmente las minas ostentan robots que reducen desperdicios y optimizan el lanzado de shotcrete.

Para calcular la necesidad de shotcrete se presenta la siguiente relación matemática:

:::equation {#eq:shotcrete}
\text{Shotcrete } \text{m}^3 = (2 \times \text{Altura} + \text{Ancho}) \times \text{Avance} \times 0.911
:::

### Mecanismo de fragmentación de la roca

Cuando al explosivo se le aplica una abrupta cantidad de energía superior a la energía química que atrae sus moléculas, estas se separan hasta conseguir un estado más estable, en este proceso se liberan principalmente gran cantidad de gases y energía mecánica en forma de ondas de presión, a este comportamiento se le conoce como reacción exotérmica. Sin embargo, no todos los explosivos reflejan los mismos resultados, esto se debe a que la velocidad de detonación en algunos es muy lenta y en otros es muy rápido, aquí se diferencian tres tipos de reacciones.

- **Combustión:** Es una reacción exotérmica de oxidación, su velocidad de denotación es menor a 1 m/s y se puede observar a simple vista en forma de llama.
- **Deflagración:** Es una reacción subsónica, debido a que su velocidad de detonación es mayor a la de la combustión, pero menor a la velocidad del sonido, esta reacción genera una onda de presión de $10^3$ atmosferas, por ello se le confunde con una explosión.
- **Detonación:** Es una reacción supersónica, ya que su velocidad de detonación supera la velocidad del sonido (entre 1500 a 9000 m/s) generando ondas de choque con altos gradientes de presión y temperatura, utilizables para la fragmentación de roca en minería.

La fragmentación de rocas se lleva a cabo principalmente por dos comportamientos que se realizan en la detonación de un explosivo.

En la primera fase, la onda de choque generada por la reacción exotérmica, con gran velocidad de detonación, representando el 10% de la energía total del explosivo, genera un fisuramiento radial. Cuando existe una cara libre las ondas de choque se reflejan creando un esfuerzo de tracción que facilitan la creación grietas y aumenta la ampliación del radio fisurado.

La segunda fase es cuando los gases liberados por esta reacción impulsan a los fragmentos creados por lo primera fase en dirección a la cara libre, incrementando así la abertura.

### Criterio de diseño de malla de perforación para voladura controlada

La voladura convencional frecuentemente afecta estructuralmente a las paredes y techo de las labores subterráneas generando inestabilidad, desprendimiento de bancos en un corto plazo y sobrerotura fuera de los estándares, para este problema se creó el criterio de voladura controlada que consiste en el uso de cargas explosivas de baja energía y perforación taladros cercanos entre sí, para crear un plano de rotura que limite la superficie final de la labor.

La voladura controlada también rige su fragmentación en el contorno por esfuerzos de la onda de choque y acción de gases de expansión, pero cuando los taladros se encuentran cercanos la interacción de las ondas de choque no solo generan las grietas radiales a lo largo del taladro, sino también producen esfuerzos de tracción perpendiculares al plano axial favoreciendo la propagación de grietas radiales en la dirección de corte proyectado, posteriormente estas grietas se agrandan con la interacción de los gases del explosivo generando un plano de rotura definido.

Para considerar una voladura como controlada en minería subterránea se deben cumplir las siguientes condiciones:

- **Perforación:** Diámetro de taladros de producción igual al diámetro de taladros de contorno, al perforar los taladros se debe mantener el paralelismo de acuerdo con el diseño del plano de rotura, el emboquillado no debe superar desviaciones de 0.1 a 0.15m en el fondo, el espaciamiento debe ser menor que el burden debido a que su relación debe estar en el rango de (0.5-0.8).
- **Carga explosiva:** Se deben usar explosivos de baja energía y velocidad, la carga debe estar desacoplada al taladro en una relación de 2:1, para facilitar la creación del plano de rotura se pueden intercalar taladros vacíos como guía entre los taladros con explosivo.
- **Carga en el fondo:** Es necesario la utilización de un explosivo potente para el cebado con la finalidad de asegurar el arranque y evitar que se formen tacos en el fondo del taladro después de la voladura.
- **Disparo:** El disparo de los taladros del contorno deben ser simultaneo, sin embargo, si el perímetro es grande se puede realizar en un máximo de dos o tres etapas con un retardo corto.

A lo largo de los años se han creado distintas técnicas, en su mayoría para casos particulares, pero existen dos técnicas genéricas en las minas subterráneas:

#### Voladura de precorte

Consiste en formar un plano de fractura antes de disparar la voladura principal, mediante taladros de bajo diámetro, cercanos entre sí, y con cargas explosivas de baja energía, desacoplados y disparados simultáneamente.

#### Voladura de recorte

Consiste en realizar la voladura de una fila de taladros cercanos y con cargas desacopladas después de la voladura de producción.

### Optimización en el diseño y cálculo de mallas de perforación: Modelo matemático de Holmberg

El modelo matemático de Holmberg, diseñado para simplificar los cálculos, divide el frente en cinco secciones, etiquetadas de A a E:

- **A:** Sección de corte.
- **B:** Sección de ayudas de hastiales.
- **C:** Sección de ayudas de corona.
- **D:** Sección de contorno.
- **E:** Sección de arrastres.

#### Avance por disparo

El primer paso en el modelo de Holmberg consiste en calcular el avance necesario por disparo. La ecuación que describe la profundidad del taladro, $H$, puede expresarse de la siguiente manera:

:::equation {#eq:profundidad-taladro}
H = 0.15 + 34.1 \times \emptyset - 39.4 \times \emptyset^2
:::

El avance $I$ es representado con el 95% de la profundidad del taladro, según la siguiente ecuación:

:::equation {#eq:avance}
I = 0.95 \times H
:::

Estas dos ecuaciones son aplicables siempre y cuando la desviación en la perforación no supere el 2%. Cuando no se cuenta con el diámetro adecuado del taladro vacío necesario para alcanzar el avance requerido, se utiliza un taladro vacío equivalente:

:::equation {#eq:diametro-equivalente}
\emptyset_2 = \emptyset \times \sqrt{NT}
:::

Donde $\emptyset_2$ representa el diámetro del taladro equivalente.

#### Arranque de cuatro secciones

La distancia entre el taladro vacío equivalente central y los taladros de la primera sección no debe exceder de $1.7 \times \emptyset_2$ (Langefors y Kilhstrom, 1963). Se recomienda calcular el burden tomando en cuenta:

:::equation {#eq:burden-b1}
B_1 = 1.5 \times \emptyset_2
:::

Cuando la desviación de perforación supera el 1%, se calcula el error de perforación $EP$:

:::equation {#eq:error-perforacion}
EP = \alpha \times I + \beta
:::

Donde $\alpha$ es la desviación angular (m/m), $I$ es la profundidad de los taladros (m) y $\beta$ es el error de emboquille (m).

El burden práctico queda determinado por:

:::equation {#eq:burden-practico-b1}
B_{1\text{practico}} = B - EP
:::

La concentración de carga lineal se calcula a partir de:

:::equation {#eq:carga-lineal-q1}
q_1 = 55 \times \emptyset \times \left(\frac{B_1}{\emptyset_2}\right)^{1.5} \times \left(B_1 - \frac{\emptyset_2}{2}\right) \times \frac{C}{0.4} \times \frac{1}{RWS_{\text{ANFO}}}
:::

Para calcular el resto de las secciones, se asume que existen huecos rectangulares de anchura $A_h$:

:::equation {#eq:burden-b}
B = 8.8 \times 10^{-2} \times \sqrt{\frac{A_h \times q \times RWS_{\text{ANFO}}}{\emptyset \times C}}
:::

:::equation {#eq:anchura-ah}
A_h = 2 \times (B_1 - EP)
:::

:::equation {#eq:burden-b2}
B_2 = 10.5 \times 10^{-2} \times \sqrt{\frac{(B_1 - EP) \times q \times RWS_{\text{ANFO}}}{\emptyset \times C}}
:::

:::equation {#eq:burden-b2-max}
B_{2\text{max}} = B - EP
:::

Limitaciones respecto a $B_2$:

:::equation {#eq:limitacion-b2-max}
B_2 \le 2 \times A_h
:::

:::equation {#eq:limitacion-b2-min}
B_2 \ge 0.5 \times A_h
:::

Si no se cumple la primera restricción, se ajusta la concentración lineal:

:::equation {#eq:carga-lineal-ajustada}
q_1 = \frac{540 \times \emptyset \times C \times A_h}{RWS_{\text{ANFO}}}
:::

Gustafsson (1973) sugiere: $B_2 = 0.7 \times B$. La longitud del retacado $T = 10 \times \emptyset$. El número de cartuchos se calcula con:

:::equation {#eq:numero-cartuchos}
\text{Número de cartuchos} = \text{ent}\left(\frac{q_1 \times L_c}{P_{\text{explo}}}\right)
:::

#### Cálculo de sección de arrastres

:::equation {#eq:ba-max}
BA_{\text{max}} = 0.9 \times \sqrt{\frac{q_1 \times RWS_{\text{ANFO}}}{C \times f \times (S/B)}}
:::

Donde $f = 1.45$ y $S/B = 1$. La constante de roca corregida $C = C + 0.05$ para $B \ge 1.4\text{m}$, y $C = C + 0.07B$ para $B < 1.4\text{m}$.

Número de taladros:

:::equation {#eq:nta}
NTA = \text{ent}\left(\frac{AT + 2 \times H \times \sin\gamma}{BA_{\text{max}}}\right) + 2
:::

Espaciamiento práctico del rincón:

:::equation {#eq:espaciamiento-rincon}
S_e = S_t - I \times \sin\alpha
:::

Burden práctico:

:::equation {#eq:burden-practico-ba}
BA = B - H \times \sin\alpha - EP
:::

Carga en el fondo y columna:

:::equation {#eq:carga-fondo-qfa}
q_{fa} = q_1
:::

:::equation {#eq:longitud-fondo-lcf}
L_{cf} = 1.25 \times BA
:::

:::equation {#eq:carga-columna-qca}
q_{ca} = 0.7 \times q_1
:::

:::equation {#eq:longitud-columna-lcc}
L_{cc} = H - L_{cf} - T_a
:::

#### Cálculo de sección de tajeo

Similar a los arrastres pero usando $f = 1.45$, $S/B = 1.25$ (hacia arriba/horizontal) o $f = 1.20$, $S/B = 1.25$ (hacia abajo). La concentración de columna es la mitad de la del fondo.

:::table {#tbl:fijacion-tajeos}
title: Valores de factor de fijación y relación (S/B) de los tajeos.
note: fuente Manual de perforación y voladura de rocas (p. 314), de Instituto Tecnológico GeoMinero de España, s.f.
---
| Dirección de salida de los taladros | Factor de fijación "f" | Relación $\frac{S}{B}$ |
|-------------------------------------|------------------------|------------------------|
| Hacia arriba y horizontalmente | 1.45 | 1.25 |
| Hacia abajo | 1.20 | 1.25 |
:::

Los valores de @tbl:fijacion-tajeos se usan al dimensionar la malla de producción en tajeo.

#### Cálculo de la sección de contorno

:::table {#tbl:fijacion-contorno}
title: Valores de factor de fijación y relación (S/B) del contorno.
note: fuente Manual de perforación y voladura de rocas (p. 314), de Instituto Tecnológico GeoMinero de España, s.f.
---
| Indicadores | Valores |
|-------------|---------|
| Factor de fijación "f" | 1.45 |
| Relación $\frac{S}{B}$ | 1.20 |
| Concentración de la carga de columna Ic | 0.5*If |
:::

Presión de taladro:

:::equation {#eq:presion-taladro}
P_t = 228 \times 10^{-6} \times \frac{\delta_e + VOD^2}{1 + 0.8 \times \delta_e}
:::

Presión efectiva:

:::equation {#eq:presion-efectiva}
P_{te} = P_t \times \left(\frac{\emptyset_c}{0.42 \times \emptyset}\right) \times 1000
:::

Concentración lineal mínima y efectiva:

:::equation {#eq:carga-contorno-qc}
q_c = 90 \times \emptyset^2
:::

:::equation {#eq:carga-contorno-qce}
q_{ce} = \delta_e \times 1000 \times \frac{\pi \times \emptyset_c^2 \times 10^{-6}}{4}
:::

Espaciamiento y burden en contorno:

:::equation {#eq:espaciamiento-contorno}
S_c = \emptyset \times \frac{P_{te} + \sigma_{\text{trac}}}{\sigma_{\text{trac}}}
:::

:::equation {#eq:burden-teorico-contorno}
BTC = \frac{S_c}{0.8}
:::

:::equation {#eq:burden-practico-contorno}
BPC = BTC - H \times \sin\gamma - EP
:::

Longitud de arco y número de taladros:

:::equation {#eq:long-arco}
\text{Long}_{\text{arco}} = \frac{\text{Ancho}^2 + 4fl^2}{4fl} \times \arcsin\left(\frac{4 \times \text{Ancho} \times fl}{\text{Ancho}^2 + 4fl^2}\right)
:::

:::equation {#eq:ntc}
NTC = \text{ent}\left(\frac{\text{Long}_{\text{arco}}}{S_c}\right) + 1
:::

## Marco conceptual

- **Geomecánica:** Ciencia que estudia el comportamiento de las rocas y su interacción con las estructuras subterráneas en minería.
- **Acelerante:** Aditivo utilizado en el concreto lanzado para acelerar el proceso de fraguado.
- **Explosivo:** Sustancia química empleada en minería para generar una reacción exotérmica controlada que facilita la fragmentación de la roca.
- **Reacción:** Proceso químico que ocurre durante la detonación de un explosivo (combustión, deflagración o detonación).
- **Fisuramiento:** Formación de grietas o fracturas en la roca debido a la acción de las ondas de choque generadas durante la detonación de explosivos.
- **Gases:** Subproductos de la detonación de los explosivos que generan presión elevada para impulsar los fragmentos.
- **Reflexión:** Comportamiento de las ondas de choque cuando encuentran una superficie libre.
- **Burden:** Distancia entre los taladros de perforación y la cara libre de la roca.
- **Taladro:** Hueco o cavidad realizada en la roca mediante perforadora, que servirá para almacenar los explosivos.
- **Interacción:** Comportamiento entre las ondas de choque generadas por los explosivos y las fracturas preexistentes en la roca.
- **Espaciamiento:** Distancia entre los taladros de perforación en una voladura controlada.
- **Emboquillado:** Alineación y desviación de los taladros respecto al fondo del agujero.
- **Desacoplamiento:** Técnica que consiste en dejar un espacio entre la carga explosiva y las paredes del taladro.
- **Cebado:** Colocación de explosivos de alta potencia en el fondo del taladro para asegurar el inicio adecuado de la voladura.
- **Cartuchos:** Unidades de explosivo que se colocan dentro de los taladros.
- **Presión:** Fuerza generada por los gases de la detonación en el interior del taladro.
- **Python:** Lenguaje de programación de alto nivel, interpretado y de propósito general, utilizado en minería y diversas aplicaciones tecnológicas.
- **Recursión:** Técnica en programación donde una función se llama a sí misma para resolver un problema más pequeño.
- **Módulo:** Conjunto de funciones y variables en un archivo, que organiza el código en Python.
- **Biblioteca:** Conjunto de módulos predefinidos que proporcionan funciones específicas sin necesidad de escribir el código desde cero.
- **Argumento:** Valor que se pasa a una función cuando se llama.
- **Parámetro:** Variable definida en una función que recibe los valores de los argumentos.
- **Método:** Función asociada a un objeto en programación orientada a objetos.
- **Constructor:** Método especial en Python que se invoca cuando se crea un objeto de una clase.
- **Herencia:** Principio en POO que permite que una clase derive características de otra.
- **Polimorfismo:** Capacidad de una función o método para manejar diferentes tipos de datos.
- **Encapsulamiento:** Principio que oculta la implementación interna de una clase y solo expone la interfaz necesaria.
