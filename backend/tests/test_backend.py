"""
G Telepathy — Backend Test Suite (Cloudflare D1 edition)
Tests all backend functions using pytest + httpx AsyncClient.
Run with: pytest backend/tests/ -v --tb=short
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

MOCK_USER = {
    "id": "user-test-abc",
    "email": "test@example.com",
    "user_metadata": {"display_name": "Tester"},
}

# HTTPBearer returns 401 or 403 for missing/invalid tokens depending on
# FastAPI/Starlette version. Accept both as "not authorized".
AUTH_REQUIRED = (401, 403)


# ── Fixtures ───────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def app():
    from main import app as _app
    return _app


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client(app):
    """Client with get_current_user dependency overridden to skip Supabase."""
    from routers.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Health / Root
# ─────────────────────────────────────────────────────────────────────────────
class TestHealthEndpoints:
    @pytest.mark.asyncio
    async def test_root_returns_ok(self, client):
        r = await client.get("/")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["phase"] == "beta"
        assert body["service"] == "G Telepathy API"

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_security_headers_present(self, client):
        r = await client.get("/health")
        assert r.headers.get("X-Content-Type-Options") == "nosniff"
        assert r.headers.get("X-Frame-Options") == "DENY"
        assert r.headers.get("X-XSS-Protection") == "1; mode=block"
        assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_server_header_not_exposed(self, client):
        r = await client.get("/health")
        assert "server" not in r.headers


# ─────────────────────────────────────────────────────────────────────────────
# 2. Auth — register input validation
# ─────────────────────────────────────────────────────────────────────────────
class TestAuthRegisterValidation:
    @pytest.mark.asyncio
    async def test_register_without_d1_returns_503(self, client):
        """Valid data + no D1 configured → 503."""
        r = await client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "TestPass1",
            "display_name": "Tester",
        })
        assert r.status_code == 503
        assert "not configured" in r.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_weak_password_rejected(self, client):
        r = await client.post("/api/auth/register", json={
            "email": "a@b.com", "password": "abc", "display_name": "User",
        })
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_register_password_no_uppercase_rejected(self, client):
        r = await client.post("/api/auth/register", json={
            "email": "a@b.com", "password": "alllowercase1", "display_name": "User",
        })
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_register_password_no_digit_rejected(self, client):
        r = await client.post("/api/auth/register", json={
            "email": "a@b.com", "password": "NoDigitHere", "display_name": "User",
        })
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_register_display_name_too_short(self, client):
        r = await client.post("/api/auth/register", json={
            "email": "a@b.com", "password": "TestPass1", "display_name": "X",
        })
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client):
        r = await client.post("/api/auth/register", json={
            "email": "notanemail", "password": "TestPass1", "display_name": "Valid Name",
        })
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client):
        r = await client.post("/api/auth/register", json={})
        assert r.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 3. Auth — login
# ─────────────────────────────────────────────────────────────────────────────
class TestAuthLogin:
    @pytest.mark.asyncio
    async def test_login_without_d1_returns_503(self, client):
        r = await client.post("/api/auth/login", json={
            "email": "test@example.com", "password": "TestPass1",
        })
        assert r.status_code == 503

    @pytest.mark.asyncio
    async def test_login_missing_password(self, client):
        r = await client.post("/api/auth/login", json={"email": "a@b.com"})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, client):
        r = await client.post("/api/auth/login", json={
            "email": "notanemail", "password": "TestPass1",
        })
        assert r.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 4. Auth — protected routes
# ─────────────────────────────────────────────────────────────────────────────
class TestAuthProtection:
    @pytest.mark.asyncio
    async def test_get_me_without_token(self, client):
        r = await client.get("/api/auth/me")
        assert r.status_code in AUTH_REQUIRED

    @pytest.mark.asyncio
    async def test_get_me_with_fake_token(self, client):
        r = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer faketoken123"},
        )
        assert r.status_code in (401, 503)

    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, auth_client):
        """get_me falls back to JWT payload when D1 is not configured."""
        r = await auth_client.get("/api/auth/me")
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == MOCK_USER["id"]
        assert body["email"] == MOCK_USER["email"]


# ─────────────────────────────────────────────────────────────────────────────
# 5. Chat Router — auth enforcement
# ─────────────────────────────────────────────────────────────────────────────
class TestChatAuth:
    @pytest.mark.asyncio
    async def test_get_conversations_no_auth(self, client):
        r = await client.get("/api/chat/conversations")
        assert r.status_code in AUTH_REQUIRED

    @pytest.mark.asyncio
    async def test_get_messages_no_auth(self, client):
        r = await client.get("/api/chat/conversations/test-123/messages")
        assert r.status_code in AUTH_REQUIRED

    @pytest.mark.asyncio
    async def test_send_message_no_auth(self, client):
        r = await client.post(
            "/api/chat/conversations/test-123/messages",
            json={"encrypted_content": "payload", "message_type": "text"},
        )
        assert r.status_code in AUTH_REQUIRED

    @pytest.mark.asyncio
    async def test_get_conversations_fake_token(self, client):
        r = await client.get(
            "/api/chat/conversations",
            headers={"Authorization": "Bearer faketoken"},
        )
        assert r.status_code in (401, 503)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Chat Router — input validation (authenticated)
# ─────────────────────────────────────────────────────────────────────────────
class TestChatValidation:
    @pytest.mark.asyncio
    async def test_send_message_empty_content_rejected(self, auth_client):
        r = await auth_client.post(
            "/api/chat/conversations/conv-123/messages",
            json={"encrypted_content": "", "message_type": "text"},
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_send_message_invalid_type_rejected(self, auth_client):
        r = await auth_client.post(
            "/api/chat/conversations/conv-123/messages",
            json={"encrypted_content": "payload==", "message_type": "INVALID"},
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_send_message_oversized_payload_rejected(self, auth_client):
        r = await auth_client.post(
            "/api/chat/conversations/conv-123/messages",
            json={"encrypted_content": "A" * 101_000, "message_type": "text"},
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_send_message_valid_accepted(self, auth_client):
        """201 if D1 configured, 503 in test env (no credentials)."""
        r = await auth_client.post(
            "/api/chat/conversations/conv-123/messages",
            json={"encrypted_content": "U2FsdGVkX1+abc123==", "message_type": "text"},
        )
        assert r.status_code in (201, 503)
        if r.status_code == 201:
            body = r.json()
            assert body["sender_id"] == MOCK_USER["id"]
            assert body["status"] == "sent"

    @pytest.mark.asyncio
    async def test_get_messages_authenticated(self, auth_client):
        """Auth works; 200 if D1 configured, 403 if not member, 503 if D1 down."""
        r = await auth_client.get("/api/chat/conversations/conv-123/messages")
        assert r.status_code in (200, 403, 503)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Calls Router
# ─────────────────────────────────────────────────────────────────────────────
class TestCallsAuth:
    @pytest.mark.asyncio
    async def test_initiate_call_no_auth(self, client):
        r = await client.post("/api/calls/initiate", json={
            "target_user_id": "other-user", "call_type": "audio",
        })
        assert r.status_code in AUTH_REQUIRED

    @pytest.mark.asyncio
    async def test_end_call_no_auth(self, client):
        r = await client.post("/api/calls/call-123/end")
        assert r.status_code in AUTH_REQUIRED

    @pytest.mark.asyncio
    async def test_call_history_no_auth(self, client):
        r = await client.get("/api/calls/history")
        assert r.status_code in AUTH_REQUIRED


class TestCallsValidation:
    @pytest.mark.asyncio
    async def test_initiate_call_invalid_type(self, auth_client):
        r = await auth_client.post(
            "/api/calls/initiate",
            json={"target_user_id": "other-user", "call_type": "fax"},
        )
        assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_initiate_call_valid_audio(self, auth_client):
        r = await auth_client.post(
            "/api/calls/initiate",
            json={"target_user_id": "other-user-id", "call_type": "audio"},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["call_type"] == "audio"
        assert body["status"] == "ringing"
        assert body["caller_id"] == MOCK_USER["id"]

    @pytest.mark.asyncio
    async def test_initiate_call_valid_video(self, auth_client):
        r = await auth_client.post(
            "/api/calls/initiate",
            json={"target_user_id": "other-user-id", "call_type": "video"},
        )
        assert r.status_code == 201

    @pytest.mark.asyncio
    async def test_end_call_authenticated(self, auth_client):
        r = await auth_client.post("/api/calls/call-abc-123/end")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ended"

    @pytest.mark.asyncio
    async def test_call_history_authenticated(self, auth_client):
        r = await auth_client.get("/api/calls/history")
        assert r.status_code == 200
        assert "calls" in r.json()


# ─────────────────────────────────────────────────────────────────────────────
# 8. Rooms Router
# ─────────────────────────────────────────────────────────────────────────────
class TestRoomsAuth:
    @pytest.mark.asyncio
    async def test_list_rooms_public(self, client):
        """Room listing is intentionally public."""
        r = await client.get("/api/rooms/")
        assert r.status_code == 200
        assert "rooms" in r.json()

    @pytest.mark.asyncio
    async def test_create_room_no_auth(self, client):
        r = await client.post("/api/rooms/", json={"name": "Test Room"})
        assert r.status_code in AUTH_REQUIRED

    @pytest.mark.asyncio
    async def test_join_room_no_auth(self, client):
        r = await client.post("/api/rooms/room-123/join")
        assert r.status_code in AUTH_REQUIRED

    @pytest.mark.asyncio
    async def test_leave_room_no_auth(self, client):
        r = await client.post("/api/rooms/room-123/leave")
        assert r.status_code in AUTH_REQUIRED


class TestRoomsValidation:
    @pytest.mark.asyncio
    async def test_create_room_name_too_short(self, auth_client):
        r = await auth_client.post("/api/rooms/", json={"name": "X", "language": "en"})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_create_room_invalid_language(self, auth_client):
        r = await auth_client.post("/api/rooms/", json={
            "name": "Valid Room", "language": "a" * 20,
        })
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_create_room_valid(self, auth_client):
        """201 when D1 is configured, 503 when not (test env)."""
        r = await auth_client.post("/api/rooms/", json={
            "name": "English Chat Room", "topic": "General", "language": "en",
        })
        assert r.status_code in (201, 503)
        if r.status_code == 201:
            body = r.json()
            assert body["owner_id"] == MOCK_USER["id"]
            assert body["name"] == "English Chat Room"

    @pytest.mark.asyncio
    async def test_join_room_valid(self, auth_client):
        """200 when D1 is configured, 404/503 when not (test env)."""
        r = await auth_client.post("/api/rooms/room-abc-123/join")
        assert r.status_code in (200, 404, 503)

    @pytest.mark.asyncio
    async def test_leave_room_valid(self, auth_client):
        """200 when D1 is configured, 503 when not (test env)."""
        r = await auth_client.post("/api/rooms/room-abc-123/leave")
        assert r.status_code in (200, 503)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Translation Router
# ─────────────────────────────────────────────────────────────────────────────
class TestTranslationAuth:
    @pytest.mark.asyncio
    async def test_translate_no_auth(self, client):
        r = await client.post("/api/translate/text", json={
            "text": "Hello", "target_language": "es",
        })
        assert r.status_code in AUTH_REQUIRED

    @pytest.mark.asyncio
    async def test_detect_language_no_auth(self, client):
        r = await client.post("/api/translate/detect", json={"text": "Hola"})
        assert r.status_code in AUTH_REQUIRED

    @pytest.mark.asyncio
    async def test_get_languages_no_auth(self, client):
        r = await client.get("/api/translate/languages")
        assert r.status_code in AUTH_REQUIRED


class TestTranslationValidation:
    @pytest.mark.asyncio
    async def test_translate_empty_text_rejected(self, auth_client):
        r = await auth_client.post("/api/translate/text", json={
            "text": "", "target_language": "es",
        })
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_translate_text_too_long(self, auth_client):
        r = await auth_client.post("/api/translate/text", json={
            "text": "A" * 6000, "target_language": "es",
        })
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_translate_invalid_language_code(self, auth_client):
        r = await auth_client.post("/api/translate/text", json={
            "text": "Hello", "target_language": "INVALID!!",
        })
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_translate_without_api_key_returns_503(self, auth_client):
        """No GOOGLE_TRANSLATE_API_KEY → 503 (service not configured)."""
        r = await auth_client.post("/api/translate/text", json={
            "text": "Hello world", "target_language": "es",
        })
        assert r.status_code == 503

    @pytest.mark.asyncio
    async def test_detect_empty_text_rejected(self, auth_client):
        r = await auth_client.post("/api/translate/detect", json={"text": ""})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_detect_without_api_key_returns_503(self, auth_client):
        r = await auth_client.post("/api/translate/detect", json={"text": "bonjour"})
        assert r.status_code == 503


# ─────────────────────────────────────────────────────────────────────────────
# 10. Config validation (unit tests, no HTTP calls needed)
# ─────────────────────────────────────────────────────────────────────────────
class TestConfigValidation:
    def test_wildcard_cors_rejected(self):
        from pydantic import ValidationError
        from config import Settings
        with pytest.raises((ValidationError, ValueError)):
            Settings(cors_origins=["*"])

    def test_insecure_jwt_secret_rejected(self):
        from pydantic import ValidationError
        from config import Settings
        with pytest.raises((ValidationError, ValueError)):
            Settings(jwt_secret_key="secret")

    def test_insecure_jwt_secret_rejected_change_me(self):
        from pydantic import ValidationError
        from config import Settings
        with pytest.raises((ValidationError, ValueError)):
            Settings(jwt_secret_key="change-me-in-production")

    def test_invalid_jwt_algorithm_rejected(self):
        from pydantic import ValidationError
        from config import Settings
        with pytest.raises((ValidationError, ValueError)):
            Settings(jwt_algorithm="NONE")

    def test_d1_missing_in_production_raises(self):
        from pydantic import ValidationError
        from config import Settings
        with pytest.raises((ValidationError, ValueError)):
            Settings(
                environment="production",
                jwt_secret_key="a" * 64,
                cloudflare_account_id="",
                cloudflare_d1_database_id="",
                cloudflare_api_token="",
            )

    def test_dev_auto_generates_jwt_secret(self, capsys):
        """In dev, a missing JWT secret auto-generates a secure random one."""
        from config import Settings
        s = Settings(jwt_secret_key="", environment="development")
        assert s.jwt_secret_key != ""
        assert len(s.jwt_secret_key) >= 32
        captured = capsys.readouterr()
        assert "WARNING" in captured.out


# ─────────────────────────────────────────────────────────────────────────────
# 11. Error handling — no stack trace leakage
# ─────────────────────────────────────────────────────────────────────────────
class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_404_not_found(self, client):
        r = await client.get("/api/this-does-not-exist")
        assert r.status_code == 404
        text = r.text
        assert "Traceback" not in text
        assert 'File "' not in text

    @pytest.mark.asyncio
    async def test_validation_error_no_traceback(self, client):
        r = await client.post("/api/auth/register", json={"bad": "data"})
        assert r.status_code == 422
        assert "Traceback" not in r.text
        # Response must be valid JSON
        body = r.json()
        assert "detail" in body

    @pytest.mark.asyncio
    async def test_validation_error_response_is_clean_json(self, client):
        """The validation error response must be well-formed JSON with no Python exceptions."""
        r = await client.post("/api/auth/register", json={
            "email": "a@b.com",
            "password": "weak",
            "display_name": "User",
        })
        assert r.status_code == 422
        body = r.json()
        assert isinstance(body, dict)
        assert "detail" in body
