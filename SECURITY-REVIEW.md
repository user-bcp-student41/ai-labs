# Revisión local de seguridad — API

**Fecha:** 2026-11-02<br>
**Base de comparación:** `main`<br>
**Rama local:** `day1/prompting`
**Alcance:** cambios de `api/` y secciones API de los documentos permitidos. No se revisó código de otros componentes.

## Hallazgos

| Severidad | Hallazgo | Evidencia | Estado |
|---|---|---|---|
| CRÍTICA | **H-API-01 — Token Base64 sin firma permite falsificar la identidad.** El secreto embebido y la decodificación Base64 no verifican firma, emisor ni audiencia. Las rutas usan esta identidad, por lo que owner-checks no son una barrera fiable mientras siga este formato. | `api/app/security.py:9,17-29`; dependencias en `api/app/main.py:49-50,57,64,71,77` | Pendiente por decisión del usuario de coordinar primero el contrato JWT con el emisor externo. |
| ALTA | **H-API-02 — La autorización por owner depende de una identidad falsificable.** Los controles comparan `owner` con la identidad obtenida del token legacy; por tanto, un token falsificado puede suplantar otro usuario y eludir el control. | `api/app/service.py:35-91`; `api/app/security.py:9,17-29` | Pendiente; volver a verificar después de resolver H-API-01. |
| ALTA | **H-API-04 — Colisión de nombres permite sobrescribir cargas.** Los archivos se guardan en un directorio compartido usando el nombre proporcionado; `write_bytes` reemplaza un destino existente. | `api/app/main.py:23-27,69-74`; `api/app/service.py:99-112` | Pendiente; aislar por owner o usar nombres de destino no colisionables y agregar prueba. |

## Verificación de otros hallazgos resueltos

- **H-API-03:** los valores SQL se pasan como parámetros; las interpolaciones usan únicamente la constante de columnas (`api/app/repository.py:61-95`).
- **H-API-05:** las versiones fijadas cumplen las correcciones referidas por los advisories consultados. Esto no equivale a un escaneo integral de todas las dependencias transitivas.
- **H-API-06 y H-API-07:** se observan capas separadas, modelos Pydantic, excepciones más específicas y respuestas genéricas. No se encontró otra observación de seguridad en estos cambios.

## Pruebas y limitaciones

El revisor no volvió a ejecutar las pruebas. `PLAN.md` registra la ejecución previa: 18 pruebas aprobadas y 96% de cobertura total. Las pruebas existentes no cubren la falsificación de identidad ni la colisión de nombres entre owners.

El escáner `appmod-cve-assessment` disponible no admite el ecosistema PyPI. Los advisories de H-API-05 se contrastaron directamente; no se afirma un escaneo automático completo.

## Documentos y fuentes consultados

- `HALLAZGOS.md`
- `PLAN.md`
- `docs/GOOD_PRACTICES.md`
- `prompts/api-prompt-d01.md`
- `prompts/api-prompt-d01-02.md`
- `prompts/api-prompt-d01-03.md`
- `prompts/api-prompt-d01-04.md`
- GitHub Security Advisories: [GHSA-gm62-xv2j-4w53](https://github.com/advisories/GHSA-gm62-xv2j-4w53), [GHSA-2xpw-w6gg-jr37](https://github.com/advisories/GHSA-2xpw-w6gg-jr37), [GHSA-mj87-hwqh-73pj](https://github.com/advisories/GHSA-mj87-hwqh-73pj), [GHSA-pp6c-gr5w-3c5g](https://github.com/advisories/GHSA-pp6c-gr5w-3c5g).
