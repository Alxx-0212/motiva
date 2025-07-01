import os
import uuid
import enum
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'users' 

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(Text, nullable=False)
    bio = Column(Text, nullable=True)
    
    # Store user's preferred timezone as IANA timezone identifier
    timezone = Column(String(50), nullable=False, default='UTC')
    
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', timezone='{self.timezone}')>"
    
class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TaskStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"

class Task(Base):
    __tablename__ = 'tasks'

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    task_name = Column(String(100), nullable=False)
    task_description = Column(Text, nullable=True)

    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
 
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    start_time_utc = Column(DateTime(timezone=True), nullable=False)
    end_time_utc = Column(DateTime(timezone=True), nullable=False)

    priority: Mapped[TaskPriority] = mapped_column(
        postgresql.ENUM(
            TaskPriority, 
            name="task_priority_enum",
            create_type=True 
        ),
        nullable=True,
    )

    status: Mapped[TaskPriority] = mapped_column(
        postgresql.ENUM(
            TaskStatus, 
            name="task_status_enum",
            create_type=True
        ),
        default=TaskStatus.ACTIVE  
    )
    
    # Store the original timezone for reference
    original_timezone = Column(String(50), nullable=True)
    
    # RFC 5545 RRULE string for repeats
    recurrence_rule = Column(Text, nullable=True) 

    user = relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"<Task(id={self.task_id}, name='{self.task_name}', start={self.start_time_utc}, end={self.end_time_utc}, user_id={self.user_id})>"

# if __name__ == "__main__":
#     DB_USER = os.getenv("DB_USER", "postgres")
#     DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
#     DB_HOST = os.getenv("DB_HOST", "localhost")
#     DB_PORT = os.getenv("DB_PORT", "1234")
#     DB_NAME = os.getenv("DB_NAME", "postgres") 

#     DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

#     engine = create_engine(DATABASE_URL)

#     Base.metadata.create_all(engine)
    