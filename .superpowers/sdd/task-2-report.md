# Task 2 Report — Password Validation API Endpoints

## Status: COMPLETE ✅

## Summary

Implemented 3 authentication API endpoints with password strength validation using TDD workflow.

## Changes Made

### 1. `backend/app/schemas/auth.py`
Added 2 new Pydantic models:
- `PasswordStrengthResponse` — score (0-100), strength ("weak"|"medium"|"strong"), issues list
- `ChangePasswordRequest` — old_password, new_password

### 2. `backend/app/routers/auth.py`
- **New import**: `Query` from fastapi, `validate_password_strength`/`check_password_validity` from `app.utils.password_validator`, new schema models
- **New endpoint** `POST /api/auth/password/validate` — returns real-time password strength without auth
- **Modified** `POST /api/auth/register` — added password strength check after email uniqueness check; now returns `{access_token, token_type, user}` on success
- **New endpoint** `POST /api/auth/change-password` — authenticated, validates old password (401 on failure), checks new password strength (400 on weak), rejects same-as-old (400), updates hash

### 3. `backend/tests/test_auth.py` (new file)
8 integration tests across 3 test classes:
- `TestPasswordValidateEndpoint` (2 tests)
- `TestRegisterWithPasswordValidation` (2 tests)
- `TestChangePasswordEndpoint` (4 tests)

## Test Results

```
25 passed, 0 failed
- 17 pre-existing tests (test_password_validator.py) — all still pass
- 8 new integration tests (test_auth.py) — all pass
```

## TDD Cycle
1. RED: Wrote tests → 4 failed, 4 errors
2. GREEN: Implemented schemas + endpoints
3. All 25 tests pass

## Key Design Decisions
- `POST /change-password` validates old password BEFORE new password strength (returns 401 first, then 400)
- Same-password check happens after strength validation to avoid leaking old password info through error ordering
- Register endpoint now returns a JWT token on success (consistent with login UX)
- Fixture uses `uuid4()` instead of `time.time()` to ensure unique emails across fast concurrent test runs
