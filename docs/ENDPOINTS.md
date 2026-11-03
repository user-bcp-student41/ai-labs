# API FastAPI — contratos observados

Este documento describe los cinco endpoints actuales de ReqFlow API. Los ejemplos muestran el contrato HTTP observado; los valores `id`, fechas y rutas dependen de la base de datos, la hora y el sistema operativo.

## Estado del contrato

- **Observado:** rutas, campos, valores predeterminados y respuestas descritos aquí se derivan de `api/app/main.py`, `api/app/models.py`, `api/app/security.py` y `api/app/service.py`.
- **Acordado:** no había un contrato previo en `docs/ENDPOINTS.md`. Se conserva el formato de respuestas exitosas para solicitudes válidas. La política seleccionada para cargas acepta `.txt`, `.md` y `.pdf`, con máximo de 5 MiB.
- **Riesgos pendientes:** H-API-01 y H-API-02 están pendientes: el token actual es Base64 legacy sin firma, por lo que la identidad usada por la autorización no es confiable. H-API-04 está pendiente: un archivo puede sobrescribir otro si comparte nombre en el directorio de uploads.

## CORS de navegador

- Los orígenes permitidos se configuran mediante `API_CORS_ALLOWED_ORIGINS`, como una lista separada por comas de orígenes exactos (esquema, host y puerto).
- Si la variable no está configurada o está vacía en la aplicación, no se autoriza ningún origen cross-origin. Compose usa `http://localhost:4200` como valor local predeterminado solo cuando la variable no está definida; se puede sobrescribir por entorno o dejar explícitamente vacía para desactivar CORS. El valor `*` se rechaza.
- Se permiten los métodos `GET` y `POST`, y los encabezados `Authorization` y `Content-Type`. Las solicitudes con credenciales cross-origin no están habilitadas.
- En Compose, la variable se pasa al contenedor de API. El origen local predeterminado no debe usarse como sustituto de los orígenes reales de otros entornos.
- CORS es una política del navegador y no reemplaza la autenticación ni la autorización de los endpoints.

## Autenticación común

Todos los endpoints requieren el header `Authorization` en el formato observado `Bearer <token>`. Si falta o el token no se acepta, la respuesta es `401` con `{"detail":"Invalid token"}`. El mecanismo actual consume un token Base64 legacy; todavía no hay un contrato JWT coordinado. No se publica un token válido ni su secreto en estos ejemplos. La integración con un emisor JWT y un ejemplo autenticado ejecutable quedan como preguntas abiertas de H-API-01.

---

## `GET /api/tasks`

### 1. Qué hace

Lista las tareas del usuario autenticado, ordenadas por `id`.

### 2. Autenticación

Requiere `Authorization: Bearer <token>` según la autenticación común.

### 3. Request

| Campo/parámetro | Tipo | Obligatorio | Descripción |
|---|---|---:|---|
| `Authorization` (header) | string | Sí | Token aceptado por la autenticación común. |
| `owner` (query) | string | No | Si se omite o está vacío, se usa el usuario del token. Si se indica un valor distinto de la identidad, se responde `403`. |

Ejemplo HTTP:

```http
GET /api/tasks?owner=student HTTP/1.1
Host: localhost:8000
Authorization: Bearer <TOKEN_VALIDO>
```

`<TOKEN_VALIDO>` es un marcador, no un token ejecutable. El contrato de emisión aún está pendiente.

### 4. Response exitosa

**Estado:** `200 OK`.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | integer | Identificador de la tarea. |
| `title` | string | Título. |
| `description` | string | Descripción. |
| `status` | string | Estado almacenado. |
| `owner` | string | Usuario propietario. |
| `priority` | string | Prioridad almacenada. |
| `createdAt` | string | Fecha y hora creadas por SQLite. |

Ejemplo en una base recién inicializada:

```json
[
  {
    "id": 1,
    "title": "Refactor login",
    "description": "Separar responsabilidades en frontend",
    "status": "TODO",
    "owner": "student",
    "priority": "HIGH",
    "createdAt": "2026-11-02 16:00:00"
  },
  {
    "id": 2,
    "title": "Review API",
    "description": "Revisar seguridad de endpoints",
    "status": "IN_PROGRESS",
    "owner": "student",
    "priority": "MEDIUM",
    "createdAt": "2026-11-02 16:00:00"
  }
]
```

Los valores de `createdAt` son ilustrativos; SQLite asigna la hora de inserción.

### 5. Respuestas de error

