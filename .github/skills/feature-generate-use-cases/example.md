# Summary
- Plan de pruebas para el login y la emisión de tokens firmados, basado en los criterios de aceptación de HU-01.
- La HU está marcada como usable con ajustes; quedan decisiones técnicas pendientes.

# Scope
- **Dentro del alcance**
  - Verificar los claims `sub`, `client`, `iat` y `exp`.
  - Verificar la validación de `client` recibido en la solicitud.
  - Comprobar la coherencia de `expiresIn` con `exp - now` dentro de la tolerancia documentada.
  - Probar login válido, credenciales inválidas y token expirado.
  - Comprobar que los logs no incluyan tokens, secretos ni valores sensibles.
- **Fuera del alcance**
  - Casos o requisitos que HU-01 no especifica.

# Supuestos
- Se prueban el endpoint existente `POST /auth/login` y los datos de respuesta indicados en la HU.
- No se asumen reglas de validación para `client`, una tolerancia temporal ni objetivos de rendimiento; deben definirse antes de concretar esos casos.

# Decisiones técnicas por tomar (pendientes o resueltas)
- Pendiente: decidir si se conserva HMAC o se adopta una librería JWT.
- Pendiente: definir la tolerancia de expiración que se usará en las comprobaciones.
- Pendiente: decidir si se elimina el secreto por defecto fuera del laboratorio o se documenta como exclusivo del laboratorio.
- Pendiente: especificar las reglas de validación de `client`.

# Riesgos y mitigaciones
- **Token o secreto expuesto en logs:** comprobar los logs de los escenarios de prueba y adjuntar evidencia de su redacción.
- **`client` inválido incluido en el token:** probar la validación una vez definidas sus reglas.
- **`expiresIn` inconsistente con `exp`:** documentar la tolerancia y comprobar la diferencia respecto de `exp - now`.

# Técnicas de prueba
- **Unitarias:** verificar claims requeridos, coherencia de expiración y errores de autenticación.
- **Funcionales:** probar login válido, credenciales inválidas y token expirado.
- **Seguridad (comprobaciones mínimas):** verificar que tokens, secretos y valores sensibles no aparezcan en logs; revisar la configuración documentada del secreto.
- **Contables:** no se describen cálculos ni reglas contables en HU-01.
- **Performance:** HU-01 no define objetivos ni umbrales de rendimiento; no se pueden especificar pruebas medibles todavía.

# Tareas sugeridas por rol
- **QA**
  - Preparar casos para login válido, credenciales inválidas y token expirado.
  - Verificar los cuatro claims requeridos en un token válido.
  - Comprobar `expiresIn` frente a `exp - now` usando la tolerancia acordada.
  - Revisar los logs de las pruebas y adjuntar evidencia de que no exponen valores sensibles.
  - Registrar resultados de pruebas y cualquier decisión pendiente que impida ejecutarlas.

# Preguntas abiertas
- ¿Qué reglas debe cumplir `client` para ser válido?
- ¿Qué tolerancia se documentará para comprobar la expiración?
- ¿Se conservará HMAC o se adoptará una librería JWT?
- ¿Se eliminará el secreto por defecto fuera del laboratorio o se documentará como exclusivo del laboratorio?
- ¿Se requieren pruebas de rendimiento? Si es así, ¿qué objetivos o umbrales deben verificarse?