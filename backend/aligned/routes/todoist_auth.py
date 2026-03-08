"""Todoist account management routes — add, update, delete API keys."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from aligned.auth.dependencies import get_current_user_from_request, get_db_session
from aligned.models.external_account import ExternalAccount

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/todoist", tags=["todoist"])


@router.post("/add-account")
async def add_account(request: Request) -> dict[str, str]:
    """Add a new Todoist account with an API key."""
    user = await get_current_user_from_request(request)
    session = get_db_session(request)
    body = await request.json()

    email = body.get("todoist_email")
    api_key = body.get("api_key")

    if not email or not api_key:
        return JSONResponse(
            {"detail": "Both todoist_email and api_key are required."},
            status_code=400,
        )  # type: ignore[return-value]

    existing = await ExternalAccount.get_task_account(
        session, user_id=user.id, provider_name="todoist", task_user_email=email
    )
    if existing:
        return JSONResponse(
            {"detail": f"A Todoist account for {email} already exists."},
            status_code=409,
        )  # type: ignore[return-value]

    account = ExternalAccount(
        user_id=user.id,
        external_email=email,
        provider="todoist",
        api_key=api_key,
        use_for_tasks=True,
    )
    session.add(account)
    await session.flush()

    logger.info("Added Todoist account %s for user %s", email, user.id)
    return {"status": "ok", "message": f"Todoist account for {email} added."}


@router.post("/update-key")
async def update_key(request: Request) -> dict[str, str]:
    """Update the API key for an existing Todoist account."""
    user = await get_current_user_from_request(request)
    session = get_db_session(request)
    body = await request.json()

    email = body.get("todoist_email")
    api_key = body.get("api_key")

    if not email:
        return JSONResponse({"detail": "todoist_email is required."}, status_code=400)  # type: ignore[return-value]

    account = await ExternalAccount.get_task_account(
        session, user_id=user.id, provider_name="todoist", task_user_email=email
    )
    if not account:
        return JSONResponse(
            {"detail": f"Todoist account for {email} not found."},
            status_code=404,
        )  # type: ignore[return-value]

    account.api_key = api_key
    account.needs_reauth = False
    await session.flush()

    logger.info("Updated Todoist API key for %s, user %s", email, user.id)
    return {"status": "ok", "message": f"API key for {email} updated."}


@router.post("/delete-account")
async def delete_account(request: Request) -> dict[str, str]:
    """Delete a Todoist account."""
    user = await get_current_user_from_request(request)
    session = get_db_session(request)
    body = await request.json()

    email = body.get("todoist_email")
    if not email:
        return JSONResponse({"detail": "todoist_email is required."}, status_code=400)  # type: ignore[return-value]

    account = await ExternalAccount.get_task_account(
        session, user_id=user.id, provider_name="todoist", task_user_email=email
    )
    if not account:
        return JSONResponse(
            {"detail": f"Todoist account for {email} not found."},
            status_code=404,
        )  # type: ignore[return-value]

    await session.delete(account)
    await session.flush()

    logger.info("Deleted Todoist account %s for user %s", email, user.id)
    return {"status": "ok", "message": f"Todoist account for {email} deleted."}


@router.post("/test")
async def test_connection(request: Request) -> dict[str, object]:
    """Test a Todoist API key without saving it."""
    body = await request.json()
    api_key = body.get("api_key")

    if not api_key:
        return {"success": False, "message": "API key is required."}

    try:
        from todoist_api_python.api import TodoistAPI

        api = TodoistAPI(api_key)
        api.get_projects()
        return {"success": True, "message": "Connection successful."}
    except Exception:
        logger.exception("Todoist API key test failed")
        return {
            "success": False,
            "message": "Connection failed. Please check your API key.",
        }
