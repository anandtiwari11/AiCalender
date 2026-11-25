from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Event, Task


def seed_if_empty(db: Session) -> None:
    if db.query(Event).count() > 0:
        return

    now = datetime.now().replace(second=0, microsecond=0)
    today = now.replace(hour=0, minute=0)

    def at(day_offset: int, hour: int, minute: int = 0) -> datetime:
        return today + timedelta(days=day_offset, hours=hour, minutes=minute)

    events = [
        Event(
            title="Standup with Engineering",
            description="Daily sync on sprint progress and blockers.",
            start_time=at(0, 9, 30),
            end_time=at(0, 10, 0),
            attendees="Priya, Rahul, Sam",
            category="meeting",
            location="Zoom",
            priority="medium",
            meeting_link="https://meet.example.com/standup",
            notes="Share yesterday's progress.",
        ),
        Event(
            title="Product Review",
            description="Review Q2 roadmap and feature priorities.",
            start_time=at(0, 11, 0),
            end_time=at(0, 12, 0),
            attendees="Ananya, Product Team",
            category="meeting",
            location="Conf Room A",
            priority="high",
            meeting_link="https://meet.example.com/product",
            notes="Bring latest metrics deck.",
        ),
        Event(
            title="Deep Work: Project Proposal",
            description="Focused writing block for the client proposal.",
            start_time=at(0, 13, 0),
            end_time=at(0, 14, 0),
            attendees="",
            category="focus",
            location="",
            priority="high",
            notes="Proposal due tomorrow.",
        ),
        Event(
            title="1:1 with Manager",
            description="Career check-in and priorities.",
            start_time=at(0, 15, 0),
            end_time=at(0, 15, 30),
            attendees="Neha",
            category="meeting",
            location="Zoom",
            priority="medium",
            meeting_link="https://meet.example.com/1on1",
        ),
        Event(
            title="Design Sync",
            description="Align on dashboard mockups.",
            start_time=at(0, 16, 0),
            end_time=at(0, 16, 45),
            attendees="Design Team",
            category="meeting",
            location="Figma",
            priority="medium",
            meeting_link="https://meet.example.com/design",
        ),
        Event(
            title="Internal Sync",
            description="Cross-team updates.",
            start_time=at(1, 10, 0),
            end_time=at(1, 10, 45),
            attendees="Ops, Growth",
            category="meeting",
            location="Zoom",
            priority="low",
        ),
        Event(
            title="Client Demo",
            description="Walk through Cal.ai prototype.",
            start_time=at(1, 14, 0),
            end_time=at(1, 15, 0),
            attendees="Client Stakeholders",
            category="important",
            location="Zoom",
            priority="high",
            meeting_link="https://meet.example.com/demo",
        ),
        Event(
            title="Gym",
            description="Evening workout.",
            start_time=at(1, 18, 0),
            end_time=at(1, 19, 0),
            category="personal",
            priority="low",
        ),
        Event(
            title="Sprint Planning",
            description="Plan next two-week sprint.",
            start_time=at(2, 11, 0),
            end_time=at(2, 12, 30),
            attendees="Engineering",
            category="meeting",
            location="Conf Room B",
            priority="high",
        ),
        Event(
            title="Deep Work: Spec Writing",
            description="Write technical design doc.",
            start_time=at(3, 9, 0),
            end_time=at(3, 11, 0),
            category="focus",
            priority="high",
        ),
        Event(
            title="Lunch with Rahul",
            description="Catch up and discuss referral pipeline.",
            start_time=at(3, 13, 0),
            end_time=at(3, 14, 0),
            attendees="Rahul",
            category="personal",
            location="Cafe downstairs",
            priority="medium",
        ),
        Event(
            title="Board Prep Call",
            description="Prep talking points for Friday board.",
            start_time=at(4, 10, 0),
            end_time=at(4, 11, 0),
            attendees="Founders",
            category="important",
            priority="high",
            meeting_link="https://meet.example.com/board",
        ),
        # Intentional overlap for demo
        Event(
            title="Vendor Intro Call",
            description="Overlaps with design sync — AI should flag this.",
            start_time=at(0, 16, 15),
            end_time=at(0, 16, 45),
            attendees="Vendor Team",
            category="meeting",
            priority="medium",
            meeting_link="https://meet.example.com/vendor",
        ),
    ]

    tasks = [
        Task(
            title="Finish project proposal draft",
            description="Due tomorrow — needs 90 minutes of focus.",
            due_date=at(1, 17, 0),
            priority="high",
            status="pending",
            estimated_minutes=90,
        ),
        Task(
            title="Review design mockups",
            description="Leave comments in Figma.",
            due_date=at(0, 18, 0),
            priority="medium",
            status="pending",
            estimated_minutes=45,
        ),
        Task(
            title="Send follow-up email to client",
            description="Summarize demo next steps.",
            due_date=at(2, 12, 0),
            priority="medium",
            status="pending",
            estimated_minutes=20,
        ),
        Task(
            title="Update hiring scorecard",
            description="Add SDE2 interview notes.",
            due_date=at(3, 17, 0),
            priority="low",
            status="pending",
            estimated_minutes=30,
        ),
        Task(
            title="Prepare board slides",
            description="Metrics + risks + asks.",
            due_date=at(4, 9, 0),
            priority="high",
            status="pending",
            estimated_minutes=120,
        ),
    ]

    db.add_all(events + tasks)
    db.commit()