| Estado | Cuándo ocurre | Ejemplo de cuerpo |
|---|---|---|
| `401 Unauthorized` | Header ausente o token inválido/expirado. | `{"detail":"Invalid token"}` |
| `403 Forbidden` | `owner` no coincide con la identidad del token. | `{"detail":"Forbidden"}` |
| `500 Internal Server Error` | Error de base de datos u otro error no manejado. El cuerpo lo genera el middleware del servidor, no un contrato específico de esta ruta. | `Internal Server Error` (texto genérico del servidor). |

### 6. Notas de seguridad

La consulta SQL usa un parámetro para `owner`, y el servicio consulta con la identidad, no con un owner ajeno. Sin embargo, la autenticación Base64 sin firma permite falsificar esa identidad; H-API-01 y H-API-02 siguen pendientes. Fuente: `api/app/main.py:48-53`, `api/app/service.py:35-44`, `api/app/repository.py:61-66`, `api/app/security.py:17-29`.

---

## `POST /api/tasks`

### 1. Qué hace

Crea una tarea para el usuario autenticado.

### 2. Autenticación

Requiere `Authorization: Bearer <token>` según la autenticación común.

### 3. Request

El cuerpo debe ser un objeto JSON; sus propiedades tienen estos tipos y valores predeterminados:

| Campo/parámetro | Tipo | Obligatorio | Descripción |
|---|---|---:|---|
| `Authorization` (header) | string | Sí | Token aceptado por la autenticación común. |
| `title` (JSON) | string | No | Título; predeterminado `""`. |
| `description` (JSON) | string | No | Descripción; predeterminado `""`. |
| `status` (JSON) | string | No | Estado; predeterminado `"TODO"`. |
| `priority` (JSON) | string | No | Prioridad; predeterminado `"MEDIUM"`. |
| `owner` (JSON) | string o null | No | Si se omite o es `null`, se usa el usuario autenticado. Un valor distinto de la identidad se rechaza con `403`. |

Ejemplo:

```http
POST /api/tasks HTTP/1.1
Host: localhost:8000
Authorization: Bearer <TOKEN_VALIDO>
Content-Type: application/json

{
  "title": "Review upload policy",
  "description": "Document the accepted file types",
  "status": "TODO",
  "priority": "MEDIUM",
  "owner": "student"
}
```

### 4. Response exitosa

**Estado:** `201 Created`. El objeto tiene los mismos campos que una tarea de `GET /api/tasks`.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | integer | Identificador asignado por SQLite. |
| `title` | string | Título almacenado. |
| `description` | string | Descripción almacenada. |
| `status` | string | Estado almacenado. |
| `owner` | string | Usuario autenticado. |
| `priority` | string | Prioridad almacenada. |
| `createdAt` | string | Fecha y hora de creación. |

Ejemplo:

```json
{
  "id": 4,
  "title": "Review upload policy",
  "description": "Document the accepted file types",
  "status": "TODO",
  "owner": "student",
  "priority": "MEDIUM",
  "createdAt": "2026-11-02 16:05:00"
}
```

El `id` y `createdAt` son dinámicos; el ejemplo supone una base recién inicializada con tres tareas sembradas.

### 5. Respuestas de error

| Estado | Cuándo ocurre | Ejemplo de cuerpo |
|---|---|---|
| `401 Unauthorized` | Header ausente o token inválido/expirado. | `{"detail":"Invalid token"}` |
| `403 Forbidden` | `owner` del cuerpo no coincide con la identidad del token. | `{"detail":"Forbidden"}` |
| `422 Unprocessable Entity` | Falta el objeto JSON o un campo presente no tiene el tipo declarado. | `{"detail":[{"type":"string_type","loc":["body","title"],"msg":"Input should be a valid string","input":[]}]}` |
| `500 Internal Server Error` | Error no manejado de persistencia u otro error interno. | `Internal Server Error` (texto genérico del servidor). |

### 6. Notas de seguridad

El servicio fuerza como propietario al usuario autenticado y no confía en un owner diferente. La identidad proviene del token legacy sin firma; no considerar esta protección suficiente hasta resolver H-API-01/H-API-02. Fuente: `api/app/main.py:55-60`, `api/app/models.py:14-19`, `api/app/service.py:46-59`, `api/app/security.py:17-29`.

---

## `GET /api/summary`

### 1. Qué hace

Resume el total de tareas, su distribución por estado y las tareas abiertas de prioridad alta del usuario autenticado.

### 2. Autenticación

Requiere `Authorization: Bearer <token>` según la autenticación común.

