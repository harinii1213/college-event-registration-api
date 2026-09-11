import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from models import Event
from services import event_service


# =========================
# Environment
# =========================

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY is not set")


# =========================
# App
# =========================

app = FastAPI(title="College Event Registration API")

security = HTTPBearer()


# =========================
# Database Dependency
# =========================

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# =========================
# Pydantic Models
# =========================

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class EventCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    date: str = Field(..., min_length=1, max_length=50)
    venue: str = Field(..., min_length=1, max_length=255)


class EventUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, min_length=1)
    date: str | None = Field(None, min_length=1, max_length=50)
    venue: str | None = Field(None, min_length=1, max_length=255)


class EventResponse(EventCreate):
    id: int
    owner_username: str

    class Config:
        from_attributes = True


# =========================
# Authentication
# =========================

def create_access_token(username: str):
    expire = datetime.now(timezone.utc) + timedelta(hours=1)

    payload = {
        "sub": username,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm="HS256",
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=["HS256"],
        )

        username = payload.get("sub")

        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )

        return username

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


# =========================
# Authorization Helper
# =========================

def verify_event_owner(event: Event, current_user: str):
    if event.owner_username != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this event",
        )


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
# Login
# =========================

@app.post("/auth/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):

    if (
        login_data.username != "admin"
        or login_data.password != "admin123"
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(login_data.username)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# =========================
# Create Event
# =========================

@app.post(
    "/events",
    response_model=EventResponse,
    status_code=201,
)
async def create_event(
    event_data: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        new_event = await event_service.create_event(
            db=db,
            name=event_data.name,
            description=event_data.description,
            date=event_data.date,
            venue=event_data.venue,
            owner_username=current_user,
        )

        await db.commit()
        await db.refresh(new_event)

        return new_event

    except Exception:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to create event",
        )


# =========================
# Search and Filter Events
# =========================

@app.get(
    "/events",
    response_model=list[EventResponse],
)
async def get_events(
    search: str | None = Query(
        default=None,
        min_length=1,
        description="Search event name or description",
    ),
    venue: str | None = Query(
        default=None,
        min_length=1,
        description="Filter events by venue",
    ),
    date: str | None = Query(
        default=None,
        min_length=1,
        description="Filter events by date",
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    events = await event_service.get_events(
        db=db,
        owner_username=current_user,
        search=search,
        venue=venue,
        date=date,
        skip=skip,
        limit=limit,
    )

    return events


# =========================
# Get Event by ID
# =========================

@app.get(
    "/events/{event_id}",
    response_model=EventResponse,
)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    event = await event_service.get_event(
        db=db,
        event_id=event_id,
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    verify_event_owner(event, current_user)

    return event


# =========================
# Update Event
# =========================

@app.patch(
    "/events/{event_id}",
    response_model=EventResponse,
)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    event = await event_service.get_event(
        db=db,
        event_id=event_id,
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    verify_event_owner(event, current_user)

    update_data = event_data.model_dump(
        exclude_unset=True
    )

    event = await event_service.update_event(
        db=db,
        event=event,
        update_data=update_data,
    )

    return event


# =========================
# Delete Event
# =========================

@app.delete("/events/{event_id}")
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    event = await event_service.get_event(
        db=db,
        event_id=event_id,
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    verify_event_owner(event, current_user)

    await event_service.delete_event(
        db=db,
        event=event,
    )

    return {
        "message": "Event deleted successfully"
    }