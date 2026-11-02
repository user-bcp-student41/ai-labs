ÁMBITO
Workspace: ai-labs, abierto en su raiz. Todas las rutas son relativas
a esa raiz. Lee el codigo solo de api/; escribe codigo, configuracion y
pruebas solo en api/. No leas ni modifiques codigo de otros componentes.
Lee README.md, RETO.md y docs/GOOD_PRACTICES.md. Lee
HALLAZGOS.md, PLAN.md y los demas documentos de docs/ solo si existen.
Escribe evidencias solo en HALLAZGOS.md, PLAN.md, prompts/,
docs/ENDPOINTS.md, docs/TESTING.md y docs/GOOD_PRACTICES.md de la raiz.
Cuando este paso pida un artefacto ausente, crealo. Si ya existe, conserva
las filas y secciones de otros componentes. No las sobrescribas.
Cada hallazgo lleva componente api e ID H-API-NN, por ejemplo H-API-01.
Cita codigo como api/ruta:linea. No renumeres IDs existentes.
Ejecuta Git desde ai-labs/; ejecuta pruebas con cwd api/.
Coordina dependencias externas sin ampliar AMBITO. No inventes aprobaciones
humanas ni resultados de pruebas. Si falta evidencia, registra el pendiente.

CONTEXTO
La API es FastAPI. Verifica los endpoints y formatos que deben
preservarse en docs/ENDPOINTS.md, si existe. RETO.md enumera
posibles hallazgos, pero es una lista de pistas, no evidencia:
confirma cada afirmación en el código.y

No presupongas que la API tiene un flujo de login. Distingue entre
un endpoint que recibe credenciales y un mecanismo que valida un
token enviado en Authorization. Comprueba qué autenticación existe
realmente y cómo las rutas la aplican.

OBJETIVO
Determinar si datos controlados por el cliente llegan concatenados
o interpolados directamente en consultas SQL, especialmente en
filtros e inserts. Sigue el flujo desde cada ruta HTTP hasta la
consulta y distingue concatenación, parametrización y casos no
comprobados.

Comprueba también si las consultas por propietario se autorizan
usando la identidad derivada de un token verificado o un owner
enviado por el cliente. No asumas que decodificar Base64 verifica
la autenticidad de un token.

RESTRICCIONES
No edites código ni ejecutes ataques contra servicios remotos.
Usa solo código y datos ficticios locales. No incluyas payloads
de explotación. No cambies contratos ni leas otros componentes.
No ejecutes las pruebas: propónlas e indica los comandos que no
se ejecutaron. No afirmes que una comprobación pasó si solo la
propones. Si falta un archivo o no puedes comprobar algo, dilo.

CRITERIOS DE ACEPTACIÓN
- Identifica las rutas y sigue los valores relevantes hasta cada
  consulta SQL, citando archivo y línea.
- Clasifica cada consulta relevante como concatenada/interpolada,
  parametrizada o no comprobada; indica si es un filtro, insert
  u otra operación.
- Verifica si existe un endpoint de login. Si no existe, indícalo
  y no propongas pruebas de credenciales de login.
- Describe el mecanismo de autenticación existente: cómo recibe y
  valida el token, qué identidad obtiene y qué rutas lo requieren.
  Distingue validación de formato o expiración de verificación
  criptográfica de firma, emisor y audiencia.
- Comprueba qué ocurre cuando falta el token o es inválido/expirado,
  según el código, las pruebas existentes y el contrato observado.
- Revisa si un owner indicado por el cliente puede cambiar el alcance
  de las consultas o crear registros para otra identidad.
- Propón pruebas locales con un token válido, uno ausente, uno inválido
  y uno expirado, según el mecanismo observado; no las describas como
  pruebas de login.
- Propón pruebas con una comilla simple en parámetros de filtro e
  insert, como owner y campos de una tarea. Indica el resultado esperado
  según el contrato: el valor debe tratarse como dato literal o rechazarse
  de forma controlada, sin alterar la consulta ni exponer datos de otro
  propietario.
- Contrasta los resultados esperados con los contratos documentados.
  No presentes recomendaciones como hallazgos confirmados sin evidencia.

FORMATO DE RESPUESTA
Usa una tabla con las columnas:
afirmación | evidencia archivo:línea | comprobado o hipótesis |
prueba propuesta

Incluye IDs H-API-NN. Separa hechos comprobados, hipótesis y aspectos
no verificables. Termina con preguntas abiertas y comandos no ejecutados.