### 3. Request

| Campo/parámetro | Tipo | Obligatorio | Descripción |
|---|---|---:|---|
| `Authorization` (header) | string | Sí | Token aceptado por la autenticación común. |
| `owner` (query) | string | No | Si se omite o está vacío, se usa el usuario del token. Un valor distinto de la identidad se rechaza con `403`. |

Ejemplo HTTP:

```http
GET /api/summary?owner=student HTTP/1.1
Host: localhost:8000
Authorization: Bearer <TOKEN_VALIDO>
```

### 4. Response exitosa

**Estado:** `200 OK`.

| Campo | Tipo | Descripción |
|---|---|---|
| `owner` | string | Usuario del token. |
| `total` | integer | Número total de tareas del usuario. |
| `byStatus` | object con valores integer | Conteo de tareas por valor de `status`. |
| `highPriorityOpen` | integer | Tareas con prioridad `HIGH` cuyo estado no es `DONE` ni `ARCHIVED`. |

Ejemplo para las tareas iniciales del usuario `student`:

```json
{
  "owner": "student",
  "total": 2,
  "byStatus": {
    "TODO": 1,
    "IN_PROGRESS": 1
  },
  "highPriorityOpen": 1
}
```

### 5. Respuestas de error

| Estado | Cuándo ocurre | Ejemplo de cuerpo |
|---|---|---|
| `401 Unauthorized` | Header ausente o token inválido/expirado. | `{"detail":"Invalid token"}` |
| `403 Forbidden` | `owner` no coincide con la identidad del token. | `{"detail":"Forbidden"}` |
| `500 Internal Server Error` | Error de base de datos u otro error no manejado. | `Internal Server Error` (texto genérico del servidor). |

### 6. Notas de seguridad

El resumen filtra por la identidad y no permite elegir otra identidad mediante `owner`, pero la autenticación Base64 sin firma permite suplantar el usuario representado por ese token. H-API-01/H-API-02 siguen pendientes. Fuente: `api/app/main.py:62-67`, `api/app/service.py:61-84`, `api/app/repository.py:92-97`, `api/app/security.py:17-29`.

---

## `POST /api/requirements`

### 1. Qué hace

Guarda un archivo de requisitos subido para la identidad autenticada y devuelve sus metadatos.

### 2. Autenticación

Requiere `Authorization: Bearer <token>` según la autenticación común.

### 3. Request

| Campo/parámetro | Tipo | Obligatorio | Descripción |
|---|---|---:|---|
| `Authorization` (header) | string | Sí | Token aceptado por la autenticación común. |
| `file` (multipart) | archivo (`UploadFile`) | Sí | Archivo de hasta 5 MiB; extensión permitida: `.txt`, `.md` o `.pdf`. El nombre no puede contener componentes de ruta. |

Ejemplo (el archivo `requirement.txt` contiene exactamente `Requirement sample`, 18 bytes):

```http
POST /api/requirements HTTP/1.1
Host: localhost:8000
Authorization: Bearer <TOKEN_VALIDO>
Content-Type: multipart/form-data; boundary=example-boundary

--example-boundary
Content-Disposition: form-data; name="file"; filename="requirement.txt"
Content-Type: text/plain

Requirement sample
--example-boundary--
```

El límite de 5 MiB se aplica al contenido del archivo. Para clientes HTTP, enviar el archivo como parte multipart normal evita construir manualmente el boundary.

### 4. Response exitosa

**Estado:** `201 Created`.

| Campo | Tipo | Descripción |
|---|---|---|
| `owner` | string | Usuario del token. |
| `fileName` | string | Nombre validado del archivo. |
| `storedAt` | string | Ruta del archivo guardado; separadores y forma dependen del sistema operativo y `WORKSHOP_UPLOAD_DIR`. |
| `size` | integer | Tamaño del contenido en bytes. |

Ejemplo en Windows con el directorio predeterminado `./uploads`:

```json
{
  "owner": "student",
  "fileName": "requirement.txt",
  "storedAt": "uploads\\requirement.txt",
  "size": 18
}
```

### 5. Respuestas de error

