# Contratos externos — web

Este documento describe el **contrato observado en el cliente web**. No hay un contrato backend acordado/documentado en el workspace; los códigos de éxito específicos y los esquemas runtime quedan como preguntas abiertas. Los tipos TypeScript ayudan al compilador, pero no validan la respuesta recibida.

## Login — `POST /auth/login`

### 1. Quién lo llama

`LoginComponent.login()` valida los campos y llama a `AuthService.login()`. El servicio envía la solicitud y guarda la sesión cuando recibe un token. Referencias: [web/src/app/login/login.component.ts:27](web/src/app/login/login.component.ts#L27), [web/src/app/login/login.component.ts:40](web/src/app/login/login.component.ts#L40), [web/src/app/services/auth.service.ts:24](web/src/app/services/auth.service.ts#L24).

### 2. Qué envía

URL configurada en [web/src/environments/environment.ts:2](web/src/environments/environment.ts#L2). Axios envía un `POST` con un objeto JSON; el cliente no configura headers propios en esta llamada. Antes de llamar, la UI rechaza username o password vacíos tras `trim()`, pero envía los valores originales sin recortarlos ([web/src/app/login/login.component.ts:29](web/src/app/login/login.component.ts#L29), [web/src/app/login/login.component.ts:33](web/src/app/login/login.component.ts#L33)).

| Parte | Campo | Valor/tipo observado |
|---|---|---|
| Body | `username` | String escrito en el formulario. |
| Body | `password` | String escrito en el formulario. |
| Body | `client` | Valor fijo `angular-workshop`. |
| Header | Headers personalizados | Ninguno configurado por el servicio. Axios serializa el objeto enviado como body JSON. |
| Timeout | Solicitud | 5000 ms, configurado por `AuthService`. |

Ejemplo basado en las credenciales ficticias del README y el cliente fijo del código:

```http
POST http://localhost:8080/auth/login
Content-Type: application/json

{"username":"student","password":"Workshop123!","client":"angular-workshop"}
```

La llamada y sus valores están en [web/src/app/services/auth.service.ts:25](web/src/app/services/auth.service.ts#L25) y [web/src/app/services/auth.service.ts:27](web/src/app/services/auth.service.ts#L27); el README identifica esas credenciales como ficticias ([README.md:44](README.md#L44)).

### 3. Qué espera recibir en éxito

El cliente no comprueba un código concreto: Axios resuelve la promesa para respuestas exitosas 2xx. `LoginResponse` describe el tipo esperado, pero no se aplica validación runtime. La UI solo comprueba que `token` sea truthy; el servicio guarda token, `user` y preferencias, y la UI navega a `/dashboard` ([web/src/app/login/login.component.ts:40](web/src/app/login/login.component.ts#L40), [web/src/app/login/login.component.ts:41](web/src/app/login/login.component.ts#L41), [web/src/app/services/auth.service.ts:31](web/src/app/services/auth.service.ts#L31), [web/src/app/services/auth.service.ts:61](web/src/app/services/auth.service.ts#L61)).

| Campo | Tipo declarado | Uso en el cliente |
|---|---|---|
| `token` | `string`, opcional en `LoginResponse` | Si es truthy, se guarda como `workshop_token`; es el único campo cuya presencia comprueba la UI. |
| `user` | `LoginUser`, requerido en el tipo | Se serializa como `workshop_user`; el cliente no valida su forma en runtime. `username`, `displayName` y `role` son opcionales. |
| `expiresIn` | `number`, opcional | Declarado en el tipo, pero la UI no lo lee ni lo usa. |

Los tipos están en [web/src/app/models.ts:7](web/src/app/models.ts#L7) y [web/src/app/models.ts:13](web/src/app/models.ts#L13). Ejemplo ilustrativo con datos ficticios del test (no es un token real):

```json
{
  "token": "test-token",
  "user": { "username": "student" }
}
```

### 4. Errores y reacción de la UI

| Situación | Reacción observada |
|---|---|
| Username vacío | No envía solicitud; muestra `Ingrese un usuario.` |
| Password vacío | No envía solicitud; muestra `Ingrese una contraseña.` |
| HTTP no exitoso, fallo de red o timeout de 5000 ms | Axios rechaza; la UI muestra `No se pudo autenticar a <username>.` y, en otra línea, primero `response.data.message`, luego el mensaje de la excepción y finalmente `Error desconocido`. También escribe el error en consola y restablece `busy`. No hay reintento automático. |
| Respuesta 2xx sin `token` truthy | Muestra `El backend respondió sin token.`; `AuthService` no persiste sesión y la UI no navega. |
| Respuesta con forma inesperada | No hay validación de esquema. Un error al leer `response.data` cae en el mismo `catch`; si hay token pero `user` falta o tiene una forma distinta, el servicio aun así intenta persistirlo. |
| Token inválido | No aplica como token de entrada: login no envía un bearer token. Si las credenciales son rechazadas por HTTP, se aplica la ruta de error HTTP anterior. |

La selección de mensajes está en [web/src/app/utils/api-error.ts:10](web/src/app/utils/api-error.ts#L10) y la UI en [web/src/app/login/login.component.ts:46](web/src/app/login/login.component.ts#L46). El timeout está configurado en [web/src/app/services/auth.service.ts:20](web/src/app/services/auth.service.ts#L20).

### 5. Seguridad y sesión

Los mensajes se muestran con interpolación Angular (`{{ message }}`), no con `[innerHTML]` ([web/src/app/login/login.component.html:39](web/src/app/login/login.component.html#L39)); los saltos de línea se conservan mediante CSS. `AuthService` centraliza almacenamiento, lectura y eliminación de sesión, pero el token permanece en `localStorage` bajo `workshop_token`, accesible a JavaScript del mismo origen ([web/src/app/services/auth.service.ts:7](web/src/app/services/auth.service.ts#L7), [web/src/app/services/auth.service.ts:48](web/src/app/services/auth.service.ts#L48)). Este riesgo sigue registrado como H-WEB-01 pendiente en [HALLAZGOS.md:15](../HALLAZGOS.md#L15). No se mueve ningún secreto al frontend; la contraseña se envía al endpoint de autenticación indicado.

## Tareas — `GET /api/tasks`

### 1. Quién lo llama

`DashboardComponent.ngOnInit()` lee la sesión mediante `AuthService` y, si hay token, llama a `TasksService.getTasks(owner, token)`. Referencias: [web/src/app/dashboard/dashboard.component.ts:44](web/src/app/dashboard/dashboard.component.ts#L44), [web/src/app/dashboard/dashboard.component.ts:53](web/src/app/dashboard/dashboard.component.ts#L53), [web/src/app/services/tasks.service.ts:8](web/src/app/services/tasks.service.ts#L8).

### 2. Qué envía

La base URL está en [web/src/environments/environment.ts:3](web/src/environments/environment.ts#L3). El servicio concatena directamente el username en el query; no codifica el valor y no envía body.

| Parte | Campo | Valor/tipo observado |
|---|---|---|
| Query | `owner` | `user.username` de `workshop_user`; usa string vacío si falta. Se concatena directamente en la URL. |
| Header | `Authorization` | `Bearer <token>` leído de `workshop_token`. |
| Body | — | No hay body en el `GET`. |
| Timeout | Solicitud | No se configura timeout en esta llamada. |

Ejemplo sintético usado por las pruebas:

```http
GET http://localhost:8000/api/tasks?owner=student
Authorization: Bearer test-token
```

La construcción se ve en [web/src/app/services/tasks.service.ts:8](web/src/app/services/tasks.service.ts#L8) y [web/src/app/services/tasks.service.ts:9](web/src/app/services/tasks.service.ts#L9); la prueba usa `student` y `test-token` ([web/src/app/dashboard/dashboard.component.spec.ts:64](web/src/app/dashboard/dashboard.component.spec.ts#L64)).

### 3. Qué espera recibir en éxito

El cliente no comprueba un código HTTP concreto: cualquier respuesta que Axios resuelva se procesa como una lista `Task[]`. Este tipo es una anotación de compilación, no validación runtime. Los campos del tipo son opcionales: `id` (`number|string`), `status`, `priority`, `owner`, `label`, `title` y `description` (`string`). `label` lo calcula el cliente para las tareas visibles; no hace falta que venga del servidor ([web/src/app/models.ts:19](web/src/app/models.ts#L19), [web/src/app/models.ts:24](web/src/app/models.ts#L24), [web/src/app/dashboard/dashboard.component.ts:56](web/src/app/dashboard/dashboard.component.ts#L56)).

| Campo | Tipo declarado | Uso en el cliente |
|---|---|---|
| `id` | `number|string`, opcional | No se usa en la lógica revisada; puede usarse como dato de tarea. |
| `status` | `string`, opcional | Filtra el valor exacto `ARCHIVED`; se transforma a etiqueta visible si coincide con un estado conocido. |
| `priority` | `string`, opcional | Participa en el orden descendente lexicográfico del comparador actual. |
| `owner` | `string`, opcional | Se usa al formar la etiqueta. |
| `title`, `description` | `string`, opcionales | Se muestran en la tarjeta de tarea. |
| `label` | `string`, opcional | El dashboard lo agrega a cada tarea visible como `PRIORITY · OWNER` en mayúsculas, con defaults si faltan valores. |

Ejemplo sintético basado en fixtures de prueba (no datos obtenidos del backend):

```json
[
  { "id": 1, "status": "TODO", "priority": "LOW", "owner": "student" },
  { "id": 2, "status": "ARCHIVED", "priority": "HIGH", "owner": "student" }
]
```

Tras recibir la lista, el cliente la conserva en `tasks`, excluye de `visibleTasks` los estados exactamente iguales a `ARCHIVED`, agrega `label` a las tareas visibles y aplica el comparador actual ([web/src/app/dashboard/dashboard.component.ts:53](web/src/app/dashboard/dashboard.component.ts#L53), [web/src/app/dashboard/dashboard.component.ts:56](web/src/app/dashboard/dashboard.component.ts#L56), [web/src/app/dashboard/dashboard.component.ts:62](web/src/app/dashboard/dashboard.component.ts#L62)).

### 4. Errores y reacción de la UI

| Situación | Reacción observada |
|---|---|
| No hay token | No llama al endpoint; navega a `/login`. |
| Token rechazado, incluido HTTP 401/403 | Axios rechaza. Si `response.data.detail` es un string no vacío, se muestra; si no, se usa el mensaje de error y luego `No se pudo cargar el dashboard`. No se borra el token ni se redirige automáticamente. El error se muestra en el dashboard, se apaga `loading` y se oculta la grilla de tareas. |
| Fallo de red o eventual timeout del adaptador | No hay timeout configurado por la aplicación. Si Axios rechaza por fallo de red, cancelación o timeout externo, se usa la misma selección de mensaje que para el error HTTP. No hay reintento. |
| Respuesta exitosa con `data` inesperado (por ejemplo, no iterable) | No se valida el esquema. Al recorrer el valor, la excepción cae en el `catch` y se muestra el mensaje de error/fallback anterior. Elementos nulos o con formas inesperadas también pueden provocar una excepción. |
| Username ausente en la sesión | Se envía `owner=`. |
| JSON de usuario local malformado | `AuthService.getUser()` hace `JSON.parse`; la llamada ocurre antes del `try` de carga del dashboard. La inicialización puede rechazarse sin actualizar `error` ni `loading`; no hay recuperación específica en este flujo. |

El manejo está en [web/src/app/dashboard/dashboard.component.ts:45](web/src/app/dashboard/dashboard.component.ts#L45), [web/src/app/dashboard/dashboard.component.ts:48](web/src/app/dashboard/dashboard.component.ts#L48), [web/src/app/dashboard/dashboard.component.ts:53](web/src/app/dashboard/dashboard.component.ts#L53), [web/src/app/dashboard/dashboard.component.ts:74](web/src/app/dashboard/dashboard.component.ts#L74) y [web/src/app/services/auth.service.ts:52](web/src/app/services/auth.service.ts#L52). La función que selecciona el texto de error está en [web/src/app/utils/api-error.ts:10](web/src/app/utils/api-error.ts#L10); la plantilla muestra el error mediante interpolación en [web/src/app/dashboard/dashboard.component.html:18](web/src/app/dashboard/dashboard.component.html#L18).

### 5. Seguridad y sesión

El bearer token se lee de `localStorage` mediante `AuthService` y se envía en el header `Authorization`; no se usa una cookie `HttpOnly` ([web/src/app/services/auth.service.ts:48](web/src/app/services/auth.service.ts#L48), [web/src/app/services/tasks.service.ts:9](web/src/app/services/tasks.service.ts#L9)). El valor `owner` proviene de datos locales del cliente y se incluye en el query; la autorización real no puede confirmarse desde el código web. El token en `localStorage` sigue siendo el riesgo pendiente H-WEB-01 ([HALLAZGOS.md:15](../HALLAZGOS.md#L15)). Tanto `owner` como los datos de tarea se tratan como valores no validados por runtime.

## Preguntas abiertas

- ¿Qué código de éxito y esquema JSON exige cada backend? El cliente solo requiere que Axios resuelva y no comprueba status o schema en runtime.
- ¿Qué campos de `user` y de cada tarea son obligatorios en el contrato de servidor? Los modelos web son tipos estáticos con varios campos opcionales.
- ¿Qué debe hacer la UI ante 401/403 de tareas: conservar el token y mostrar error, limpiar sesión o volver a login? El comportamiento observado conserva la sesión y presenta el error.
- ¿Debe `owner` codificarse como parámetro URL y cómo se configura un timeout de tareas? Actualmente se concatena sin codificar y no hay timeout explícito.
