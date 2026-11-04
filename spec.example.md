# Validar inicialización del terminal antes de un retiro

## Porque

Se solicita evitar que se realice una operación de retiro de dinero desde un terminal de agente corresponsal que todavía no haya sido inicializado.

La fuente de esta especificación es el requerimiento proporcionado; no se adjuntó un issue ni evidencia adicional.

## Que cambia

Antes de procesar un retiro, el sistema deberá comprobar que el terminal desde el que se solicita la operación esté inicializado. Si no lo está, el retiro no deberá ejecutarse.

## Alcance

- Validar el estado de inicialización del terminal al solicitar un retiro.
- Permitir que el retiro continúe cuando el terminal esté inicializado.
- Impedir que el retiro continúe cuando el terminal no esté inicializado.

## Como se sabra que esta hecho

La validación estará implementada y probada para los casos de terminal inicializado y no inicializado. Las pruebas demostrarán que solo el primer caso puede continuar con el flujo de retiro.

## Specs (criterios verificables)

1. **Terminal inicializado:** dado un terminal inicializado, cuando se solicita un retiro, el sistema permite que la operación continúe por el flujo existente.
2. **Terminal no inicializado:** dado un terminal no inicializado, cuando se solicita un retiro, el sistema rechaza la operación y no ejecuta el retiro.
3. **Sin regresiones:** las operaciones distintas al retiro mantienen su comportamiento actual.
4. **Pruebas:** existen pruebas automatizadas para los escenarios anteriores.

## Decisiones de diseño

- Esta especificación no prescribe cómo se representa ni cómo se consulta el estado de inicialización.
- Está pendiente definir la respuesta que recibirá el usuario cuando el retiro sea rechazado, respetando el contrato existente del sistema.
- Está pendiente precisar qué debe ocurrir si no es posible determinar el estado del terminal.

## Lista de tareas

1. Identificar el flujo actual de retiro y el contrato que debe preservar.
2. Confirmar cómo se define y consulta que un terminal está inicializado.
3. Acordar la respuesta para un terminal no inicializado y para un estado que no se pueda determinar.
4. Agregar pruebas para terminal inicializado, no inicializado y los casos acordados.
5. Implementar la validación y verificar que el flujo existente de retiro se preserve.
