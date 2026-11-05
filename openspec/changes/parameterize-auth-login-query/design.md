# Design

## Context

Motivation and scope: see `proposal.md`. Required behavior: see `specs/auth-login/spec.md`. This design covers only the `auth/` component (Quarkus 3.27, Java 21, SQLite via `sqlite-jdbc`).

Current state observed in the code:

- `AuthResource.login` validates the request, calls `LegacyDatabase.findByCredentials(username, password)`, and builds the response. It does not touch SQL.
- `LegacyDatabase.findByCredentials` builds the query by concatenating `username` and `password` into the SQL text and runs it through a `Statement` (H-AUTH-01, `LegacyDatabase.java:32`).
- Any exception inside `findByCredentials` is caught, printed, and turned into `null`, which `AuthResource` maps to `401`.
- `AuthResource` only uses `trim()` to detect blank input; the untrimmed values are what reach the lookup.
- The database location comes from `AUTH_DB_URL` (default `jdbc:sqlite:./data/workshop.db`, relative to the working directory). `initialize()` seeds `student` and `trainer` with `INSERT OR IGNORE` using static SQL only (no user input).
- The only existing test is `AuthResourceTest.logsInWithWorkshopUser` (valid login).

Because `AND` binds tighter than `OR`, the current query is bypassed only by some payloads (analysis, to be confirmed by running the tests before the fix):

| Input | Resulting condition | Expected today |
|---|---|---|
| `student` / `' OR '1'='1` | `username='student' AND password='' OR '1'='1'` is always true | `200` (bypass) |
| `' OR '1'='1` / `' OR '1'='1` | always true | `200` (bypass) |
| `student'--` / any value | password check commented out | `200` (bypass) |
| `' OR '1'='1` / wrong password | `username='' OR ('1'='1' AND password='wrong')` is false | `401` (not a bypass) |
| `o'brien` / any value | SQL syntax error, swallowed | `401` |

## Goals / Non-Goals

**Goals:**

- Make the credential lookup treat `username` and `password` strictly as data, so no input can change the query structure.
- Keep every externally observable behavior of `POST /auth/login` identical, except that bypass inputs now yield `401`.
- Keep the change small enough to review in isolation: one method in production code plus tests.

**Non-Goals:**

- Hashing or otherwise changing how passwords are stored or compared (plaintext storage is a separate finding).
- Changing the token format, secret, or lifetime (`LegacyTokenUtil`), the `debug` field, or the `401` message that echoes the username.
- Restructuring `AuthResource` into layers or other clean-code refactors; those belong in separate reviewable changes.
- Changing database configuration, schema, seed data, dependencies, `application.properties`, CORS, or error handling policy (the swallow-and-return-`null` behavior stays).
- Touching `api/`, `web/`, or `docs/ENDPOINTS.md` (which documents ReqFlow API and has no `/auth/login` section).

## Protected Contracts

These must be identical before and after the change. The first two rows come from the specs; the rest are observed behavior that the change must not alter.

| Contract | Behavior to preserve |
|---|---|
| `POST /auth/login` valid credentials (spec) | `student` / `Workshop123!` returns `200` with `user.username` and a non-empty `token`. |
| Invalid credentials (spec) | Non-matching credentials return `401` with no `token`. |
| Success body (observed) | `token`, `expiresIn` = `3600`, `user.username`, `user.displayName` (HTML-escaped), `user.role`, `debug`. |
| Request body (observed) | JSON with `username`, `password`, optional `client` (ignored); unknown properties are ignored. |
| Input validation (observed) | Null body, blank/missing username, blank/missing password return `400` with the existing messages. |
| `401` body (observed) | `{"message": "Invalid user <username> or password"}`. |
| Seed users (observed) | `student` (`STUDENT`) and `trainer` (`TRAINER`) with their current passwords. |
| Matching semantics (observed) | Exact, case-sensitive match on both fields; values are not trimmed or normalized before matching. |
| Failure mapping (observed) | A database failure during lookup still ends as `401`, not `500`. |
| Lookup signature | `findByCredentials(String, String)` returns a `UserRecord` or `null`, so `AuthResource` needs no change. |

## Affected Components

| Component | Change |
|---|---|
| `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java` | Only `findByCredentials`: the lookup no longer builds SQL from user input. Same columns selected, same return values. |
| `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java` | New characterization and injection tests. |

Not affected: `AuthResource`, `LegacyTokenUtil`, `UserRecord`, `LoginRequest`, `pom.xml`, `application.properties`, `initialize()`, `api/`, `web/`, general docs.

## Decisions

### D1. Use JDBC parameter binding inside `findByCredentials`

The query text becomes a constant with one placeholder per credential, and `username` and `password` are bound as string parameters. The query, selected columns, result mapping, `try-with-resources`, and the catch-and-return-`null` behavior stay as they are.

Why: it removes the vulnerability at its cause, requires no new dependency, preserves exact string-equality semantics in SQLite, and matches the acceptance criterion in Issue #22.

Alternatives considered:

