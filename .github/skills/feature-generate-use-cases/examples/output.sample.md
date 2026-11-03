# Ejemplo: emisión de token al iniciar sesión

1. **Summary**
   - Al iniciar sesión, el servicio emite un token firmado con los claims `sub`, `client`, `iat` y `exp`.
   - El caso contempla login válido, credenciales inválidas y token expirado.

2. **Scope**
    - **Dentro del alcance**
      - Obtener y validar `client` desde la solicitud, y reflejarlo en el token.
      - Mantener `expiresIn` coherente con `exp - now` dentro de una tolerancia documentada.
      - Evitar registrar tokens, secretos y valores sensibles.
    - **Fuera del alcance**
      - Cambios no descritos en HU-01.

3. **Supuestos**
   - El endpoint existente es `POST /auth/login` y devuelve `token`, `expiresIn` y `user`.
   - La HU no determina la regla para validar `client`, la tolerancia de expiración ni la alternativa de firma.

4. **Decisiones técnicas por tomar (pendientes o resueltas)**
   - Pendiente: decidir si se conserva HMAC o se adopta una librería JWT.
   - Pendiente: definir la tolerancia para comprobar `expiresIn` frente a `exp - now`.
   - Pendiente: decidir si se elimina el secreto por defecto fuera del laboratorio o se documenta como exclusivo del laboratorio.
   - Pendiente: especificar las reglas de validación de `client`.

5. **Riesgos y mitigaciones**
   - **Exposición de información sensible en logs:** evitar registrar tokens y secretos; comprobar los logs generados.
   - **Claim `client` incorrecto:** validar el valor recibido y probar casos válidos e inválidos.
   - **Expiración inconsistente:** documentar la tolerancia acordada y probar la relación entre `expiresIn` y `exp - now`.

6. **Técnicas de prueba**
    - **Unitarias:** verificar claims requeridos, expiración y errores de autenticación.
    - **Funcionales:** probar login válido, credenciales inválidas y token expirado.
    - **Seguridad (comprobaciones mínimas):** comprobar que tokens y secretos no aparezcan en logs y revisar la configuración documentada del secreto.
    - **Contables:** no se especifican requisitos contables en HU-01.
    - **Performance:** no se especifican métricas ni requisitos de rendimiento en HU-01.

7. **Tareas sugeridas por rol**
    - **QA**
      - Probar login válido, credenciales inválidas y token expirado.
      - Verificar que los tokens válidos contengan `sub`, `client`, `iat` y `exp`.
      - Comprobar la coherencia de `expiresIn` dentro de la tolerancia documentada.
      - Adjuntar resultados de pruebas y evidencia de logs redactados.

8. **Preguntas abiertas**
   - ¿Se conserva HMAC o se adopta una librería JWT?
   - ¿Qué tolerancia se aplicará a la comparación de expiración?
   - ¿Qué reglas debe cumplir `client` para ser válido?
   - ¿Cómo se tratará el secreto por defecto fuera del laboratorio?