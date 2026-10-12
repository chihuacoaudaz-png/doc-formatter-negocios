# Supuestos y Riesgos

El cumplimiento exitoso de los plazos y objetivos pactados depende del cumplimiento de premisas operativas clave por parte del cliente, así como de la gestión activa de los riesgos identificados.

## Supuestos Críticos

* Disponibilidad de Enlaces: El cliente designará formalmente un enlace técnico y un enlace operativo durante los primeros 2 días hábiles tras la aprobación.
* Acceso a Instalaciones: Se facilitarán los permisos de ingreso a planta y mina para las jornadas de levantamiento en terreno conforme al programa de seguridad vigente.
* Muestras de Datos Reales: Se proveerá acceso a muestras históricas anonimizadas de reportes de guardia y partes diarios para parametrizar las reglas del MVP.

## Cláusula de Congelamiento de Alcance (Scope Freezing)

Cualquier funcionalidad no contemplada expresamente en el apartado *In-Scope* de la presente propuesta técnica será considerada una solicitud de cambio y se programará para fases subsiguientes, previa cotización formal y aprobación escrita del Sponsor Ejecutivo.

## Matriz de Riesgos y Mitigación

:::table {#tbl:matriz-riesgos}
title: Matriz de Riesgos Operativos, Probabilidad, Impacto y Medidas Preventivas
note: Evaluación de criticidad realizada por el equipo de PMO y operaciones
---
| Riesgo Identificado | Probabilidad e Impacto | Medida de Mitigación Preventiva |
|---|---|---|
| Resistencia al cambio en operadores | Media y Alto | Diseño ergonómico de interfaces de un solo toque y talleres prácticos de inducción |
| Baja cobertura de red en frentes de trabajo | Alto y Medio | Arquitectura Offline-First con persistencia local y sincronización diferida |
| Demora en aprobaciones internas de compuerta | Baja y Alto | Calendario de reuniones ejecutivas pre-agendadas con el Sponsor al inicio del proyecto |
:::

La gestión continua de @tbl:matriz-riesgos garantiza la estabilidad operacional y el cumplimiento estricto del cronograma establecido.
