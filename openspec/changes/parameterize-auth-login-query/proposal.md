# Proposal

## Why

GitHub Issue [#22](https://github.com/user-bcp-student41/ai-labs/issues/22), Hallazgo H-AUTH-01, reports that credential input can change the login database query and allow authentication without valid credentials. This change closes that authentication bypass while preserving the existing login contract.

## What Changes

- Require credential lookup to treat username and password as values that cannot change the meaning of the lookup.
- Preserve `POST /auth/login`: valid workshop credentials return `200` with `user.username` and `token`; invalid credentials, including values intended to alter lookup logic, return `401` without a token.
- Limit the change to the `auth/` component. Do not change the endpoint, its successful response contract, or behavior in `api/` and `web/`.

Out of scope: token format or lifecycle changes, authentication redesign, unrelated findings, and changes to other components or endpoints.

## Capabilities

### New Capabilities
- `auth-login`: observable behavior for credential-based login and rejection of credentials that attempt to alter lookup logic.

### Modified Capabilities
- None.

## Impact

The affected component is `auth/`, specifically the credential lookup and its login tests. `docs/ENDPOINTS.md` describes ReqFlow API endpoints and does not document `POST /auth/login`; therefore it provides no login-specific baseline to change. The login scenarios will preserve the behavior explicitly committed in Issue #22 and asserted by the existing `AuthResourceTest`. No API contract documented in `docs/ENDPOINTS.md` is changed.