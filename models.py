from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    date: Mapped[str] = mapped_column(String(50))
    venue: Mapped[str] = mapped_column(String(255))

    registrations: Mapped[list["Registration"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )


class Registration(Base):
    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id"),
        nullable=False,
    )
    student_name: Mapped[str] = mapped_column(String(255))
    student_email: Mapped[str] = mapped_column(String(255))

    event: Mapped["Event"] = relationship(
        back_populates="registrations"
    )