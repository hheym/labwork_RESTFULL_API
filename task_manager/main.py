from datetime import date
from typing import Optional, Literal
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from database import DataBase, engine, SessionLocal
import models

DataBase.metadata.create_all(bind=engine)

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error = exc.errors()[0]

    field = error["loc"][-1]
    error_type = error["type"]

    if error_type == "missing":
        reason = f"Field '{field}' is required"

    elif field == "status":
        reason = "Field 'status' must be one of: planning, in_work, done"

    elif field == "deadline":
        reason = "Field 'deadline' must be a valid date"

    else:
        reason = error["msg"]

    return JSONResponse(
        status_code=400,
        content={
            "status": 400,
            "reason": reason
        }
    )

class Project(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    deadline: date
    status: Literal["planning", "in_work", "done"]

class ProjectUpdate(BaseModel):
    description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    deadline: Optional[date] = None
    status: Optional[Literal["planning", "in_work", "done"]] = None

class Task(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    status: Literal["planning", "in_work", "done"]
    project_id: int

class TaskUpdate(BaseModel):
    description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    status: Optional[Literal["planning", "in_work", "done"]] = None

@app.get("/")
def root():
    return {"message": "Task manager"}

@app.get("/api/projects")
def get_projects():
    db = SessionLocal()

    try:
        projects = db.query(models.ProjectDB).all()

        result = []

        for project in projects:
            result.append({
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "deadline": project.deadline,
                "status": project.status
            })

        return {"list": result}

    finally:
        db.close()


@app.get("/api/tasks")
def get_tasks():
    db = SessionLocal()

    try:
        tasks = db.query(models.TaskDB).all()

        result = []

        for task in tasks:
            result.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "project_id": task.project_id
            })

        return {"list": result}

    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "reason": str(error)
            }
        )

    finally:
        db.close()

@app.get("/api/projects/{project_id}")
def get_project(project_id: int):
    db = SessionLocal()

    try:
        project = db.get(models.ProjectDB, project_id)

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        return {
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "deadline": project.deadline,
                "status": project.status
            }
        }

    finally:
        db.close()

@app.get("/api/tasks/{task_id}")
def get_task(task_id: int):
    db = SessionLocal()

    try:
        task = db.get(models.TaskDB, task_id)

        if task is None:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

        return {
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "project_id": task.project_id
            }
        }

    except HTTPException:
        raise

    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "reason": str(error)
            }
        )

    finally:
        db.close()

@app.post("/api/projects")
def create_project(project: Project):
    db = SessionLocal()

    try:
        new_project = models.ProjectDB(
            name=project.name,
            description=project.description,
            deadline=project.deadline,
            status=project.status
        )

        db.add(new_project)
        db.commit()
        db.refresh(new_project)

        return {
            "project": {
                "id": new_project.id,
                "name": new_project.name,
                "description": new_project.description,
                "deadline": new_project.deadline,
                "status": new_project.status
            }
        }

    except Exception as error:
        db.rollback()

        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "reason": str(error)
            }
        )

    finally:
        db.close()

@app.post("/api/tasks")
def create_task(task: Task):
    db = SessionLocal()

    try:
        project = db.get(models.ProjectDB, task.project_id)

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        new_task = models.TaskDB(
            title=task.title,
            description=task.description,
            status=task.status,
            project_id=task.project_id
        )

        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        return {
            "task": {
                "id": new_task.id,
                "title": new_task.title,
                "description": new_task.description,
                "status": new_task.status,
                "project_id": new_task.project_id
            }
        }

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()

        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "reason": str(error)
            }
        )

    finally:
        db.close()

@app.delete("/api/projects/{project_id}", status_code=202)
def delete_project(project_id: int):
    db = SessionLocal()

    try:
        project = db.get(models.ProjectDB, project_id)

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        db.delete(project)
        db.commit()

        return {"message": "Project deleted"}

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()

        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "reason": str(error)
            }
        )

    finally:
        db.close()


@app.delete("/api/tasks/{task_id}", status_code=202)
def delete_task(task_id: int):
    db = SessionLocal()

    try:
        task = db.get(models.TaskDB, task_id)

        if task is None:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

        db.delete(task)
        db.commit()

        return {"message": "Task deleted"}

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()

        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "reason": str(error)
            }
        )

    finally:
        db.close()

@app.patch("/api/projects/{project_id}")
def update_project(project_id: int, project_update: ProjectUpdate):
    db = SessionLocal()

    try:
        project = db.get(models.ProjectDB, project_id)

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        if project_update.description is not None:
            project.description = project_update.description

        if project_update.deadline is not None:
            project.deadline = project_update.deadline

        if project_update.status is not None:
            project.status = project_update.status

        db.commit()
        db.refresh(project)

        return {
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "deadline": project.deadline,
                "status": project.status
            }
        }

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()

        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "reason": str(error)
            }
        )

    finally:
        db.close()

@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate):
    db = SessionLocal()

    try:
        task = db.get(models.TaskDB, task_id)

        if task is None:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

        if task_update.description is not None:
            task.description = task_update.description

        if task_update.status is not None:
            task.status = task_update.status

        db.commit()
        db.refresh(task)

        return {
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "project_id": task.project_id
            }
        }

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()

        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "reason": str(error)
            }
        )

    finally:
        db.close()