# Tasks

Scope: Issue #22 (H-AUTH-01), component `auth/` only. Production code changes are limited to `LegacyDatabase.findByCredentials`; tests go in `AuthResourceTest`. Run Maven from `auth/`; run Git and OpenSpec from the repository root. Do not create or switch branches.

## 1. Baseline: characterize behavior that must be preserved

- [x] 1.1 Run `mvn test` from `auth/` on the unmodified code and verify the existing `logsInWithWorkshopUser` test passes; if the Quarkus test port is already in use, free it or use an alternative test port and note that in the result
- [x] 1.2 In `AuthResourceTest`, extend the valid-login coverage to the full success shape (`token`, `expiresIn` `3600`, `user.username`, `user.displayName`, `user.role`) for `student`/`Workshop123!`, and add `trainer`/`Trainer123!` with role `TRAINER`; verify both pass on the unmodified code
- [x] 1.3 Add tests for valid user with wrong password and for an unknown user, each expecting `401` and no `token`; verify both pass on the unmodified code
- [x] 1.4 Add tests for blank or missing username and blank or missing password expecting `400` with the existing messages; verify they pass on the unmodified code
- [x] 1.5 Add a test for a legitimate value containing a single quote (for example `o'brien`) expecting `401` and not `500`; verify it passes on the unmodified code
- [x] 1.6 Add a test for username `' OR '1'='1` with a wrong password expecting `401` and no `token`; verify it passes on the unmodified code (control case, already rejected today)
- [x] 1.7 Characterize the null-body request: run it against the unmodified code, assert the observed status, and verify it passes

## 2. Reproduce the vulnerability (tests expected to fail before the fix)

- [x] 2.1 Add a test for username `student` with password `' OR '1'='1` expecting `401` and no `token`; run it on the unmodified code and verify it fails because the response is `200` with a `token`
- [x] 2.2 Add a test for username and password both `' OR '1'='1` expecting `401` and no `token`; run it on the unmodified code and verify it fails with a `200` response
- [x] 2.3 Add a test for username `student'--` with an arbitrary password expecting `401` and no `token`; run it on the unmodified code and verify it fails with a `200` response
- [x] 2.4 Run `mvn test` from `auth/` and verify that the only failing tests are those from 2.1-2.3, and that all of group 1 still passes; keep the output as evidence

## 3. Fix: parameterized credential lookup

- [x] 3.1 In `LegacyDatabase.findByCredentials`, replace the concatenated SQL with a constant query using bound parameters for `username` and `password`, keeping the same selected columns, result mapping, return values, and catch-and-return-`null` behavior; verify by reading the diff that no other production file or line outside this method changed and that no credential value is concatenated into SQL
- [x] 3.2 Run `mvn test` from `auth/` and verify that all tests from groups 1 and 2 pass, including 2.1-2.3 now returning `401` without a `token`

## 4. Final verification

- [x] 4.1 Run `mvn verify` from `auth/` and verify the build succeeds with JaCoCo and without adding exclusions to CodeQL, Dependency Review, or JaCoCo
- [x] 4.2 Verify from the JaCoCo report that coverage of the modified code is 85% or higher
- [x] 4.3 Run `git status` and `git diff --stat` from the root and verify the only files changed under the repository outside `openspec/` are `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java` and `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`, and that `api/`, `web/`, and `docs/` are untouched
- [x] 4.4 Check each scenario in `specs/auth-login/spec.md` against a passing test (valid login, non-matching credentials, lookup-altering input) and verify none is left without coverage

## Workflow follow-up

- Review the change under the project's review requirements before integrating.
- Archive the OpenSpec change after review and verify the archived result.
