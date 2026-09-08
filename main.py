from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from models import Event


app = FastAPI(title="College Event Registration API")


# =========================
# Database Dependency
# =========================

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# =========================
# Pydantic Models
# =========================

class EventCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    date: str = Field(..., min_length=1, max_length=50)
    venue: str = Field(..., min_length=1, max_length=255)


class EventResponse(EventCreate):
    id: int

    class Config:
        from_attributes = True


# =========================
# Health Check
# =========================

@app.get("/health")
async def health_check():
    return {
        "status": "success",
        "message": "API is running"
    }


# =========================
# Create Event
# =========================

@app.post("/events", response_model=EventResponse, status_code=201)
async def create_event(
    event_data: EventCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        new_event = Event(
            name=event_data.name,
            description=event_data.description,
            date=event_data.date,
            venue=event_data.venue,
        )

        # Transactional database write
        async with db.begin():
            db.add(new_event)
            await db.flush()

        return new_event

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to create event"
        )


# =========================
# Get All Events
# =========================

@app.get("/events", response_model=list[EventResponse])
async def get_events(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Event))
    events = result.scalars().all()

    return events


# =========================
# Get Event by ID
# =========================

@app.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Event).where(Event.id == event_id)
    )

    event = result.scalar_one_or_none()

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    return event