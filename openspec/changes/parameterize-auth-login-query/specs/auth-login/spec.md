# Spec Delta

## Purpose

Defines the observable contract for credential-based login, including successful authentication and rejection of credentials that attempt to bypass authentication.

## ADDED Requirements

### Requirement: Valid credentials preserve the login response contract
The system MUST accept the existing workshop credentials through `POST /auth/login` and return a successful response containing the authenticated username and a token.

#### Scenario: Login with valid workshop credentials
- **WHEN** a client submits username `student` and password `Workshop123!` to `POST /auth/login`
- **THEN** the response status is `200` and the response contains `user.username` equal to `student` and a non-empty `token`

### Requirement: Invalid credentials cannot bypass authentication
The system MUST treat submitted credentials only as credential values and MUST reject any credentials that do not match a user, including input intended to change the meaning of the credential lookup.

#### Scenario: Login with credentials that do not match a user
- **WHEN** a client submits invalid credentials to `POST /auth/login`
- **THEN** the response status is `401` and the response contains no `token`

#### Scenario: Login input attempts to alter credential lookup logic
- **WHEN** a client submits a username or password containing syntax intended to alter the credential lookup rather than identify a user
- **THEN** the response status is `401` and the response contains no `token`