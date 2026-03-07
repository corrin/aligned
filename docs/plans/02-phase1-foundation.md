# Phase 1: Foundation — Models, Auth, Settings

## Goal

Port all SQLAlchemy models to async, implement JWT authentication with Google Sign-In, and build the settings/user management API + Vue pages.

## Source Files

| Original | New |
|----------|-----|
| `database/user.py` | `aligned/models/user.py` |
| `database/external_account.py` | `aligned/models/external_account.py` |
| `database/task.py` | `aligned/models/task.py` |
| `chat/models.py` | `aligned/models/conversation.py` |
| `auth/user_auth.py` | `aligned/auth/jwt.py` + `aligned/auth/google.py` |
| `flask_app.py` (login/settings routes) | `aligned/viewsets/auth.py` + `aligned/viewsets/settings.py` |
| `utils/settings.py` | `aligned/config.py` (done in Phase 0) |
| `templates/login.html` | `frontend/src/views/LoginView.vue` |
| `templates/settings.html` | `frontend/src/views/SettingsView.vue` |

## Steps

### 1.1 Port SQLAlchemy Models to Async

Convert all models from Flask-SQLAlchemy to plain SQLAlchemy 2.0 async style. Key changes:

- Remove `db.Model` → use `Base` (DeclarativeBase)
- Remove `UserMixin` (Flask-Login) — JWT replaces session auth
- Remove `cls.query.filter_by(...)` → use `select()` statements with `AsyncSession`
- Keep `MySQLUUID` custom type (needed for MySQL UUID storage)
- Move business logic (e.g., `Task.create_or_update_from_provider_task`, `Task.move_task`) into service functions or keep as classmethods that accept a session parameter
- Use `datetime.now(timezone.utc)` everywhere (the original mixes `utcnow()` and `timezone.utc`)

**Models to port:**

1. **User** — Remove `UserMixin`, `get_id()`. Keep all fields. Add `hashed_password` field (optional, for future non-Google auth).

2. **ExternalAccount** — Port as-is. All fields, relationships, and helper methods. Methods that use `cls.query` must accept `session: AsyncSession` parameter.

3. **Task** — Port as-is. The `create_or_update_from_provider_task`, `move_task`, `update_task_order`, `sync_task_deletions` methods need async conversion. Replace `db.session` with injected session.

4. **Conversation + ChatMessage** — Port as-is with async queries.

### 1.2 Create Alembic Migration

Generate the initial migration from the ported models:

```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

### 1.3 FastREST Serializers

```python
# aligned/serializers/user.py
from fastrest.serializers import ModelSerializer
from aligned.models.user import User

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "app_login", "ai_instructions", "schedule_slot_duration", "llm_model"]
        read_only_fields = ["id", "app_login"]

class UserSettingsSerializer(ModelSerializer):
    """For the settings update endpoint — includes sensitive fields."""
    class Meta:
        model = User
        fields = ["ai_api_key", "ai_instructions", "schedule_slot_duration", "llm_model"]

# aligned/serializers/external_account.py
class ExternalAccountSerializer(ModelSerializer):
    class Meta:
        model = ExternalAccount
        fields = [
            "id", "provider", "external_email",
            "use_for_calendar", "use_for_tasks",
            "is_primary_calendar", "is_primary_tasks",
            "needs_reauth", "last_sync",
        ]
        read_only_fields = ["id"]
```

### 1.4 JWT Authentication

Create `aligned/auth/jwt.py`:

- `create_access_token(user_id, email)` → signs JWT with `JWT_SECRET_KEY`, expiry 24h
- `verify_access_token(token)` → decodes and validates
- FastREST `TokenAuthentication` backend that extracts Bearer token, decodes JWT, loads User from DB

Create `aligned/auth/google.py`:

- `verify_google_token(id_token)` → verifies Google ID token using `google.auth.transport.requests` + `google.oauth2.id_token`
- Returns email on success

### 1.5 Auth ViewSet / Routes

These don't fit the CRUD viewset pattern, so use FastAPI routes directly:

```python
# aligned/viewsets/auth.py — mounted as regular FastAPI routes

