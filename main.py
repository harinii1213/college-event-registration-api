from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="College Event Registration API")


# =========================
# Pydantic Models
# =========================

class EventCreate(BaseModel):
    name: str
    description: str
    date: str
    venue: str


class EventResponse(EventCreate):
    id: int


# =========================
# Temporary Data Storage
# =========================

events = []


# =========================
# Health Check
# =========================

@app.get("/health")
def health_check():
    return {
        "status": "success",
        "message": "API is running"
    }


# =========================
# Create Event
# =========================

@app.post("/events", response_model=EventResponse)
def create_event(event: EventCreate):
    new_event = EventResponse(
        id=len(events) + 1,
        **event.model_dump()
    )

    events.append(new_event)

    return new_event


# =========================
# Get All Events
# =========================

@app.get("/events", response_model=list[EventResponse])
def get_events():
    return events


# =========================
# Get Event by ID
# =========================

@app.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: int):

    for event in events:
        if event.id == event_id:
            return event

    raise HTTPException(
        status_code=404,
        detail="Event not found"
    )