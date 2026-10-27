# PLAN

## Aprobación
Nombre: José Damián
Fecha: 26/10/2026
Hallazgos: H-WEB-02, H-WEB-03, H-WEB-04 y H-WEB-06

## Registro previo — bloqueo antes de aprobación

- **Componente/IDs:** web — H-WEB-02, H-WEB-03, H-WEB-04 y H-WEB-06.
- **Estado en ese momento:** bloqueado porque aún no estaba registrada la aprobación; no se editaron archivos de código ni pruebas.
- **Actualización:** la aprobación humana quedó registrada arriba con nombre, fecha e IDs; la implementación se inició después de añadir y ejecutar la caracterización.

## Ejecución de caracterización — 2026-10-26

- **Componente/IDs:** web — H-WEB-02, H-WEB-03, H-WEB-04 y H-WEB-06.
- **Comando/cwd:** `npm test`, `web/`.
- **Intento inicial:** 1 archivo pasó (3 pruebas); 2 archivos no cargaron por falta de compilador Angular JIT en el entorno de Vitest. Se añadió el import del compilador solo en las specs.
- **Segundo intento:** 11/12 pruebas pasaron; una expectativa de orden asumía prioridad semántica y falló. La observación confirmó el orden actual `LOW` antes que `HIGH`; se corrigió la expectativa de caracterización, no el código de producción.
- **Resultado de línea base:** 3 archivos y 12/12 pruebas pasaron antes de modificar componentes o servicios.
- **Corrección H-WEB-02:** `npm test -- src/app/login/login.component.spec.ts`, `web/`: 1 archivo y 5/5 pruebas pasaron después de cambiar los mensajes a texto e interpolación.

## Implementación y regresión — 2026-10-26

- **Componente/IDs:** web — H-WEB-02, H-WEB-03, H-WEB-04 y H-WEB-06.
- **`npm test`, `web/`, tras extraer servicios:** 9 pruebas fallaron porque las caracterizaciones todavía construían los componentes con sus constructores anteriores. Se actualizaron los fixtures para inyectar los servicios reales; no se cambió el comportamiento esperado.
- **`npm test`, `web/`, tras adaptar fixtures:** 3 archivos, 12/12 pruebas pasaron.
- **`npm test`, `web/`, con pruebas de servicios/utilidad:** 6 archivos, 24/24 pruebas pasaron.
- **`npm run build`, `web/`:** build Angular de producción completado. Angular mostró advertencias CommonJS para Axios y `lodash/merge`; no se agregaron dependencias ni se ocultaron advertencias.
- **Primer `npm run test:coverage`, `web/`:** 24/24 pruebas; 213/243 líneas globales cubiertas (87.65%). El dashboard tenía 69/71 líneas cubiertas; se agregaron pruebas de etiquetas de estado.
- **`npm run test:coverage` final, `web/`:** 6 archivos, 26/26 pruebas; 215/243 líneas globales (88.47%), 18/20 funciones (90%) y 67/73 ramas (91.78%). En los módulos ejecutables modificados: 215/215 líneas (100%); 65/69 ramas (94.20%). Método: Vitest 3.2.4 con V8; resumen `web/coverage/coverage-summary.json`, HTML `web/coverage/index.html`. Los 28 renglones no cubiertos pertenecen a `main.ts`, `app.component.ts` y `app.routes.ts`, no modificados aquí.
- **Verificación visual:** `npm start` desde la raíz falló por falta de `package.json`; corregido el directorio a `web/`, Angular encontró 4200 ocupado. Se rechazó el puerto alternativo, por lo que no se realizó comprobación en navegador.
- **Integración:** endpoints, payloads, encabezados, persistencia, filtrado/orden de tareas y logout se caracterizaron con Axios, router y almacenamiento simulados. No se verificó contra servicios auth/api reales, fuera del ámbito.
- **Dependencias:** no se ejecutó `npm audit`; H-WEB-05 permanece pendiente. H-WEB-01 también permanece pendiente; el token sigue en `localStorage` y no se movieron secretos al frontend.

## Alcance y selección

El marcador de IDs del pedido no especifica una lista. De los hallazgos web que siguen en estado `Pendiente` en `HALLAZGOS.md`, se seleccionan:

- **H-WEB-02**: el mensaje dinámico se renderiza como HTML; se puede reducir esa superficie dentro de `web/` conservando el texto visible.
- **H-WEB-03**: HTTP, sesión y navegación están mezclados; separar esos roles es una mejora transversal del flujo y está prevista por `docs/GOOD_PRACTICES.md`.
- **H-WEB-04**: los tipos `any` y las validaciones anidadas están evidenciados; se pueden abordar con tipos explícitos y retornos anticipados, sin cambiar el contrato.
- **H-WEB-06**: la suite encontrada cubre una utilidad; las pruebas de flujo darán una base para los cambios anteriores.

