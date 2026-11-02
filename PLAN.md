# Plan de corrección

## API

### Alcance y condiciones

- Al crear este plan, los siete hallazgos H-API-01 a H-API-07 estaban `Pendiente`. Tras la revisión local del diff, H-API-01, H-API-02 y H-API-04 permanecen `Pendiente`; H-API-03, H-API-05, H-API-06 y H-API-07 siguen `Resuelto`.
- `docs/ENDPOINTS.md` no existe. El contrato observado y sus referencias están en `HALLAZGOS.md`; no se presenta como contrato acordado.
- Conservar rutas, métodos, códigos de éxito, campos y formatos de respuesta existentes para solicitudes válidas. Las correcciones de seguridad sí deben rechazar tokens no verificables, acceso a otro propietario y archivos fuera de política.
- No modificar `auth/` ni otros componentes. Para JWT, coordinar externamente el formato de claims, emisor, audiencia y clave con el emisor actual antes de implementar; no mantener aceptación de tokens Base64 sin firma como alternativa.
- No se ejecutaron pruebas ni análisis SCA y no consta aprobación humana. No cambiar umbrales de calidad. Antes del cierre, medir la cobertura del código modificado (meta mínima 85%) y registrar por separado el gate global de API.

### H-API-01 — Token Base64 con secreto embebido y sin firma

- **Problema:** `legacy_identity` confía en contenido Base64 y un secreto fijo; no verifica firma, emisor ni audiencia. Cambiar solo el lector sin coordinar al emisor dejaría el login integrado incompatible.
- **Cambio propuesto:** sustituir la decodificación casera por validación de JWT firmado con una biblioteca mantenida (PyJWT, dependencia nueva justificada por verificación criptográfica y claims estándar). Exigir algoritmo configurado, firma, `iss`, `aud` y `exp`; mapear identidad/rol a la estructura que consumen las rutas. Leer configuración de entorno, devolver error genérico y no aceptar tokens legacy. Usar claves aisladas de prueba; nunca secretos reales.
- **Archivos a tocar:** `api/requirements.txt`, `api/app/security.py` (nuevo), `api/app/main.py`, `api/app/models.py` (nuevo, identidad tipada), `api/tests/test_api.py`.
- **Caracterización antes de tocar código:** agregar pruebas de las respuestas actuales de endpoints con identidad válida y de rechazo de autorización ausente/malformada/expirada. Agregar pruebas de aceptación para JWT válido y rechazo por firma, emisor, audiencia o expiración incorrectos; estas últimas documentan el requisito de seguridad y pueden fallar antes del cambio. Acordar primero con el emisor los claims y la clave.

### H-API-02 — El cliente puede consultar y asignar tareas a otro owner

- **Problema:** `owner` de query y del cuerpo puede sustituir la identidad autenticada, exponiendo o atribuyendo datos a otro usuario.
- **Cambio propuesto:** derivar el propietario de `identity` verificada en servicios y repositorio. Mantener los parámetros/campos existentes por compatibilidad de forma, pero rechazar con `403` los intentos de operar sobre otro owner; no confiar en el valor enviado por el cliente. Si se requiere acceso de rol, definirlo explícitamente y cubrirlo con pruebas.
- **Archivos a tocar:** `api/app/main.py`, `api/app/models.py` (nuevo), `api/app/service.py` (nuevo), `api/app/repository.py` (nuevo), `api/tests/test_api.py`.
- **Caracterización antes de tocar código:** comprobar respuestas, orden y formato de `GET /api/tasks` y `GET /api/summary` para el owner autenticado, y creación con owner predeterminado. Añadir pruebas de seguridad para owner ajeno en query y cuerpo, que deben exigir rechazo y ausencia de lectura/escritura cruzada.

### H-API-03 — Filtros e inserts SQL concatenados

