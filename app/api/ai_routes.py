import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai import apply_actions, daily_brief, get_ai_status, run_assistant
from app.auth.deps import get_google_user
from app.calendar.factory import get_calendar_provider
from app.database import get_db
from app.models import AIMessage, PendingProposal, User

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ChatIn(BaseModel):
    message: str


@router.get("/status")
def ai_status():
    return get_ai_status()


@router.get("/brief")
def brief(
    db: Session = Depends(get_db),
    user: User = Depends(get_google_user),
):
    provider = get_calendar_provider(db, user)
    return daily_brief(provider)


@router.get("/messages")
def messages(
    db: Session = Depends(get_db),
    user: User = Depends(get_google_user),
):
    rows = (
        db.query(AIMessage)
        .filter(AIMessage.user_id == user.id)
        .order_by(AIMessage.created_at.desc())
        .limit(40)
        .all()
    )
    rows = list(reversed(rows))
    return {
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in rows
        ]
    }


@router.post("/chat")
async def chat(
    body: ChatIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_google_user),
):
    provider = get_calendar_provider(db, user)
    db.add(AIMessage(user_id=user.id, role="user", content=body.message))
    proposal, mode = await run_assistant(provider, body.message)
    proposal_json = proposal.model_dump_json() if proposal.actions else ""
    db.add(
        AIMessage(
            user_id=user.id,
            role="assistant",
            content=proposal.reply + f"\n\n_({mode})_",
            proposal_json=proposal_json,
        )
    )
    proposal_id = None
    if proposal.actions:
        pending = PendingProposal(
            user_id=user.id,
            summary=proposal.summary,
            actions_json=json.dumps([a.model_dump() for a in proposal.actions]),
        )
        db.add(pending)
        db.flush()
        proposal_id = pending.id
    db.commit()
    return {
        "reply": proposal.reply,
        "summary": proposal.summary,
        "actions": [a.model_dump() for a in proposal.actions],
        "proposal_id": proposal_id,
        "mode": mode,
        "provider": provider.name,
    }


@router.get("/proposals")
def list_proposals(
    db: Session = Depends(get_db),
    user: User = Depends(get_google_user),
):
    rows = (
        db.query(PendingProposal)
        .filter(PendingProposal.user_id == user.id, PendingProposal.applied == False)  # noqa: E712
        .order_by(PendingProposal.created_at.desc())
        .limit(10)
        .all()
    )
    return {
        "proposals": [
            {
                "id": p.id,
                "summary": p.summary,
                "actions": json.loads(p.actions_json),
                "created_at": p.created_at.isoformat(),
            }
            for p in rows
        ]
    }


@router.post("/proposals/{proposal_id}/confirm")
def confirm_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_google_user),
):
    pending = (
        db.query(PendingProposal)
        .filter(PendingProposal.id == proposal_id, PendingProposal.user_id == user.id)
        .first()
    )
    if not pending or pending.applied:
        return {"ok": False, "error": "Proposal not found or already applied"}
    provider = get_calendar_provider(db, user)
    actions = json.loads(pending.actions_json)
    results = apply_actions(provider, actions)
    pending.applied = True
    db.add(
        AIMessage(
            user_id=user.id,
            role="assistant",
            content="Applied to calendar:\n• " + "\n• ".join(results or ["No changes"]),
        )
    )
    db.commit()
    return {"ok": True, "results": results, "provider": provider.name}


@router.post("/proposals/{proposal_id}/dismiss")
def dismiss_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_google_user),
):
    pending = (
        db.query(PendingProposal)
        .filter(PendingProposal.id == proposal_id, PendingProposal.user_id == user.id)
        .first()
    )
    if pending:
        pending.applied = True
        db.add(
            AIMessage(
                user_id=user.id,
                role="assistant",
                content="Proposal dismissed. No calendar changes made.",
            )
        )
        db.commit()
    return {"ok": True}
