# Arquitectura Técnica

La arquitectura tecnológica del sistema se fundamenta en un diseño por capas desacopladas, garantizando resiliencia operacional, alta disponibilidad y capacidad de funcionamiento ininterrumpido en entornos industriales aislados.

## Capas del Sistema

* **Capa de Captura e Ingesta:** Frontend liviano implementado bajo estándares modernos de Aplicación Web Progresiva (PWA), optimizado para bajo consumo de memoria y compatibilidad total con dispositivos Android e iOS de gama media o superior.
* **Capa de Negocio y Procesamiento:** Microservicios en contenedores Docker ejecutando validaciones de negocio en tiempo real, normalización de esquemas de datos y motores de cálculo estadístico.
* **Capa de Persistencia y Seguridad:** Base de datos relacional robusta con réplica asíncrona, cifrado en reposo (AES-256) y en tránsito (TLS 1.3), respaldada por bitácoras de auditoría inmutables.

## Capacidad Offline-First

Considerando la variabilidad de cobertura de red móvil y Wi-Fi en operaciones mineras e industriales, la plataforma incorpora almacenamiento local transaccional mediante IndexedDB en el dispositivo. Las transacciones se almacenan y validan localmente cuando no existe señal, y se sincronizan de forma automática y bidireccional mediante un protocolo de resolución determinística de conflictos en cuanto el equipo restablece la conectividad.