- **Problema:** valores de query y payload se interpolan en SQL y pueden alterar la consulta; el acceso posterior por id también concatena texto.
- **Cambio propuesto:** mover SQL al repositorio y usar placeholders SQLite en todos los filtros, inserts y consultas por id. Mantener columnas, orden, valores predeterminados y estructuras de respuesta observadas.
- **Archivos a tocar:** `api/app/main.py`, `api/app/repository.py` (nuevo), `api/app/service.py` (nuevo), `api/tests/test_api.py`.
- **Caracterización antes de tocar código:** fijar pruebas para listar tareas en orden, crear una tarea válida y comprobar su persistencia/representación, y calcular el resumen esperado. Añadir una prueba de texto con caracteres SQL que compruebe que el valor se almacena como dato literal y no altera registros ni filtros.

### H-API-04 — Nombre y contenido de archivo guardados sin validación

- **Problema:** el nombre recibido se combina directamente con el directorio y se lee el archivo completo en memoria; no hay límites de ruta, tipo ni tamaño.
- **Cambio propuesto:** validar y normalizar el nombre, restringirlo al directorio de uploads, aplicar allowlist de extensiones y límite de bytes mientras se lee en bloques, y rechazar archivos no válidos con error HTTP genérico. Mantener `POST /api/requirements`, el campo multipart `file` y la forma de respuesta para cargas válidas. Definir el límite y extensiones permitidas con el responsable del contrato antes de escribir las pruebas; representarlos con configuración/constantes nombradas, no valores mágicos.
- **Archivos a tocar:** `api/app/main.py`, `api/app/service.py` (nuevo), `api/app/models.py` (nuevo, si se tipa la respuesta), `api/tests/test_api.py`.
- **Caracterización antes de tocar código:** fijar la carga válida actual: `201`, campos de respuesta y bytes guardados iguales al archivo recibido. Añadir pruebas de rechazo para nombre de ruta, extensión no permitida y tamaño en el límite y sobre el límite una vez acordada la política.

### H-API-05 — Versiones de dependencias SCA señaladas por el RETO

- **Problema:** `requirements.txt` fija las versiones indicadas por el RETO; su presencia no demuestra por sí sola que exista un CVE aplicable.
- **Cambio propuesto:** obtener y conservar un informe de un escáner SCA aprobado para las dependencias resueltas; confirmar advisory, rango afectado y compatibilidad antes de cambiar versiones. Actualizar solo paquetes confirmados a versiones corregidas compatibles, sin silenciar hallazgos ni añadir herramientas al proyecto sin justificar.
- **Archivos a tocar:** inicialmente ninguno hasta contar con evidencia; después, solo `api/requirements.txt` y `api/tests/test_api.py` si la actualización exige adaptar pruebas.
- **Caracterización antes de tocar código/configuración:** guardar el resultado SCA de línea base para `urllib3` y `python-multipart` y ejecutar la suite actual en `api/`. No se inventa una prueba funcional para un cambio solo de dependencias; después de una actualización confirmada, repetir el escaneo y la suite.

### H-API-06 — Rutas, persistencia, reglas y serialización concentradas en un módulo

- **Problema:** configuración SQLite, consultas, reglas y construcción de respuestas conviven con las rutas; los cambios cruzan responsabilidades y dificultan pruebas aisladas.
- **Cambio propuesto:** separar modelos de request/response, seguridad, rutas, servicios y repositorio. Mantener `main.py` como composición de la app y sus rutas; centralizar reglas en funciones con una responsabilidad, nombres explícitos, sin duplicación ni anidamiento profundo. Esta estructura compartirá módulos con H-API-01, H-API-02, H-API-03 y H-API-07, evitando capas duplicadas.
- **Archivos a tocar:** `api/app/main.py`, `api/app/models.py` (nuevo), `api/app/security.py` (nuevo), `api/app/service.py` (nuevo), `api/app/repository.py` (nuevo), `api/tests/test_api.py`.
- **Caracterización antes de tocar código:** ampliar las pruebas de rutas para fijar métodos, códigos de éxito, campos, valores predeterminados y respuestas de lista, creación, resumen, carga y backend health. Usar SQLite temporal y simular la llamada de health para no depender de otro servicio; ejecutar las pruebas antes de mover responsabilidades.

### H-API-07 — Uso de `dict`/`Any`, excepciones amplias y lógica condicional anidada

