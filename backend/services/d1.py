"""
G Telepathy — Cloudflare D1 Client

Cloudflare D1 is accessed from our GCP VM via the D1 HTTP REST API.
All queries use parameterised SQL to prevent injection.

D1 API reference:
  POST https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{db_id}/query

Rate limits (Cloudflare free plan):
  - 100K read rows/day, 100K write rows/day
  - Paid plans have higher limits
"""
import logging
import httpx
from typing import Any
from config import settings

logger = logging.getLogger(__name__)

# D1 HTTP API endpoint
D1_API_URL = (
    "https://api.cloudflare.com/client/v4/accounts/"
    "{account_id}/d1/database/{database_id}/query"
)
TIMEOUT = httpx.Timeout(15.0, connect=5.0)


class D1Error(Exception):
    """Raised when D1 returns an API-level error."""


class D1NotConfiguredError(Exception):
    """Raised when D1 credentials are missing from config."""


def _check_config() -> None:
    if not all([
        settings.cloudflare_account_id,
        settings.cloudflare_d1_database_id,
        settings.cloudflare_api_token,
    ]):
        raise D1NotConfiguredError(
            "Cloudflare D1 is not configured. "
            "Set CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_D1_DATABASE_ID, and CLOUDFLARE_API_TOKEN."
        )


def _endpoint() -> str:
    return D1_API_URL.format(
        account_id=settings.cloudflare_account_id,
        database_id=settings.cloudflare_d1_database_id,
    )


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.cloudflare_api_token}",
        "Content-Type": "application/json",
    }


async def query(sql: str, params: list[Any] | None = None) -> list[dict]:
    """
    Execute a single SQL statement against D1 and return rows as a list of dicts.

    Args:
        sql:    Parameterised SQL — use ? as placeholder (SQLite syntax)
        params: Ordered list of parameter values matching ? placeholders

    Returns:
        List of row dicts (empty list for INSERT/UPDATE/DELETE)

    Raises:
        D1NotConfiguredError: if credentials are missing
        D1Error:              if D1 API returns an error
    """
    _check_config()

    payload: dict = {"sql": sql}
    if params:
        payload["params"] = params

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(_endpoint(), headers=_headers(), json=payload)
    except httpx.TimeoutException:
        raise D1Error("D1 query timed out.")
    except httpx.RequestError as e:
        raise D1Error(f"Network error reaching D1: {type(e).__name__}")

    if resp.status_code != 200:
        logger.error("D1 API HTTP error %d: %s", resp.status_code, resp.text[:300])
        raise D1Error(f"D1 API returned HTTP {resp.status_code}.")

    try:
        data = resp.json()
    except ValueError:
        raise D1Error("D1 API returned non-JSON response.")

    if not data.get("success"):
        errors = data.get("errors", [])
        logger.error("D1 query errors: %s", errors)
        raise D1Error(f"D1 query failed: {errors}")

    results = data.get("result", [])
    if not results:
        return []

    # D1 returns results as list of result objects; we typically use single statements
    first = results[0]
    return first.get("results", [])


async def execute(sql: str, params: list[Any] | None = None) -> dict:
    """
    Execute a write statement (INSERT / UPDATE / DELETE).
    Returns D1 meta: {last_row_id, rows_written, duration_ms}.
    """
    _check_config()

    payload: dict = {"sql": sql}
    if params:
        payload["params"] = params

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(_endpoint(), headers=_headers(), json=payload)
    except httpx.TimeoutException:
        raise D1Error("D1 write timed out.")
    except httpx.RequestError as e:
        raise D1Error(f"Network error reaching D1: {type(e).__name__}")

    if resp.status_code != 200:
        logger.error("D1 API HTTP error %d: %s", resp.status_code, resp.text[:300])
        raise D1Error(f"D1 API returned HTTP {resp.status_code}.")

    data = resp.json()
    if not data.get("success"):
        errors = data.get("errors", [])
        raise D1Error(f"D1 write failed: {errors}")

    results = data.get("result", [])
    meta = results[0].get("meta", {}) if results else {}
    return meta
