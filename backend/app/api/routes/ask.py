
import logging
import time
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.observability import log_event
from app.db.session import get_db
from app.schemas.ask import AskRequest, AskResponse
from app.services.agent_service import answer_with_agent

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ask", response_model=AskResponse)
def ask_finance_agent(
    request: AskRequest,
    db: Session = Depends(get_db),
):
    request_id = str(uuid4())
    started = time.perf_counter()

    log_event(
        "ask_request_started",
        request_id=request_id,
        snapshot_id=request.snapshot_id,
    )

    try:
        answer = answer_with_agent(
            db=db,
            question=request.question,
            snapshot_id=request.snapshot_id,
        )

        log_event(
            "ask_request_completed",
            request_id=request_id,
            snapshot_id=request.snapshot_id,
            status_code=200,
            duration_ms=round(
                (time.perf_counter() - started) * 1000, 2
            ),
        )

        return AskResponse(answer=answer)

    except ValueError as exc:
        log_event(
            "ask_request_failed",
            request_id=request_id,
            status_code=400,
            error_type=type(exc).__name__,
            duration_ms=round(
                (time.perf_counter() - started) * 1000, 2
            ),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except RuntimeError as exc:
        message = str(exc)

        if "GEMINI_API_KEY is missing" in message:
            status_code = 503
            detail = "The AI service is not configured."
        else:
            status_code = 502
            detail = "The AI agent could not complete the request."

        logger.error(
            "Agent request failed: request_id=%s error_type=%s",
            request_id,
            type(exc).__name__,
        )

        log_event(
            "ask_request_failed",
            request_id=request_id,
            status_code=status_code,
            error_type=type(exc).__name__,
            duration_ms=round(
                (time.perf_counter() - started) * 1000, 2
            ),
        )
        raise HTTPException(
            status_code=status_code,
            detail=detail,
        ) from exc

    except Exception as exc:
        logger.exception(
            "Unexpected agent error: request_id=%s", request_id
        )

        log_event(
            "ask_request_failed",
            request_id=request_id,
            status_code=500,
            error_type=type(exc).__name__,
            duration_ms=round(
                (time.perf_counter() - started) * 1000, 2
            ),
        )
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred.",
        ) from exc

