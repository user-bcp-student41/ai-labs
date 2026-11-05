package com.bcp.workshop.auth;

import io.quarkus.test.junit.QuarkusTest;
import io.restassured.response.ValidatableResponse;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.notNullValue;
import static org.hamcrest.Matchers.nullValue;

@QuarkusTest
class AuthResourceTest {
    @Test
    void logsInWithWorkshopUser() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .body("user.username", is("student"))
                .body("token", notNullValue());
    }

    // Spec "Valid credentials preserve the login response contract": full success shape.
    @Test
    void studentLoginReturnsFullSuccessShape() {
        login("student", "Workshop123!")
                .statusCode(200)
                .body("token", notNullValue())
                .body("expiresIn", is(3600))
                .body("user.username", is("student"))
                .body("user.displayName", is("Workshop Student"))
                .body("user.role", is("STUDENT"))
                .body("debug", is("authenticated-with-legacy-flow"));
    }

    // Seed user preserved: trainer keeps its password and role.
    @Test
    void trainerLoginReturnsTrainerRole() {
        login("trainer", "Trainer123!")
                .statusCode(200)
                .body("token", notNullValue())
                .body("user.username", is("trainer"))
                .body("user.role", is("TRAINER"));
    }

    // Spec "Login with credentials that do not match a user": wrong password.
    @Test
    void rejectsValidUserWithWrongPassword() {
        login("student", "wrong-password")
                .statusCode(401)
                .body("token", nullValue())
                .body("message", is("Invalid user student or password"));
    }

    // Spec "Login with credentials that do not match a user": unknown user.
    @Test
    void rejectsUnknownUser() {
        login("nobody", "Workshop123!")
                .statusCode(401)
                .body("token", nullValue())
                .body("message", is("Invalid user nobody or password"));
    }

    // Input validation: existing 400 messages are part of the contract.
    @Test
    void rejectsBlankUsername() {
        login("   ", "Workshop123!")
                .statusCode(400)
                .body("message", is("Username is required"));
    }

    @Test
    void rejectsMissingUsername() {
        postLogin(Map.of("password", "Workshop123!"))
                .statusCode(400)
                .body("message", is("Username is required"));
    }

    @Test
    void rejectsBlankPassword() {
        login("student", "   ")
                .statusCode(400)
                .body("message", is("Password is required"));
    }

    @Test
    void rejectsMissingPassword() {
        postLogin(Map.of("username", "student"))
                .statusCode(400)
                .body("message", is("Password is required"));
    }

    // Failure mapping: a legitimate value with a single quote ends as 401, not 500.
    @Test
    void rejectsLegitimateValueWithSingleQuoteAs401() {
        login("o'brien", "Workshop123!")
                .statusCode(401)
                .body("token", nullValue())
                .body("message", is("Invalid user o'brien or password"));
    }

    // Control case: already rejected today; must stay 401 after the fix.
    @Test
    void rejectsInjectionUsernameWithWrongPassword() {
        login("' OR '1'='1", "wrong-password")
                .statusCode(401)
                .body("token", nullValue());
    }

    // Spec "Login input attempts to alter credential lookup logic": injected password.
    @Test
    void rejectsInjectionPasswordForExistingUser() {
        login("student", "' OR '1'='1")
                .statusCode(401)
                .body("token", nullValue());
    }

    // Spec "Login input attempts to alter credential lookup logic": injected username and password.
    @Test
    void rejectsInjectionInUsernameAndPassword() {
        login("' OR '1'='1", "' OR '1'='1")
                .statusCode(401)
                .body("token", nullValue());
    }

    // Spec "Login input attempts to alter credential lookup logic": comment sequence in username.
    @Test
    void rejectsCommentInjectionInUsername() {
        login("student'--", "any-password")
                .statusCode(401)
                .body("token", nullValue());
    }

    // Input validation: request without a body (observed status is characterized here).
    @Test
    void rejectsRequestWithoutBody() {
        given()
                .contentType("application/json")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Request is null"));
    }

    private static ValidatableResponse login(String username, String password) {
        return postLogin(Map.of("username", username, "password", password));
    }

    private static ValidatableResponse postLogin(Map<String, String> body) {
        return given()
                .contentType("application/json")
                .body(body)
                .when().post("/auth/login")
                .then();
    }
}