- **Problema:** payloads y respuestas sin modelos específicos permiten datos inconsistentes; los `except Exception` mezclan fallos y backend health puede devolver detalles internos; el cálculo anidado de resumen dificulta mantener sus reglas.
- **Cambio propuesto:** definir modelos Pydantic tipados para requests, identidad y respuestas, preservando nombres de campos, defaults y formato JSON observado. Extraer el cálculo de resumen a una función pequeña con condiciones combinadas/retornos tempranos. Capturar únicamente excepciones esperadas, responder con mensajes genéricos y registrar los detalles en servidor sin exponerlos al cliente. Centralizar límites y demás valores configurables como constantes con nombre.
- **Archivos a tocar:** `api/app/main.py`, `api/app/models.py` (nuevo), `api/app/service.py` (nuevo), `api/app/security.py` (nuevo), `api/tests/test_api.py`.
- **Caracterización antes de tocar código:** fijar campos y valores predeterminados de creación, formato de todas las respuestas y resultados de resumen para estados y prioridades observados. Añadir casos de payload inválido y fallo de backend health para verificar respuesta pública genérica y que no incluya la excepción interna.

### Secuencia y validación propuestas

1. Resolver coordinación del emisor JWT y política de extensión/tamaño de archivo; registrar el contrato acordado antes de implementar cambios que afecten esas integraciones.
2. Escribir y ejecutar las caracterizaciones indicadas desde `api/` antes de modificar los archivos de aplicación. Registrar resultados reales; no marcar pruebas no ejecutadas como aprobadas.
3. Implementar seguridad de token, autorización, SQL parametrizado y carga segura; separar capas y modelos en cambios revisables, manteniendo los formatos de éxito acordados.
4. Ejecutar `python -m pytest` desde `api/`, repetir el SCA con el mismo escáner y método de línea base, y medir cobertura del código modificado y cobertura global sin reducir gates.
5. Actualizar `HALLAZGOS.md` solo con resultados observados; documentar después el contrato acordado y ejecuciones reales en los entregables correspondientes.

### Aprobación, decisiones y ejecución