@router.post("/api/auth/google")
async def google_login(request):
    """Accept Google ID token, verify, create/find user, return JWT."""
    # 1. Verify Google ID token
    # 2. Find or create User by app_login (email)
    # 3. Return JWT access token

@router.post("/api/auth/logout")
async def logout(request):
    """Client-side only for JWT — this is a no-op or token blacklist."""
    pass

@router.get("/api/auth/me")
async def get_current_user(request):
    """Return current user profile (from JWT)."""
    pass
```

### 1.6 Settings ViewSet

```python
# aligned/viewsets/settings.py
from fastrest.viewsets import ModelViewSet

class UserSettingsViewSet(ModelViewSet):
    """GET/PUT for current user's settings."""
    queryset = User
    serializer_class = UserSettingsSerializer
    permission_classes = [IsAuthenticated]

    # Override to always scope to current user
    async def get_object(self):
        return self.request.user
```

ExternalAccount listing for settings page:

```python
class ExternalAccountViewSet(ReadOnlyModelViewSet):
    queryset = ExternalAccount
    serializer_class = ExternalAccountSerializer
    permission_classes = [IsAuthenticated]

    # Filter to current user's accounts only
    def get_queryset(self):
        return ExternalAccount.query.filter_by(user_id=self.request.user.id)
```

### 1.7 Router Registration

```python
# In app.py
router = DefaultRouter()
router.register("settings", UserSettingsViewSet, basename="settings")
router.register("external-accounts", ExternalAccountViewSet, basename="external-account")
app.include_router(router.urls, prefix="/api")
# Plus the auth routes (non-viewset)
app.include_router(auth_router, prefix="/api/auth")
```

### 1.8 Vue Frontend — Login

`frontend/src/views/LoginView.vue`:
- Google Sign-In button (using `@google/gsi` or `vue3-google-login`)
- On success: POST Google ID token to `/api/auth/google`
- Store JWT in localStorage/Pinia store
- Redirect to chat page

`frontend/src/api/client.ts`:
- Axios instance with interceptor to attach `Authorization: Bearer <token>`
- 401 interceptor to redirect to login

`frontend/src/stores/auth.ts` (Pinia):
- `user`, `token` state
- `login()`, `logout()`, `fetchUser()` actions

### 1.9 Vue Frontend — Settings

`frontend/src/views/SettingsView.vue`:
- Form for AI API key, AI instructions, LLM model, schedule slot duration
- List of external accounts with primary toggles
- Save via `PUT /api/settings/{id}`

### 1.10 Vue Router + Navigation Guard

```typescript
// Protect routes — redirect to /login if no token
router.beforeEach((to) => {
    const auth = useAuthStore()
    if (to.meta.requiresAuth && !auth.token) {
        return '/login'
    }
})
```

### 1.11 Tests

**Unit tests:**
- User model creation, serialization
- JWT token creation and verification
- Google token verification (mocked)

**Integration tests (FastREST APIClient):**
- `POST /api/auth/google` with valid/invalid tokens
- `GET /api/auth/me` with/without JWT
- `GET /api/settings` returns current user settings
- `PUT /api/settings` updates settings
- `GET /api/external-accounts` returns user's accounts only

**E2E tests (Playwright):**
- Login page loads, shows Google Sign-In button
- After login, redirected to main page
- Settings page loads, can edit and save settings
- Logout works, redirected to login

## Acceptance Criteria

- [ ] All 4 models created with async support
- [ ] `alembic upgrade head` creates all tables
- [ ] Google Sign-In → JWT flow works end-to-end
- [ ] JWT protects all API endpoints (401 without token)
- [ ] Settings CRUD works via API
- [ ] Vue login + settings pages functional
- [ ] `mypy aligned --strict` passes
- [ ] All tests pass (unit, integration, e2e)
- [ ] OpenAPI docs at `/docs` show all endpoints with typed schemas