- **Escape or strip quotes**: fragile, depends on SQL dialect details, and changes which valid inputs match. Rejected.
- **Reject inputs containing SQL characters in `AuthResource`**: a blacklist that changes the contract (`400` or `401` for legitimate values) and does not fix the lookup itself. Rejected.
- **ORM or repository framework (for example Panache)**: new dependency and a much larger change than the finding requires. Rejected.
- **Fetch by username only and compare the password in Java**: changes where the comparison happens and invites plaintext handling changes; better deferred to a password-hashing change. Rejected for this scope.

### D2. Keep the method contract and error mapping unchanged

No signature, return type, or exception behavior changes. This keeps the change confined to one method and makes the "no behavior drift" claim verifiable by tests rather than by reading code.

Alternative: let lookup failures surface as `500`. That is arguably better practice but is an observable contract change, so it is out of scope and noted under risks.

### D3. Tests extend the existing `AuthResourceTest` through HTTP

The tests exercise `POST /auth/login` end to end with the existing Quarkus test setup, so they validate the spec scenarios as observed by a client and keep passing if the lookup is later refactored. No new test dependencies.

Alternative: unit-test `LegacyDatabase` directly. It is useful for later layering work but would not prove the `200`/`401` contract, so it is not the primary evidence here.

## Incremental Strategy

Each step is independently reviewable and leaves the build in a known state.

1. **Characterize current behavior (tests only).** Add the preserved-behavior tests below and the injection tests. Run `mvn test` from `auth/` against the unmodified code. Record the result: preserved-behavior tests pass; bypass tests fail, confirming the vulnerability. Keep this output as evidence.
2. **Apply the fix.** Change only `findByCredentials` as in D1. No other production file changes.
3. **Verify.** Re-run `mvn verify` from `auth/`: all tests pass and JaCoCo reports at least 85% coverage on the modified code. Confirm the diff touches only `LegacyDatabase.java` and `AuthResourceTest.java` under `auth/`.

## Characterization Tests Required Before Changing Behavior

All run through `POST /auth/login`. "Before" is the expected result on the unmodified code; "After" is the required result.

| # | Case | Before | After |
|---|---|---|---|
| 1 | `student` / `Workshop123!` returns full success shape (`token`, `expiresIn` `3600`, `user.username`, `user.displayName`, `user.role`) | `200` | `200` |
| 2 | `trainer` / `Trainer123!` returns `user.role` `TRAINER` | `200` | `200` |
| 3 | Valid user, wrong password | `401`, no `token` | `401`, no `token` |
| 4 | Unknown user | `401`, no `token` | `401`, no `token` |
| 5 | Blank or missing username; blank or missing password | `400` with existing messages | unchanged |
| 6 | Value with a single quote that is not an attack (for example `o'brien`) | `401`, not `500` | `401`, not `500` |
| 7 | Password `' OR '1'='1` with username `student` | `200` (bypass) | `401`, no `token` |
| 8 | Username and password both `' OR '1'='1` | `200` (bypass) | `401`, no `token` |
| 9 | Username `student'--` with an arbitrary password | `200` (bypass) | `401`, no `token` |
| 10 | Username `' OR '1'='1` with a wrong password | `401` (already rejected) | `401`, no `token` |

Rows 7-9 are the red tests that prove the finding; rows 1-6 and 10 must pass both before and after. The null-body case is checked when writing the tests, and the observed value is what gets characterized.

## Risks / Trade-offs

- [A test that was green before could change meaning after the fix] → Characterization tests 1-6 and 10 run before and after; any difference is a regression to investigate, not to adjust.
- [Lookup failures still return `401`, which can mask database outages] → Preserved deliberately to protect the contract; track as a separate finding.
- [Closing H-AUTH-01 can be read as "auth is secure"] → Plaintext passwords, the reversible token with an embedded secret, the echoed username in the `401` message, and the `debug` field remain and are out of scope.
- [Tests depend on the shared SQLite file `./data/workshop.db` relative to the working directory] → Run tests from `auth/` as the repository rules require; seed data uses `INSERT OR IGNORE`, so repeated runs are stable.
- [Port `8081` already in use makes the Quarkus test fail to start, as observed in an earlier validation] → Treat it as an environment issue; free the port or run with an alternative test port, and do not read it as a product failure.
- [Coverage target for modified code (85% or higher) and security scanners] → Do not add exclusions to JaCoCo, CodeQL, or Dependency Review; coverage comes from the tests above.

## Migration Plan / Rollback

- No data, schema, configuration, or API migration is needed; the change is code and tests inside `auth/`.
- Deployment is a normal release of the `auth` service.
- Rollback: revert the fix commit on the branch (the tests-only commit can stay). There is no feature flag because it would keep the vulnerable path available. Reverting reintroduces H-AUTH-01, so prefer a forward fix if a defect appears in the new lookup.

## Open Questions

- Should `POST /auth/login` be documented in `docs/ENDPOINTS.md` (or a separate auth contract document) so future changes have a documented baseline? This can be decided later without affecting the specs or this approach.