Se difieren **H-WEB-01**, porque reemplazar `localStorage` por una cookie `HttpOnly` requeriría coordinar el contrato con `auth/`, fuera de este alcance; y **H-WEB-05**, porque las versiones están confirmadas pero no hay resultado de SCA ni CVE confirmado. No se descartan ni se cambia su estado en `HALLAZGOS.md`.

No existe `docs/ENDPOINTS.md`. Se preserva el comportamiento observado en `HALLAZGOS.md`; la aprobación humana de los IDs seleccionados está registrada al inicio de este plan.

## Contrato y comportamiento a preservar

- Login: `POST http://localhost:8080/auth/login`, mismo JSON (`username`, `password`, `client`), lectura de `response.data.token` y `response.data.user`, claves `workshop_token`, `workshop_user` y `workshop_preferences`, y navegación a `/dashboard`.
- Tareas: `GET http://localhost:8000/api/tasks?owner=<username>` con `Authorization: Bearer <token>`. Se conserva la forma de respuesta observada, el filtrado de `ARCHIVED`, las etiquetas y el orden actuales.
- Sin token, el dashboard navega a `/login`. Logout elimina token y usuario del almacenamiento y vuelve a `/login`; preferencias permanecen como hoy.
- Los cambios de presentación conservarán los mensajes legibles actuales. No se cambian endpoints, payloads, encabezados ni respuestas esperadas, y no se agrega una dependencia.

## H-WEB-02 — Mensaje dinámico con `[innerHTML]`

