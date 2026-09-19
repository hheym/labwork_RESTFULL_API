import pytest
from fastapi.testclient import TestClient
import main
import models
from database import SessionLocal

client = TestClient(main.app)

@pytest.fixture(autouse=True)
def clean_database():
    db = SessionLocal()

    db.query(models.TaskDB).delete()
    db.query(models.ProjectDB).delete()

    db.commit()
    db.close()


def create_project():
    response = client.post(
        "/api/projects",
        json={
            "name": "Web Platform",
            "description": "Разработка веб-платформы",
            "deadline": "2026-12-20",
            "status": "planning"
        }
    )

    return response.json()["project"]


def test_project_crud():
    response = client.post(
        "/api/projects",
        json={
            "name": "Web Platform",
            "description": "Разработка веб-платформы",
            "deadline": "2026-12-20",
            "status": "planning"
        }
    )

    assert response.status_code == 200

    project = response.json()["project"]
    project_id = project["id"]

    assert project["name"] == "Web Platform"
    assert project["status"] == "planning"

    response = client.get("/api/projects")

    assert response.status_code == 200
    assert len(response.json()["list"]) == 1

    response = client.get(f"/api/projects/{project_id}")

    assert response.status_code == 200
    assert response.json()["project"]["id"] == project_id

    response = client.patch(
        f"/api/projects/{project_id}",
        json={
            "description": "Новая версия проекта",
            "status": "in_work"
        }
    )

    assert response.status_code == 200
    assert response.json()["project"]["description"] == "Новая версия проекта"
    assert response.json()["project"]["status"] == "in_work"

    response = client.delete(f"/api/projects/{project_id}")

    assert response.status_code == 202

    response = client.get(f"/api/projects/{project_id}")

    assert response.status_code == 404


def test_project_validation():
    response = client.post(
        "/api/projects",
        json={
            "name": "Web Platform",
            "description": "Test",
            "deadline": "2026-12-20",
            "status": "wrong_status"
        }
    )

    assert response.status_code == 400
    assert response.json()["status"] == 400


def test_project_required_field():
    response = client.post(
        "/api/projects",
        json={
            "description": "Test",
            "deadline": "2026-12-20",
            "status": "planning"
        }
    )

    assert response.status_code == 400
    assert response.json()["status"] == 400


def test_project_not_found():
    response = client.get("/api/projects/999999")

    assert response.status_code == 404


def test_task_crud():
    project = create_project()
    project_id = project["id"]

    response = client.post(
        "/api/tasks",
        json={
            "title": "Сделать backend",
            "description": "Реализовать REST API",
            "status": "planning",
            "project_id": project_id
        }
    )

    assert response.status_code == 200

    task = response.json()["task"]
    task_id = task["id"]

    assert task["title"] == "Сделать backend"
    assert task["project_id"] == project_id

    response = client.get("/api/tasks")

    assert response.status_code == 200
    assert len(response.json()["list"]) == 1

    response = client.get(f"/api/tasks/{task_id}")

    assert response.status_code == 200
    assert response.json()["task"]["id"] == task_id

    response = client.patch(
        f"/api/tasks/{task_id}",
        json={
            "description": "REST API почти готов",
            "status": "in_work"
        }
    )

    assert response.status_code == 200
    assert response.json()["task"]["description"] == "REST API почти готов"
    assert response.json()["task"]["status"] == "in_work"

    response = client.delete(f"/api/tasks/{task_id}")

    assert response.status_code == 202

    response = client.get(f"/api/tasks/{task_id}")

    assert response.status_code == 404


def test_task_project_not_found():
    response = client.post(
        "/api/tasks",
        json={
            "title": "Test task",
            "description": "Test",
            "status": "planning",
            "project_id": 999999
        }
    )

    assert response.status_code == 404

def test_task_validation():
    project = create_project()

    response = client.post(
        "/api/tasks",
        json={
            "title": "Test task",
            "description": "Test",
            "status": "wrong_status",
            "project_id": project["id"]
        }
    )

    assert response.status_code == 400
    assert response.json()["status"] == 400


def test_delete_project_deletes_tasks():
    project = create_project()
    project_id = project["id"]

    response = client.post(
        "/api/tasks",
        json={
            "title": "Сделать backend",
            "description": "REST API",
            "status": "planning",
            "project_id": project_id
        }
    )

    assert response.status_code == 200

    task_id = response.json()["task"]["id"]

    response = client.delete(f"/api/projects/{project_id}")

    assert response.status_code == 202

    response = client.get(f"/api/tasks/{task_id}")

    assert response.status_code == 404