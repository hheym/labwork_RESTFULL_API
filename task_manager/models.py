from sqlalchemy import Column, Integer, String, Date, ForeignKey
from database import DataBase

class ProjectDB(DataBase):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    deadline = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)

class TaskDB(DataBase):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )