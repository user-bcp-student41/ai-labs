# Pruebas del flujo web

## Alcance

Se caracteriza el flujo observado de login y consulta de tareas descrito en [ENDPOINTS.md](ENDPOINTS.md). Las pruebas usan Vitest con Axios, `localStorage` y navegación simulados; no llaman a los servicios reales ni validan sus contratos en vivo. Se usan únicamente los datos ficticios `student`, `Workshop123!` y `test-token`.

El componente es `web`. Esta evidencia se relaciona con H-WEB-06. No se modifica código de producción en esta tarea.

## Casos

| flujo | caso | tipo | resultado esperado |
|---|---|---|---|
| Login y tareas | Login correcto, persistencia de sesión y carga de tareas | Camino feliz | Se guarda el token; se navega al dashboard; `GET /api/tasks` lleva el token como Bearer y la tarea activa se muestra. ([prueba](../web/src/app/auth-flow.spec.ts)) |
| Login | Username vacío | Borde | Se muestra la validación y no se envía una petición. ([prueba](../web/src/app/login/login.component.spec.ts)) |
| Login | Password vacío | Borde | Se muestra la validación y no se envía una petición. ([prueba](../web/src/app/login/login.component.spec.ts)) |
| Login | Respuesta sin token | Borde | Se informa que el backend respondió sin token y no se navega al dashboard. ([prueba](../web/src/app/login/login.component.spec.ts)) |
| Tareas | No hay token de sesión | Borde | Se redirige a `/login` y no se consulta `/api/tasks`. ([prueba](../web/src/app/dashboard/dashboard.component.spec.ts)) |
| Login | Servicio de autenticación no disponible (`Network Error`) | Error | Se muestra `No se pudo autenticar a student.` seguido del mensaje de red y se restablece `busy`. ([prueba](../web/src/app/login/login.component.spec.ts)) |
| Login | Tiempo de espera de 5000 ms agotado | Error | Se muestra el mensaje de timeout de Axios y se restablece `busy`; el login configura `timeout: 5000`. ([prueba](../web/src/app/login/login.component.spec.ts), [configuración probada](../web/src/app/services/auth.service.spec.ts)) |
| Tareas | Token rechazado con HTTP 401 | Error | Se muestra el `detail` del backend, se detiene la carga y se conserva la sesión; no se redirige automáticamente. ([prueba](../web/src/app/dashboard/dashboard.component.spec.ts)) |
| Tareas | Axios rechaza por timeout del adaptador | Error | Se muestra el mensaje recibido, se detiene la carga y se conserva la sesión. El cliente de tareas no configura timeout propio. ([prueba](../web/src/app/dashboard/dashboard.component.spec.ts)) |

## Código de pruebas

Este extracto de aserciones del caso feliz comprueba que el token guardado tras login se usa en la petición de tareas:

```ts
expect(storage.get('workshop_token')).toBe('test-token');
expect(axios.get).toHaveBeenCalledWith('http://localhost:8000/api/tasks?owner=student', {
  headers: { Authorization: 'Bearer test-token' }
});
expect(dashboard.visibleTasks.map((task) => task.title)).toEqual(['Local task']);
```

Estos extractos de las pruebas de timeout de login y token rechazado simulan el rechazo en el límite HTTP:

```ts
vi.mocked(axios.post).mockRejectedValue(new Error('timeout of 5000ms exceeded'));
await component.login();
expect(normalizedMessage(component.message))
  .toBe('No se pudo autenticar a student.\ntimeout of 5000ms exceeded');
expect(component.busy).toBe(false);

vi.mocked(axios.get).mockRejectedValue({
  response: { status: 401, data: { detail: 'Token inválido' } }
});
await component.ngOnInit();
expect(component.error).toBe('Token inválido');
expect(storage.get('workshop_token')).toBe('invalid-token');
expect(router.navigate).not.toHaveBeenCalled();
expect(component.loading).toBe(false);
```

Los fragmentos corresponden a [auth-flow.spec.ts](../web/src/app/auth-flow.spec.ts), [login.component.spec.ts](../web/src/app/login/login.component.spec.ts) y [dashboard.component.spec.ts](../web/src/app/dashboard/dashboard.component.spec.ts). El resto de casos está en esos archivos y en [auth.service.spec.ts](../web/src/app/services/auth.service.spec.ts).

## Ejecución y resultados

Comandos ejecutados en PowerShell desde `web/` (el directorio real fue `C:\Users\Usuario\Documents\T36439-jose-damian\ai-labs\web`):

| comando | código de salida | resultado |
|---|---:|---|
| `npm test` | 0 | 7 archivos aprobados; 31 pruebas aprobadas. |
| `npm run test:coverage` | 0 | 7 archivos aprobados; 31 pruebas aprobadas; cobertura generada con V8. |

### Cobertura

La medida es cobertura de líneas generada por Vitest con `@vitest/coverage-v8`; el resumen proviene de `web/coverage/coverage-summary.json`.

| alcance | líneas cubiertas / líneas totales | cobertura |
|---|---:|---:|
| Módulos ejecutables del flujo login/tareas (`login`, `dashboard`, servicios, utilidades y entorno) | 215 / 215 | 100% |
| Aplicación web completa, incluido bootstrap y rutas | 215 / 243 | 88.47% |

El alcance del flujo supera la meta de 85%. La cifra global se informa por separado e incluye líneas no ejecutadas de `main.ts`, `app.component.ts` y `app.routes.ts`. Para contexto adicional, la cobertura global reportó 92.1% de ramas; `dashboard.component.ts` reportó 80% de ramas aunque sus líneas están cubiertas al 100%.

## Fallos, pendientes y propuestas

**Fallos de esta ejecución:** ninguno. Ambos comandos terminaron con código 0.

**Pendiente:** no se ejecutó una integración contra los servicios reales ni una prueba de navegador. Las respuestas, el error 401 y los errores de timeout se inyectan mediante mocks; por tanto, estos casos prueban el manejo del frontend, no la disponibilidad, autenticación o tiempos de respuesta de los servicios. El endpoint de tareas no establece timeout en su configuración actual.

**Propuesto, no ejecutado:** añadir una prueba de integración con los servicios levantados cuando el contrato del backend esté disponible y acordado; revisar cobertura de bootstrap/rutas si se amplía el alcance de esta entrega.

## Documentos consultados

- [AGENTS.md](../AGENTS.md)
- [README.md](../README.md)
- [RETO.md](../RETO.md)
- [GOOD_PRACTICES.md](GOOD_PRACTICES.md)
- [HALLAZGOS.md](../HALLAZGOS.md)
- [PLAN.md](../PLAN.md)
- [ENDPOINTS.md](ENDPOINTS.md)