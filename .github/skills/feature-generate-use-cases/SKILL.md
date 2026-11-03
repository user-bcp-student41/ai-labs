---
name: feature-generate-use-cases
description: Genera un test plan a partir de la historia de usuario proporcionada.
---

# Skill: Feature Generate Use Cases

## 1) Metadata
- **Skill ID:** feature-generate-use-cases
- **Version:** 0.1.0
- **Purpose:** Generar un test plan a partir de la historia de usuario proporcionada.
- **Audience (roles):** Chapter/PO, Tech Lead, Backend, Frontend, QA
- **When to use:** Cuando la historia de usuario está disponible y se requiere un test plan.
- **When NOT to use:** Cuando la historia de usuario no tiene los criterios de aceptación definidos y no se haya marcado como lista para pruebas.
- **Sensitive inputs:** No incluyas datos reales de clientes, credenciales, secretos, tokens ni URLs internas no autorizadas.
- **Expected output:** Markdown estructurado con las secciones de Output definidas más abajo.

## 2) Inputs
Proporciona la información en este formato:

- **Business context (brief):**
- **Feature request / user story:**
- **Expected impact (metric or outcome):**
- **Scope (in/out):**
- **Known technical constraints:** (performance, security)
- **Team Definition of Done (DoD):** (if available)

## 3) Output
Devuelve **solo** un documento Markdown con estas secciones y bullets:

1. **Summary**
2. **Scope**
    - Dentro del alcance
    - Fuera del alcance
3. **Supuestos**
4. **Decisiones técnicas por tomar (pendientes o resueltas)**
5. **Riesgos y mitigaciones**
6. **Técnicas de prueba**
    - Unitarias
    - Funcionales
    - Seguridad (comprobaciones mínimas)
    - Contables
    - Performance
7. **Tareas sugeridas por rol**
    - QA
8. **Preguntas abiertas**

## 4) Constraints
- No inventes requisitos: si falta información, inclúyela bajo **Preguntas abiertas**.
- No incluyas datos sensibles ni secretos.
- Considera las técnicas ISTQB para la definición de pruebas.
- Mantén la salida en un máximo de 1-2 páginas para que siga siendo usable.

## 5) Validation Rules
La salida es válida si:
- Incluye todas las secciones definidas en Output.
- Incluye al menos 2 riesgos con mitigaciones.
- No contiene datos sensibles ni secretos.
- No contiene supuestos no declarados.

## 6) Evidence
Adjunta o referencia estos elementos en el PR o entrega:
- `SKILL.md` versionado.
- `examples/input.sample.md`.
- `examples/output.sample.md`.
- Tag de versión para el Skill, como `skill-feature-generate-use-cases-v0.1.0`.