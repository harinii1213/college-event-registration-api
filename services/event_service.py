from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Event


async def create_event(
    db: AsyncSession,
    name: str,
    description: str,
    date: str,
    venue: str,
    owner_username: str,
):
    new_event = Event(
        name=name,
        description=description,
        date=date,
        venue=venue,
        owner_username=owner_username,
    )

    db.add(new_event)
    await db.flush()

    return new_event


async def get_events(
    db: AsyncSession,
    owner_username: str,
    search: str | None = None,
    venue: str | None = None,
    date: str | None = None,
    skip: int = 0,
    limit: int = 10,
):
    query = select(Event).where(
        Event.owner_username == owner_username
    )

    if search:
        search_pattern = f"%{search}%"

        query = query.where(
            or_(
                Event.name.ilike(search_pattern),
                Event.description.ilike(search_pattern),
            )
        )

    if venue:
        query = query.where(
            Event.venue.ilike(f"%{venue}%")
        )

    if date:
        query = query.where(
            Event.date == date
        )

    query = (
        query
        .order_by(Event.id)
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)

    return result.scalars().all()


async def get_event(
    db: AsyncSession,
    event_id: int,
):
    result = await db.execute(
        select(Event).where(Event.id == event_id)
    )

    return result.scalar_one_or_none()


async def update_event(
    db: AsyncSession,
    event: Event,
    update_data: dict,
):
    for field, value in update_data.items():
        setattr(event, field, value)

    await db.commit()
    await db.refresh(event)

    return event


async def delete_event(
    db: AsyncSession,
    event: Event,
):
    await db.delete(event)
    await db.commit()