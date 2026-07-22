from sqlalchemy import Integer, String, DateTime, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from enum import Enum

from app.database.database import Base


class TaskStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"



class TaskModel(Base):
    __tablename__ = "tasks"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:Mapped[int] = mapped_column(Integer, nullable=False)
    title:Mapped[str] = mapped_column(String, nullable=False)
    description:Mapped[str] = mapped_column(String, nullable=True)
    due_date:Mapped[datetime] = mapped_column(DateTime)
    status:Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    google_event_id: Mapped[str] = mapped_column(String, nullable=True)
    created_date:Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_date:Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), server_onupdate=func.now())



class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    access_token: Mapped[str] = mapped_column(String, nullable=False)
    refresh_token: Mapped[str] = mapped_column(String, nullable=False)
    token_expiry: Mapped[datetime] = mapped_column(DateTime)
    calendar_id: Mapped[str] = mapped_column(String, nullable=True)
    created_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), server_onupdate=func.now())