| Estado | Cuándo ocurre | Ejemplo de cuerpo |
|---|---|---|
| `401 Unauthorized` | Header ausente o token inválido/expirado. | `{"detail":"Invalid token"}` |
| `400 Bad Request` | Nombre vacío o con separadores/componentes de ruta. | `{"detail":"Invalid file name"}` |
| `400 Bad Request` | Extensión distinta de `.txt`, `.md` o `.pdf`. | `{"detail":"Unsupported file type"}` |
| `413 Content Too Large` | Archivo mayor de 5 MiB. | `{"detail":"Uploaded file is too large"}` |
| `422 Unprocessable Entity` | Falta el campo multipart `file` o el multipart no se puede validar. | `{"detail":[{"type":"missing","loc":["body","file"],"msg":"Field required","input":null}]}` |
| `500 Internal Server Error` | `write_bytes` falla con `OSError`. | `{"detail":"Unable to store uploaded file"}` |

### 6. Notas de seguridad

La carga valida el nombre, la extensión y el tamaño antes de escribir. Sin embargo, el directorio es compartido y el nombre validado se usa como destino: dos usuarios pueden colisionar y una carga puede sobrescribir otra. H-API-04 sigue pendiente. La atribución a `owner` también depende del token legacy no firmado. Fuente: `api/app/main.py:23-27,69-74`, `api/app/service.py:18-25,94-138`, `api/app/security.py:17-29`.

---

## `GET /api/backend-health`

### 1. Qué hace

Consulta desde el servidor el endpoint de salud de autenticación y devuelve su estado y cuerpo.

### 2. Autenticación

Requiere `Authorization: Bearer <token>` según la autenticación común.

### 3. Request

| Campo/parámetro | Tipo | Obligatorio | Descripción |
|---|---|---:|---|
| `Authorization` (header) | string | Sí | Token aceptado por la autenticación común. |
| Query/body | — | No | Este endpoint no declara parámetros de query ni cuerpo. |

La URL de destino no la envía el cliente: se obtiene de `AUTH_HEALTH_URL`; si no está configurada, el servidor usa `http://localhost:8080/q/health`.

Ejemplo HTTP:

```http
GET /api/backend-health HTTP/1.1
Host: localhost:8000
Authorization: Bearer <TOKEN_VALIDO>
```

### 4. Response exitosa

**Estado:** `200 OK` cuando la ruta devuelve su respuesta, incluso si la consulta downstream falla.

| Campo | Tipo | Descripción |
|---|---|---|
| `requestedBy` | string | Usuario del token. |
| `status` | integer | Código HTTP recibido del servicio de salud; `0` si ocurre una excepción manejada. |
| `body` | string | Cuerpo recibido como UTF-8 o mensaje genérico si ocurre una excepción manejada. |

Ejemplo cuando el servicio de salud responde `200`:

```json
{
  "requestedBy": "student",
  "status": 200,
  "body": "{\"status\":\"UP\"}"
}
```

### 5. Respuestas de error

| Estado | Cuándo ocurre | Ejemplo de cuerpo |
|---|---|---|
| `401 Unauthorized` | Header ausente o token inválido/expirado. | `{"detail":"Invalid token"}` |
| `200 OK` con fallo downstream | La consulta lanza `urllib3.exceptions.HTTPError`, `OSError` o `UnicodeDecodeError`; la ruta registra el detalle en el servidor y devuelve estado `0` en el cuerpo. | `{"requestedBy":"student","status":0,"body":"Backend health check failed"}` |
| `500 Internal Server Error` | Una excepción no incluida en las capturadas llega al middleware del servidor. | `Internal Server Error` (texto genérico del servidor). |

Un código HTTP `4xx` o `5xx` recibido del servicio downstream se incluye en el campo `status`; la respuesta de esta API sigue siendo `200 OK`.

### 6. Notas de seguridad

La URL downstream se configura del lado del servidor, no mediante un parámetro del cliente. El timeout observado es de 3 segundos. Los errores manejados no exponen el detalle interno al cliente y se registran en el servidor. La identidad del solicitante sigue dependiendo del token Base64 legacy (H-API-01 pendiente). Fuente: `api/app/main.py:76-79`, `api/app/service.py:140-161`, `api/app/security.py:17-29`.

## Preguntas abiertas

1. ¿Qué emisor, algoritmo, claims, emisor (`iss`), audiencia (`aud`) y mecanismo de claves conformarán el contrato JWT? Hasta resolverlo no hay un ejemplo de `Authorization` ejecutable para integración y H-API-01/H-API-02 siguen pendientes.
2. ¿Cómo se aislarán los nombres de archivos para que una carga no sobrescriba la de otro owner? H-API-04 sigue pendiente.
3. ¿El despliegue configura un manejador global que cambie el cuerpo de los errores internos `500`? El código de la aplicación no fija un esquema para excepciones no manejadas.