**Hallazgo:** H-WEB-02, Vulnerabilidad, severidad media, estado `Pendiente` en `HALLAZGOS.md`. La plantilla interpreta como HTML un mensaje que incluye valores dinámicos ([web/src/app/login/login.component.html:39](web/src/app/login/login.component.html#L39), [web/src/app/login/login.component.ts:56](web/src/app/login/login.component.ts#L56)). Angular sanitiza `innerHTML` por defecto; no se da por demostrada ejecución de HTML arbitrario.

**Problema:** concatenar contenido dinámico con marcado y enlazarlo como HTML aumenta la superficie de interpretación y dificulta distinguir texto de formato.

**Cambio propuesto:** mantener `message` como texto plano, sustituir `[innerHTML]` por interpolación Angular y expresar la separación visual de líneas con CSS (`white-space: pre-line`) si se necesita. No usar `DomSanitizer` ni cambiar el contenido legible de los mensajes.

**Archivos a tocar:** `web/src/app/login/login.component.ts`, `web/src/app/login/login.component.html`, `web/src/app/login/login.component.css`; nueva prueba `web/src/app/login/login.component.spec.ts`.

**Caracterización antes de tocar esos archivos:** añadir pruebas Vitest con Axios y Router simulados para validar los mensajes de usuario/contraseña vacíos y error del backend, y comprobar que el flujo de login exitoso sigue guardando los datos y navegando. Antes de cambiar la plantilla, verificar localmente en navegador el texto visible de esos estados; `vitest.config.ts` usa entorno `node`, por lo que la prueba unitaria no demuestra por sí sola el render del DOM.

## H-WEB-03 — Responsabilidades mezcladas en los componentes

**Hallazgo:** H-WEB-03, Refactor, severidad baja, estado `Pendiente` en `HALLAZGOS.md`. Login y dashboard conocen URLs y hacen HTTP, manejan almacenamiento y navegan ([web/src/app/login/login.component.ts:41](web/src/app/login/login.component.ts#L41), [web/src/app/dashboard/dashboard.component.ts:36](web/src/app/dashboard/dashboard.component.ts#L36), [web/src/app/dashboard/dashboard.component.ts:43](web/src/app/dashboard/dashboard.component.ts#L43), [web/src/app/dashboard/dashboard.component.ts:74](web/src/app/dashboard/dashboard.component.ts#L74)).

**Problema:** la integración y la sesión están acopladas a la vista, lo que hace más difícil probarlas y cambiar una responsabilidad sin afectar las demás.

**Cambio propuesto:** extraer las operaciones de login y sesión a `AuthService`, y la consulta de tareas a `TasksService`. Los componentes se limitarán a estado de vista y navegación. Centralizar las URLs en configuración de ambiente, como prescribe `docs/GOOD_PRACTICES.md`; conservar `localStorage` y sus claves durante este cambio para no alterar el comportamiento de persistencia observado. No agregar dependencias.

**Archivos a tocar:** `web/src/app/login/login.component.ts`, `web/src/app/dashboard/dashboard.component.ts`; nuevos `web/src/app/models.ts`, `web/src/app/services/auth.service.ts`, `web/src/app/services/tasks.service.ts` y `web/src/environments/environment.ts`; pruebas `web/src/app/login/login.component.spec.ts`, `web/src/app/dashboard/dashboard.component.spec.ts` y pruebas de los servicios nuevos.

**Caracterización antes de tocar esos archivos:** añadir primero pruebas con HTTP, Router y almacenamiento simulados. Comprobar el método y URL de login, body, claves guardadas y navegación; para tareas, comprobar URL/query, encabezado bearer, ausencia de token, logout y transformaciones visibles. Estas pruebas deben pasar sobre el flujo actual antes de extraer servicios.

## H-WEB-04 — Tipado `any` y condicionales anidados

**Hallazgo:** H-WEB-04, Refactor, severidad baja, estado `Pendiente` en `HALLAZGOS.md`. Hay `any` en login, dashboard y formato de tareas, además de validaciones anidadas ([web/src/app/login/login.component.ts:16](web/src/app/login/login.component.ts#L16), [web/src/app/login/login.component.ts:33](web/src/app/login/login.component.ts#L33), [web/src/app/login/login.component.ts:36](web/src/app/login/login.component.ts#L36), [web/src/app/dashboard/dashboard.component.ts:23](web/src/app/dashboard/dashboard.component.ts#L23), [web/src/app/utils/legacy-format.ts:1](web/src/app/utils/legacy-format.ts#L1)). La duplicación indicada por `RETO.md` no quedó confirmada y no se incluirá como cambio supuesto.

**Problema:** los valores de requests, responses, tareas y errores quedan sin comprobación estática suficiente; la anidación complica seguir los casos de validación.

**Cambio propuesto:** definir interfaces para los requests/responses de login y las tareas; sustituir `any` por esos tipos y `unknown` en límites de error, con narrowing explícito. Convertir las validaciones anidadas a retornos anticipados. Mantener la misma validación, mensajes, orden y filtrado actuales. Evitar duplicar tipos o lógica al extraer los servicios de H-WEB-03.

**Archivos a tocar:** `web/src/app/login/login.component.ts`, `web/src/app/dashboard/dashboard.component.ts`, `web/src/app/utils/legacy-format.ts`, `web/src/app/utils/api-error.ts`; tipos en `web/src/app/models.ts` creados para H-WEB-03; pruebas correspondientes.

**Caracterización antes de tocar esos archivos:** añadir casos para usuario y contraseña vacíos, login válido y error HTTP; tareas vacías y mixtas con tareas archivadas, formatos de prioridad/owner y logout. Mantener los casos existentes de `legacy-format.spec.ts` y ampliar sus casos de valores ausentes antes de ajustar los tipos.

## H-WEB-06 — Pruebas limitadas a una utilidad

**Hallazgo:** H-WEB-06, Sugerencia, severidad baja, estado `Pendiente` en `HALLAZGOS.md`. La spec localizada solo prueba `formatTaskLabel` ([web/src/app/utils/legacy-format.spec.ts:4](web/src/app/utils/legacy-format.spec.ts#L4), [web/src/app/utils/legacy-format.spec.ts:6](web/src/app/utils/legacy-format.spec.ts#L6)).

**Problema:** no hay caracterización automatizada localizada para login, persistencia de sesión, carga de tareas ni cierre de sesión; cambios en esos flujos podrían regresionar sin detección.

**Cambio propuesto:** añadir pruebas Vitest de componente/servicio para los caminos válidos y de error descritos en H-WEB-02 y H-WEB-03. Reusar mocks y casos compartidos, sin agregar un framework o duplicar pruebas. Ejecutar `npm test` y `npm run test:coverage` desde `web/` cuando se implemente; registrar entonces los resultados reales y cobertura, sin inferirlos desde esta propuesta.

**Archivos a tocar:** `web/src/app/login/login.component.spec.ts`, `web/src/app/dashboard/dashboard.component.spec.ts`, nuevas specs de `AuthService`, `TasksService` y `web/src/app/utils/api-error.ts`; `web/src/app/utils/legacy-format.spec.ts` solo para ampliar casos de la utilidad.

**Caracterización antes de tocar componentes o servicios:** escribir y ejecutar primero las pruebas del comportamiento actual: mensajes de login, request/almacenamiento/navegación, dashboard sin token y con tareas, error de carga y logout. Registrar fallos iniciales sin ocultarlos; no se afirma que estas pruebas ya existan ni que se hayan ejecutado.