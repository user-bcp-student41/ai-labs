// HApi02AuthorizationTest.java
package pe.bcp.login;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Base64;
import java.util.UUID;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

@QuarkusTest
class HApi02AuthorizationTest {
    @TestHTTPResource("/")
    URI baseUri;

    private final HttpClient client = HttpClient.newHttpClient();
    private String testOwner;

    @AfterEach
    void cleanup() {
        // Estos casos esperan una denegación y no crean filas.
        // Si un caso positivo llega a crear datos, debe añadirse aquí su
        // borrado usando el mecanismo real del proyecto antes de ejecutarlo.
        testOwner = null;
    }

    @Test
    void ca2_negativo_ownerQueryTasks() throws Exception {
        testOwner = uniqueOwner();
        String otherOwner = testOwner + "-otro";

        HttpResponse<String> response = send(
                "GET",
                "/api/tasks?owner=" + encode(otherOwner),
                signedToken(testOwner),
                null);

        assertEquals(403, response.statusCode());
        assertTrue(response.body().contains("\"detail\":\"Forbidden\""));
    }

    @Test
    void ca2_negativo_ownerQuerySummary() throws Exception {
        testOwner = uniqueOwner();
        String otherOwner = testOwner + "-otro";

        HttpResponse<String> response = send(
                "GET",
                "/api/summary?owner=" + encode(otherOwner),
                signedToken(testOwner),
                null);

        assertEquals(403, response.statusCode());
        assertTrue(response.body().contains("\"detail\":\"Forbidden\""));
    }

    @Test
    void ca2_negativo_ownerCuerpoPost() throws Exception {
        testOwner = uniqueOwner();
        String otherOwner = testOwner + "-otro";
        String body = "{\"owner\":\"" + otherOwner + "\"}";

        HttpResponse<String> response = send(
                "POST",
                "/api/tasks",
                signedToken(testOwner),
                body);

        assertEquals(403, response.statusCode());
        assertTrue(response.body().contains("\"detail\":\"Forbidden\""));
    }

    @Test
    void ca3_negativo_tokenLegadoTasks() throws Exception {
        HttpResponse<String> response = send(
                "GET",
                "/api/tasks",
                legacyToken(),
                null);

        assertUnauthorized(response);
    }

    @Test
    void ca3_negativo_tokenLegadoSummary() throws Exception {
        HttpResponse<String> response = send(
                "GET",
                "/api/summary",
                legacyToken(),
                null);

        assertUnauthorized(response);
    }

    @Test
    void ca3_negativo_tokenLegadoPost() throws Exception {
        HttpResponse<String> response = send(
                "POST",
                "/api/tasks",
                legacyToken(),
                "{\"owner\":\"owner-falsificado\"}");

        assertUnauthorized(response);
    }

    private HttpResponse<String> send(
            String method,
            String path,
            String token,
            String body) throws Exception {
        URI uri = baseUri.resolve(path);
        HttpRequest.Builder builder = HttpRequest.newBuilder(uri)
                .header("Authorization", "Bearer " + token)
                .header("Accept", "application/json");

        if ("POST".equals(method)) {
            builder.header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(body));
        } else {
            builder.GET();
        }

        return client.send(builder.build(), HttpResponse.BodyHandlers.ofString());
    }

    private static void assertUnauthorized(HttpResponse<String> response) {
        assertEquals(401, response.statusCode());
        assertTrue(response.body().contains(
                "\"detail\":\"Invalid authentication credentials\""));
    }

    private static String uniqueOwner() {
        return "owner-" + UUID.randomUUID();
    }

    private static String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }

    private static String signedToken(String owner) throws Exception {
        String secret = System.getenv("API_TOKEN_SECRET");
        if (secret == null || secret.isBlank()) {
            throw new IllegalStateException("Falta API_TOKEN_SECRET de laboratorio");
        }

        long expiresAt = Instant.now().getEpochSecond() + 3600;
        String header = base64Url("{\"alg\":\"HS256\",\"typ\":\"JWT\"}");
        String payload = base64Url(
                "{\"sub\":\"" + owner + "\",\"exp\":" + expiresAt + "}");
        String signingInput = header + "." + payload;

        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(
                secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        String signature = Base64.getUrlEncoder().withoutPadding()
                .encodeToString(mac.doFinal(
                        signingInput.getBytes(StandardCharsets.US_ASCII)));

        return signingInput + "." + signature;
    }

    private static String base64Url(String value) {
        return Base64.getUrlEncoder().withoutPadding().encodeToString(
                value.getBytes(StandardCharsets.UTF_8));
    }

    private static String legacyToken() {
        // SUPUESTO de caracterización: Base64 URL-safe sin firma del JSON
        // {"sub":"owner-falsificado"}. Confirmar el formato legado real.
        return base64Url("{\"sub\":\"owner-falsificado\"}");
    }
}