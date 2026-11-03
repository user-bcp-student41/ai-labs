# Hallazgos

## API

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-API-01 | api | Token Base64 con secreto embebido y sin firma | Vulnerabilidad | Sigue aceptándose el formato Base64 con secreto fijo; no se verifican firma, emisor ni audiencia. La extracción del helper y los errores genéricos no resuelven el riesgo. El usuario pidió coordinar primero el contrato con el emisor JWT, por lo que este hallazgo sigue pendiente. | `api/app/security.py:9`, `api/app/security.py:17-29` | alta | Pendiente |
| H-API-02 | api | El cliente puede consultar y asignar tareas a otro owner | Vulnerabilidad | Pendiente: el servicio liga el owner a la identidad y rechaza valores distintos, pero esa identidad todavía procede del token Base64 sin firma de H-API-01. Un token falsificado puede suplantar otro usuario y eludir este control. | `api/app/service.py:35-91`, `api/app/security.py:9`, `api/app/security.py:17-29` | alta | Pendiente |
| H-API-03 | api | Filtros e inserts SQL concatenados | Vulnerabilidad | Resuelto: el repositorio usa parámetros SQLite para filtros, inserts y la lectura de la tarea creada. | `api/app/repository.py:61-96` | alta | Resuelto |
| H-API-04 | api | Nombre y contenido de archivo guardados sin validación | Vulnerabilidad | Pendiente: se rechazan rutas, extensiones no permitidas y archivos mayores de 5 MiB, pero los archivos usan un directorio compartido y el nombre enviado se reutiliza; una carga puede sobrescribir otra con el mismo nombre. Aislar el almacenamiento por owner o usar nombres de destino no colisionables. | `api/app/main.py:23-27`, `api/app/main.py:69-74`, `api/app/service.py:94-112` | alta | Pendiente |
| H-API-05 | api | Dependencias con advisories aplicables | Vulnerabilidad | Resuelto: los advisories oficiales identifican CVE-2025-66418 y CVE-2025-66471 para `urllib3` 2.5.0, y CVE-2026-40347 y CVE-2026-42561 para `python-multipart` 0.0.21. Se actualizaron a las versiones mínimas corregidas 2.6.0 y 0.0.27; la revisión de advisories y `pip check` no mostraron dependencias rotas. | `api/requirements.txt:4-5`; [GHSA-gm62-xv2j-4w53](https://github.com/advisories/GHSA-gm62-xv2j-4w53), [GHSA-2xpw-w6gg-jr37](https://github.com/advisories/GHSA-2xpw-w6gg-jr37), [GHSA-mj87-hwqh-73pj](https://github.com/advisories/GHSA-mj87-hwqh-73pj), [GHSA-pp6c-gr5w-3c5g](https://github.com/advisories/GHSA-pp6c-gr5w-3c5g) | alta | Resuelto |
| H-API-06 | api | Rutas, persistencia, reglas y serialización concentradas en un módulo | Refactor | Resuelto: modelos, seguridad, repositorio y servicios están separados de la composición y rutas HTTP; las formas de respuesta observadas se mantienen para solicitudes válidas. | `api/app/main.py:23-83`, `api/app/models.py:1-57`, `api/app/repository.py:1-96`, `api/app/service.py:1-168`, `api/app/security.py:1-30` | media | Resuelto |
| H-API-07 | api | Uso de `dict`/`Any`, excepciones amplias y lógica condicional anidada | Refactor | Resuelto: requests/responses e identidad tienen modelos Pydantic; se acotaron excepciones y se usan respuestas genéricas con logging del detalle; el resumen evita condicionales profundamente anidados. | `api/app/models.py:1-57`, `api/app/security.py:17-30`, `api/app/service.py:61-84`, `api/app/service.py:140-161` | baja | Resuelto |

## Contrato observado — API

`docs/ENDPOINTS.md` no existe; este resumen se deriva del código observado y no constituye un contrato acordado.

- Todas las rutas mostradas dependen de `legacy_identity`, que lee `Authorization`, decodifica Base64 y espera cuatro partes separadas por `|` (usuario, rol, expiración y secreto). Solo comprueba que la expiración no haya pasado y que el secreto coincida. `api/app/main.py:14-25`, `api/app/main.py:67-120`
- `GET /api/tasks?owner=...` devuelve una lista de tareas con `id`, `title`, `description`, `status`, `owner`, `priority` y `createdAt`. Si se omite `owner`, usa el usuario del token. `api/app/main.py:56-75`
- `POST /api/tasks` acepta un objeto JSON; `status` y `priority` tienen valores predeterminados y `owner` puede venir en el cuerpo. Responde `201` con la tarea creada. `api/app/main.py:77-88`
- `GET /api/summary?owner=...` devuelve `owner`, `total`, `byStatus` y `highPriorityOpen`; si se omite `owner`, usa el usuario del token. `api/app/main.py:90-105`
- `POST /api/requirements` recibe multipart con el campo `file`, guarda su contenido y responde `201` con `owner`, `fileName`, `storedAt` y `size`. `api/app/main.py:107-112`
- `GET /api/backend-health` devuelve `requestedBy`, `status` y `body`; consulta `AUTH_HEALTH_URL` o, por defecto, `http://localhost:8080/q/health`. `api/app/main.py:114-121`
- La aplicación usa SQLite en `WORKSHOP_DB_PATH` o `./data/workshop.db`, crea la tabla `tasks` y añade tres registros de ejemplo si está vacía. Comparte una conexión para las rutas y la cierra al apagar la aplicación. `api/app/main.py:29-43`, `api/app/main.py:35`, `api/app/main.py:123-124`

No se ejecutaron pruebas ni un análisis SCA durante Discovery.

## Comportamiento actualizado tras las correcciones

Se conservan los endpoints, métodos, códigos y formas de respuesta existentes para solicitudes válidas. No se creó `docs/ENDPOINTS.md` ni se considera que haya un contrato acordado adicional.

- `GET /api/tasks` y `GET /api/summary` siguen aceptando `owner`; cuando se omite o está vacío se usa la identidad del token. Un owner diferente se rechaza con `403`, pero la identidad no es confiable mientras siga activo el token Base64 sin firma de H-API-01. `api/app/main.py:48-67`, `api/app/service.py:35-91`, `api/app/security.py:17-29`
- `POST /api/tasks` conserva sus campos y defaults; el owner de creación queda ligado a la identidad y un owner diferente se rechaza con `403`. La protección depende de resolver H-API-01. `api/app/main.py:55-60`, `api/app/models.py:14-19`, `api/app/service.py:46-59`
- `POST /api/requirements` conserva el campo multipart y los campos de respuesta para archivos permitidos; admite `.txt`, `.md` y `.pdf` hasta 5 MiB. Nombres con separadores/ruta, otras extensiones y archivos mayores se rechazan, pero nombres repetidos pueden sobrescribir archivos en el directorio compartido. `api/app/main.py:23-27`, `api/app/main.py:69-74`, `api/app/service.py:18-25`, `api/app/service.py:94-112`
- `GET /api/backend-health` conserva `requestedBy`, `status` y `body`; ante errores mantiene `status: 0` pero devuelve mensaje genérico y registra el detalle en el servidor. `api/app/main.py:76-79`, `api/app/service.py:140-161`
- El token sigue siendo el formato Base64 legado hasta coordinar el emisor JWT; no se presenta H-API-01 como resuelto. `api/app/security.py:9`, `api/app/security.py:17-29`

## Candidatos de discovery — API

### H-API-08 — CORS con cualquier origen y credenciales
- Estado: Aprobado por el usuario; implementado, pendiente de revisión humana.
- Evidencia: `api/app/main.py:15-30`, `api/app/main.py:68-71`, `compose.yaml:10`, `api/tests/test_api.py:62-129`.
- Impacto: una política sin lista explícita de orígenes de confianza puede habilitar acceso cross-origin más amplio del previsto. El impacto efectivo depende de cómo el cliente envía sus credenciales y de los orígenes que deban estar autorizados.
- Prioridad propuesta: Media.
- Contrato potencialmente afectado: política CORS y acceso del frontend a la API desde el navegador.
- Cómo validarlo: `python tools/lab.py test api` — 7 pruebas pasaron; cobertura global de `app`: 91.94%. Se verificaron denegación por defecto, origen local configurado, origen no listado, métodos/encabezados y rechazo de `*`. Los orígenes para entornos distintos al Compose local y la revisión humana siguen pendientes.

### H-API-09 — Límite de carga aplicado después del parseo multipart
- Estado: CANDIDATO
- Evidencia: `api/app/main.py:67-74` recibe un `UploadFile` multipart antes de llamar al servicio; `api/app/service.py:129-139` aplica el límite durante la lectura de ese archivo. La prueba existente verifica el rechazo posterior de un archivo apenas mayor al límite: `api/tests/test_api.py:277-287`.
- Impacto: el parseo multipart puede consumir almacenamiento temporal antes de que el límite del servicio responda con rechazo; cargas grandes o concurrentes podrían presionar ese almacenamiento. La exposición depende también de los límites configurados en el servidor o infraestructura externa, que no se verifican aquí.
- Prioridad propuesta: Media.
- Contrato potencialmente afectado: límite de tamaño y disponibilidad del endpoint `POST /api/requirements`.
- Cómo validarlo: probar cargas multipart grandes y concurrentes en un entorno aislado, observar el almacenamiento temporal hasta recibir la respuesta y confirmar si existe un límite de cuerpo efectivo antes del parseo.

### H-API-10 — La imagen no declara un usuario no privilegiado
- Estado: CANDIDATO
- Evidencia: `api/Dockerfile:1-9` usa una imagen base y define el comando de inicio, pero no declara `USER`.
- Impacto: si el runtime no establece un usuario distinto, el proceso de la API podría ejecutarse con el usuario predeterminado de la imagen base, ampliando el impacto de una vulneración del proceso dentro del contenedor.
- Prioridad propuesta: Media.
- Contrato potencialmente afectado: configuración de ejecución y privilegios del contenedor de API.
- Cómo validarlo: construir la imagen y comprobar el usuario efectivo con `docker run --rm <imagen> id`; contrastarlo con cualquier sobreescritura de usuario aplicada por el entorno de ejecución.