- **Aprobación humana:** el usuario confirmó “estan aprobados todos los hallazgos” el 2026-11-02. Aprobados H-API-01 a H-API-07.
- **Política H-API-04:** permitir `.txt`, `.md` y `.pdf`, con máximo de 5 MiB por archivo, según la selección del usuario del 2026-11-02.
- **Bloqueo H-API-01:** el usuario eligió coordinar primero el contrato con el emisor JWT. No modificar la autenticación API ni aceptar JWT sin contrato confirmado; H-API-01 permanece pendiente y no se cambia `auth/`.
- **Ejecución base — componente api; IDs H-API-01 a H-API-07:** desde `api/`, `python -m pytest` falló porque el Python global no tiene `pytest` (`No module named pytest`). El intérprete seleccionado de `api/.venv` sí lo tiene.
- **Ejecución base — componente api; IDs H-API-01 a H-API-07:** desde `api/`, `.\.venv\Scripts\python.exe -m pytest` pasó: 4 pruebas, 11 warnings deprecación; código aún sin modificar.
- **Caracterización previa — componente api; IDs H-API-02 a H-API-04 y H-API-06 a H-API-07:** tras añadir pruebas y antes de cambiar la aplicación, `.\.venv\Scripts\python.exe -m pytest --tb=short` dio 8 pasadas y 10 fallidas esperadas: H-API-02 (2), H-API-03 (2), H-API-04 (3) y H-API-07 (3). Las caracterizaciones de contrato de H-API-06 pasaron. H-API-01 no se modifica mientras espera coordinación; H-API-05 no tiene prueba funcional.
- **SCA previo — componente api; H-API-05:** el escáner compartido `appmod-cve-assessment` no acepta el ecosistema PyPI, así que se contrastaron los advisories oficiales de GitHub. `urllib3==2.5.0` está afectado por CVE-2025-66418 (GHSA-gm62-xv2j-4w53; solicitudes HTTP a orígenes no confiables) y CVE-2025-66471 (GHSA-2xpw-w6gg-jr37; uso streaming); ambas recomiendan `urllib3>=2.6.0`. `python-multipart==0.0.21` está afectado por CVE-2026-40347 (GHSA-mj87-hwqh-73pj) y CVE-2026-42561 (GHSA-pp6c-gr5w-3c5g); se requiere `python-multipart>=0.0.27`. Referencias: [GHSA-gm62-xv2j-4w53](https://github.com/advisories/GHSA-gm62-xv2j-4w53), [GHSA-2xpw-w6gg-jr37](https://github.com/advisories/GHSA-2xpw-w6gg-jr37), [GHSA-mj87-hwqh-73pj](https://github.com/advisories/GHSA-mj87-hwqh-73pj), [GHSA-pp6c-gr5w-3c5g](https://github.com/advisories/GHSA-pp6c-gr5w-3c5g). Próximo paso: actualizar solo a esas versiones mínimas y volver a comprobar los advisories.

### Resultados de implementación por hallazgo

| ID | Cambio/diff | Antes del cambio | Después del cambio |
|---|---|---|---|
| H-API-01 | Pendiente; no se reemplazó el parser Base64 porque el usuario pidió coordinar primero el contrato con el emisor externo. El helper se movió a `api/app/security.py` como parte de H-API-06 y ahora devuelve error genérico, pero sigue sin verificar firma, emisor ni audiencia. | Suite base con el token legacy: 4 pruebas pasaron. | Las pruebas de token legacy siguen pasando dentro de la suite; no hay prueba JWT ni resolución del riesgo. Mantener `Pendiente`. |
| H-API-02 | `api/app/main.py`, `api/app/service.py`, `api/app/models.py`: identidad es fuente de owner; otro owner en query/cuerpo responde `403`. | Las dos pruebas de acceso/cruce de owner fallaron: 200 y 201 donde se esperaba 403. | Las pruebas pasan, pero la revisión encontró que el token Base64 legacy permite falsificar la identidad usada por el control. Se devuelve a `Pendiente` hasta resolver H-API-01 y volver a verificar la autorización. |
| H-API-03 | `api/app/repository.py`: filtros, inserts y lookup por id usan parámetros SQLite. | Las dos pruebas con apóstrofes fallaron con HTTP 500. | Las dos pruebas pasan: texto literal se guarda y el filtro literal devuelve lista vacía. |
| H-API-04 | `api/app/service.py`: rechaza separadores de ruta, aplica allowlist `.txt`/`.md`/`.pdf` y limita lectura a 5 MiB. | Tres pruebas fallaron: path, extensión prohibida y archivo sobre límite recibían 201. | Las pruebas de ruta, extensión y tamaño pasan, pero la revisión detectó que un archivo con nombre repetido sobrescribe otro en el directorio compartido. Se devuelve a `Pendiente` hasta evitar colisiones/aislar almacenamiento y añadir una prueba. |
| H-API-05 | `api/requirements.txt`: `urllib3==2.6.0`, `python-multipart==0.0.27`. | Advisories oficiales confirmaron las cuatro CVE indicadas arriba en las versiones anteriores. | `pip show` confirmó las versiones corregidas instaladas; los advisories indican esos mínimos como corregidos; `pip check` informó que no hay requirements rotos. No hay escáner automático registrado para PyPI en `appmod-cve-assessment`, por lo que no se afirma un escaneo integral de todas las transitivas. |
| H-API-06 | `api/app/main.py`, `api/app/models.py`, `api/app/security.py`, `api/app/repository.py`, `api/app/service.py`: composición/rutas, DTOs, autenticación actual, persistencia y reglas quedaron en módulos separados. | Las caracterizaciones de formatos y respuestas válidas pasaron antes del refactor. | Las mismas caracterizaciones pasan después; los endpoints, campos y códigos de éxito para peticiones válidas se mantienen. |
| H-API-07 | `api/app/models.py`, `api/app/security.py`, `api/app/service.py`: modelos Pydantic, excepciones acotadas, mensajes genéricos con logging y resumen sin anidamiento profundo. | Tres pruebas fallaron: payload inválido aceptado, detalle del token filtrado y error interno de health devuelto. | Las tres pasan; la validación devuelve 422 y las respuestas de error no incluyen detalles internos. |

### Registro de ejecuciones

- **Componente api; H-API-01 a H-API-07; línea base:** `python -m pytest` falló por ejecutar un intérprete sin `pytest`; con `.\.venv\Scripts\python.exe -m pytest` resultó `4 passed`.
- **Componente api; H-API-02 a H-API-04 y H-API-06 a H-API-07; caracterización pre-cambio:** `.\.venv\Scripts\python.exe -m pytest --tb=short` resultó `8 passed, 10 failed` (fallos esperados de corrección: H-API-02 2, H-API-03 2, H-API-04 3, H-API-07 3).
- **Componente api; H-API-02 a H-API-07; iteración de verificación:** `.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing` dio `16 passed, 2 failed` porque los stubs de prueba de backend health no aceptaban el argumento keyword `timeout`; se corrigió la firma del mock antes de la ejecución final.
- **Componente api; H-API-01 a H-API-07; regresión final:** `.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing` resultó `18 passed`. Cobertura total `96%`; módulos modificados: `main.py` y `models.py` 100%, `repository.py` 93%, `security.py` 91%, `service.py` 95%. La meta de 85% se cumple para el código de aplicación medido.
- **Componente api; H-API-05:** `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` instaló las versiones fijadas; `.\.venv\Scripts\python.exe -m pip check` informó `No broken requirements found`.
- **Componente api; H-API-01 a H-API-07:** Pylance no reportó errores de tipos/imports en archivos modificados; permanece una advertencia deprecada preexistente por `FastAPI.on_event` en `api/app/main.py:81`. No se cambió porque no forma parte del plan.

### Desviación y pendiente

H-API-01 no queda resuelto: falta coordinar el contrato JWT con el emisor fuera de este alcance, tal como eligió el usuario. No se modificó ningún otro componente ni se agregó una dependencia JWT. La revisión también devuelve H-API-02 a `Pendiente` porque su autorización depende de esa identidad no verificada, y H-API-04 a `Pendiente` por colisiones de nombres entre owners. Solo H-API-03, H-API-05, H-API-06 y H-API-07 quedan resueltos.

### Revisión local del diff

- La revisión se hizo sobre `git diff main -- api/` y las secciones API de los documentos permitidos. El worktree inicialmente estaba en `main`; como solo existía esa rama local, se creó y activó `day1/prompting` sin commit, conservando el diff local.
- **Bloqueante — H-API-01/H-API-02:** `api/app/security.py:9,17-29` sigue derivando identidad de Base64 y secreto fijo sin firma. Las rutas dependen de esa identidad (`api/app/main.py:49-50,57,64,71,77`); por ello el guardado de owner por identidad no acredita aislamiento real. H-API-02 vuelve a `Pendiente`.
- **Importante — H-API-04:** `api/app/service.py:99-112` guarda en el directorio común con el nombre aportado, y `write_bytes` reemplaza un destino existente. Añadir aislamiento por owner o nombre de destino no colisionable, más una prueba de dos cargas con igual nombre, antes de resolver.
- **Ejecución de pruebas:** el revisor no las volvió a ejecutar; los resultados de la implementación arriba se conservan como evidencia previa, no como una validación independiente de esta revisión.

### Actualización de alcance

La propuesta siguiente es la planificación vigente únicamente para H-API-02 y H-API-04, ambos `Pendiente` en `HALLAZGOS.md`. Conserva las secciones anteriores como historial. El contrato detallado ya está en `docs/ENDPOINTS.md`; la política de carga acordada es `.txt`, `.md` y `.pdf`, máximo 5 MiB. No se modificarán endpoints ni el formato de respuesta.

## Item: H-API-02 — El cliente puede consultar y asignar tareas a otro owner

- **Hallazgo de `HALLAZGOS.md`:** H-API-02, componente `api`, severidad alta, estado `Pendiente`.
- **Problema:** las rutas aceptan `owner` en query o en el cuerpo. El servicio actualmente rechaza un owner distinto y consulta/crea usando `identity.username`, pero esa identidad todavía se obtiene del token Base64 sin firma de H-API-01 (`api/app/service.py:35-91`, `api/app/security.py:17-29`). Mientras la autenticación no sea verificable, un cliente puede falsificar la identidad y eludir la autorización.
- **Cambio propuesto:** conservar `GET /api/tasks`, `GET /api/summary` y `POST /api/tasks`, sus parámetros/campos, respuestas y `403` para un owner distinto. Asegurar que toda lectura y creación use exclusivamente la identidad ya verificada; no usar `owner` enviado por el cliente como identidad ni permitir una ruta que evada el servicio. No incluir la sustitución del parser/token dentro de este item: la coordinación del emisor y la verificación criptográfica pertenecen a H-API-01. H-API-01 es una precondición externa; hasta que exista una identidad confiable, no se puede declarar H-API-02 corregido.
- **Archivos a tocar:** `api/app/service.py` y `api/tests/test_api.py`. Tocar `api/app/main.py` o `api/app/repository.py` solo si las pruebas previas demuestran un bypass o una consulta que no usa la identidad. `api/app/security.py` y `api/requirements.txt` quedan fuera de este item porque cambiar autenticación/dependencias corresponde a H-API-01.
- **Pruebas antes de tocar código:** en `api/tests/test_api.py`, ampliar las caracterizaciones existentes `test_list_and_summary_reject_another_owner` y `test_create_rejects_another_owner`. Con `TestClient` y SQLite temporal, verificar que el usuario autenticado puede listar/resumir y crear para sí mismo; que `owner` omitido/vacío conserva el comportamiento documentado; que un owner distinto en cada query devuelve `403 {"detail":"Forbidden"}` sin exponer tareas ajenas; y que un owner distinto en el cuerpo devuelve `403` sin insertar una tarea. Cuando el contrato JWT de H-API-01 esté coordinado, repetir los casos con dos identidades realmente verificadas y comprobar que el segundo usuario no puede leer ni atribuir datos al primero. La suite existente ya contiene pruebas con el token legacy, pero no prueba la autenticidad criptográfica de esas identidades.
- **Ejecución:** no se ejecutaron pruebas ni se modificó código al crear esta propuesta.

## Item: H-API-04 — Nombre y contenido de archivo guardados sin aislamiento contra colisiones

- **Hallazgo de `HALLAZGOS.md`:** H-API-04, componente `api`, severidad alta, estado `Pendiente`.
- **Problema:** `store_requirement` valida ruta, extensión y tamaño, pero escribe el nombre recibido directamente en el directorio compartido (`api/app/service.py:94-112`). Dos cargas con el mismo nombre pueden escribir el mismo destino y la segunda reemplaza el contenido de la primera.
- **Cambio propuesto:** conservar la validación existente y generar un destino de almacenamiento único en el servidor, creándolo de manera exclusiva para impedir sobrescrituras. Puede usarse `uuid` de la biblioteca estándar, sin dependencia nueva. Mantener el nombre original en `fileName`, el tamaño en `size`, el owner en `owner`, el estado `201` y `storedAt` como string con la ruta real al archivo guardado; no cambiar el esquema de respuesta. El valor concreto de la ruta puede variar, como ya indica `docs/ENDPOINTS.md`. No modificar `docs/ENDPOINTS.md`, límites, extensiones ni autenticación dentro de este item.
- **Archivos a tocar:** `api/app/service.py` y `api/tests/test_api.py`. `api/app/main.py`, `api/app/models.py`, `api/requirements.txt` y `docs/ENDPOINTS.md` no requieren cambios previstos.
- **Pruebas antes de tocar código:** primero caracterizar en `api/tests/test_api.py` una carga válida comprobando `201`, los campos documentados, que `storedAt` identifica un archivo existente y que sus bytes coinciden con la carga. Añadir después una prueba de regresión con dos identidades distintas que suben contenidos diferentes usando el mismo `fileName`; exigir dos rutas `storedAt` distintas y comprobar que ambos archivos conservan sus bytes originales. Esta prueba de colisión debe fallar con el destino compartido actual y no debe relajarse para aceptar la sobrescritura. Mantener las pruebas existentes de ruta, extensión, archivo exactamente de 5 MiB y archivo mayor de 5 MiB.
- **Ejecución:** no se ejecutaron pruebas ni se modificó código al crear esta propuesta.
