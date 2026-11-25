from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.deps import get_google_user
from app.database import get_db
from app.models import Task, User

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskIn(BaseModel):
    title: str
    description: str = ""
    due_date: datetime | None = None
    priority: str = "medium"
    estimated_minutes: int = 30
    status: str = "pending"


@router.get("")
def list_tasks(db: Session = Depends(get_db), user: User = Depends(get_google_user)):
    rows = (
        db.query(Task)
        .filter((Task.user_id == user.id) | (Task.user_id.is_(None)))
        .order_by(Task.status, Task.due_date.is_(None), Task.due_date)
        .all()
    )
    return {
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "priority": t.priority,
                "status": t.status,
                "estimated_minutes": t.estimated_minutes,
            }
            for t in rows
        ]
    }


@router.post("")
def create_task(
    body: TaskIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_google_user),
):
    t = Task(user_id=user.id, **body.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"id": t.id, "title": t.title}


@router.post("/{task_id}/toggle")
def toggle_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_google_user)):
    t = db.get(Task, task_id)
    if not t:
        raise HTTPException(404, "Task not found")
    t.status = "done" if t.status != "done" else "pending"
    db.commit()
    return {"id": t.id, "status": t.status}


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_google_user)):
    t = db.get(Task, task_id)
    if t:
        db.delete(t)
        db.commit()
    return {"ok": True}
