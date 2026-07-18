from sqlalchemy import Integer, String, DateTime, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from enum import Enum

from app.database.database import Base


class TaskStatus(Enum):
    PENDING = "pending"
    NOTIFIED = "notified"
    EXPIRED = "expired"



class TaskModel(Base):
    __tablename__ = "tasks"

    id:Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:Mapped[int] = mapped_column(Integer, nullable=False)
    title:Mapped[str] = mapped_column(String, nullable=False)
    description:Mapped[str] = mapped_column(String, nullable=True)
    due_date:Mapped[datetime] = mapped_column(DateTime)
    status:Mapped[str] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    created_date:Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_date:Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), server_onupdate=func.now())