# define database tables as python classes via ORM (SQLAlchemy)
# ORM translates your preferred programming language to SQL lines.
# allows interaction with the database using Python objects instead of writing raw SQL queries
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class LabType(Base):
    __tablename__ = "lab_types"  # tells object relational mapping what db table this model maps to

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    image = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    description = Column(Text)

class LabSession(Base):
    __tablename__ = "lab_sessions" 
    id = Column(Integer, primary_key=True)
    lab_type_id = Column(Integer, nullable=False)
    pod_name = Column(String(255))
    url = Column(String(255))
    status = Column(String(50), default="running")
    start_time = Column(DateTime, server_default=func.now())
    expiration_time = Column(DateTime)