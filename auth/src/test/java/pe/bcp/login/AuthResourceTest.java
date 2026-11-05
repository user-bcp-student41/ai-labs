// AuthResourceTest.java
package pe.bcp.login;

import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

@QuarkusTest
class AuthResourceTest {
    private static final String SQL_INJECTION = "' OR '1'='1";
    private static final HttpClient HTTP = HttpClient.newHttpClient();

    @TestHTTPResource("/auth/login")
    URI loginUri;

    @Test
    void ca1_positivo_consultaPreparadaSinConcatenacion() throws IOException {
        Path sourcePath = Paths.get(
                "src/main/java/com/bcp/workshop/auth/LegacyDatabase.java");
        assertTrue(Files.isRegularFile(sourcePath),
                "No se encontró la fuente de LegacyDatabase en la ruta esperada");

        String source = new String(Files.readAllBytes(sourcePath), StandardCharsets.UTF_8);
        int methodName = source.indexOf("findByCredentials");
        assertTrue(methodName >= 0, "No se encontró findByCredentials");

        int openBrace = source.indexOf('{', methodName);
        assertTrue(openBrace >= 0, "No se encontró el cuerpo de findByCredentials");

        int depth = 0;
        int closeBrace = -1;
        for (int i = openBrace; i < source.length(); i++) {
            char current = source.charAt(i);
            if (current == '{') {
                depth++;
            } else if (current == '}') {
                depth--;
                if (depth == 0) {
                    closeBrace = i;
                    break;
                }
            }
        }
        assertTrue(closeBrace > openBrace, "No se pudo delimitar findByCredentials");

        String method = source.substring(openBrace, closeBrace + 1);
        assertTrue(Pattern.compile("\\bPreparedStatement\\b").matcher(method).find(),
                "El método no declara ni usa PreparedStatement");

        assertTrue(hasParameterBinding(method, "username"),
                "No se encontró una asignación parametrizada de username");
        assertTrue(hasParameterBinding(method, "password"),
                "No se encontró una asignación parametrizada de password");

        Pattern directConcatenation = Pattern.compile(
                "(?:[\"']\\s*\\+\\s*(?:username|password)\\b"
                        + "|\\b(?:username|password)\\s*\\+\\s*[\"'])");
        assertFalse(directConcatenation.matcher(method).find(),
                "Se detectó concatenación directa de credenciales en el método");
    }

    @Test
    void ca2_positivo_loginValidoDevuelveUsuarioYToken() throws Exception {
        HttpResponse<String> response = post("student", "Workshop123!");

        assertTrue(response.statusCode() == 200,
                "Se esperaba HTTP 200, recibido: " + response.statusCode());
        assertTrue(Pattern.compile(
                        "\"user\"\\s*:\\s*\\{[^}]*\"username\"\\s*:\\s*\"student\"")
                        .matcher(response.body()).find(),
                "La respuesta debe incluir user.username igual a student");
        assertTrue(Pattern.compile("\"token\"\\s*:\\s*\"[^\"]+\"")
                        .matcher(response.body()).find(),
                "La respuesta debe incluir un token no vacío");
    }

    @Test
    void ca3_negativo_inyeccionEnUsuarioDevuelve401SinToken() throws Exception {
        HttpResponse<String> response = post(SQL_INJECTION, "valor-no-válido");

        assertUnauthorizedWithoutToken(response);
    }

    @Test
    void ca3_negativo_inyeccionEnPasswordDevuelve401SinToken() throws Exception {
        HttpResponse<String> response = post("valor-no-válido", SQL_INJECTION);

        assertUnauthorizedWithoutToken(response);
    }

    private static boolean hasParameterBinding(String method, String parameterName) {
        Pattern binding = Pattern.compile(
                "\\.set(?:String|Object)\\s*\\(\\s*[^,]+,\\s*"
                        + Pattern.quote(parameterName)
                        + "\\b");
        Matcher matcher = binding.matcher(method);
        return matcher.find();
    }

    private HttpResponse<String> post(String username, String password) throws Exception {
        String json = "{\"username\":\"" + escapeJson(username)
                + "\",\"password\":\"" + escapeJson(password) + "\"}";

        HttpRequest request = HttpRequest.newBuilder(loginUri)
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();

        return HTTP.send(request, HttpResponse.BodyHandlers.ofString());
    }

    private static String escapeJson(String value) {
        return value.replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }

    private static void assertUnauthorizedWithoutToken(HttpResponse<String> response) {
        assertTrue(response.statusCode() == 401,
                "Se esperaba HTTP 401, recibido: " + response.statusCode());
        assertFalse(Pattern.compile("\"token\"\\s*:").matcher(response.body()).find(),
                "La respuesta de error no debe incluir el campo token");
    }
}