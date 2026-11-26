from datetime import date
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Health / probe endpoints
# ---------------------------------------------------------------------------

def test_health_check(client: TestClient):
    """Basic health check returns 200 and status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_liveness_probe(client: TestClient):
    """Liveness probe used by Kubernetes to decide if the container should restart."""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_probe(client: TestClient):
    """Readiness probe used by Kubernetes to decide if traffic should be routed here."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


# ---------------------------------------------------------------------------
# GET /api/tasks
# ---------------------------------------------------------------------------

def test_list_tasks_empty(client: TestClient):
    """Empty database returns an empty list, not a 404."""
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_returns_created_task(client: TestClient):
    """A task created via POST appears in the list."""
    client.post("/api/tasks", json={
        "intern_id": 1,
        "title": "Write documentation",
        "priority": "HIGH",
        "due_date": str(date(2026, 6, 1)),
    })
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Write documentation"


# ---------------------------------------------------------------------------
# GET /api/tasks/{id}
# ---------------------------------------------------------------------------

def test_get_task_not_found(client: TestClient):
    """Requesting a non-existent task returns 404."""
    response = client.get("/api/tasks/999")
    assert response.status_code == 404


def test_get_task_by_id(client: TestClient):
    """A task can be retrieved by its id."""
    created = client.post("/api/tasks", json={
        "intern_id": 1,
        "title": "Deploy to Kubernetes",
        "priority": "HIGH",
    }).json()

    response = client.get(f"/api/tasks/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Deploy to Kubernetes"


# ---------------------------------------------------------------------------
# POST /api/tasks
# ---------------------------------------------------------------------------

def test_create_task_returns_201(client: TestClient):
    """Creating a valid task returns HTTP 201 and the task body."""
    response = client.post("/api/tasks", json={
        "intern_id": 1,
        "title": "Set up ArgoCD",
        "priority": "MEDIUM",
        "due_date": str(date(2026, 5, 15)),
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Set up ArgoCD"
    assert data["priority"] == "MEDIUM"
    assert data["status"] == "PENDING"
    assert data["intern_id"] == 1


def test_create_task_invalid_priority_returns_422(client: TestClient):
    """An invalid priority value is rejected with HTTP 422 (validation error)."""
    response = client.post("/api/tasks", json={
        "intern_id": 1,
        "title": "Bad priority",
        "priority": "URGENT",  # not a valid value
    })
    assert response.status_code == 422


def test_create_task_missing_title_returns_422(client: TestClient):
    """A missing required field returns HTTP 422."""
    response = client.post("/api/tasks", json={
        "intern_id": 1,
        "priority": "LOW",
    })
    assert response.status_code == 422


def test_create_task_intern_not_found_returns_404(client: TestClient, mock_http_client):
    """
    When interns-api responds with 404 the endpoint should return 404 too.
    This validates the service-to-service guard before persisting the task.
    """
    _, mock_response = mock_http_client
    mock_response.status_code = 404  # simulate intern not found

    response = client.post("/api/tasks", json={
        "intern_id": 999,
        "title": "Orphan task",
        "priority": "LOW",
    })
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/tasks/{id}
# ---------------------------------------------------------------------------

def test_update_task(client: TestClient):
    """Updating an existing task returns the updated values."""
    created = client.post("/api/tasks", json={
        "intern_id": 1,
        "title": "Initial title",
        "priority": "LOW",
    }).json()

    response = client.put(f"/api/tasks/{created['id']}", json={
        "title": "Updated title",
        "priority": "HIGH",
        "status": "IN_PROGRESS",
        "due_date": str(date(2026, 12, 31)),
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated title"
    assert data["status"] == "IN_PROGRESS"
    assert data["priority"] == "HIGH"


def test_update_task_not_found(client: TestClient):
    """Updating a non-existent task returns 404."""
    response = client.put("/api/tasks/999", json={
        "title": "Ghost update",
        "priority": "LOW",
        "status": "PENDING",
    })
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/tasks/{id}
# ---------------------------------------------------------------------------

def test_delete_task_returns_204(client: TestClient):
    """Deleting an existing task returns HTTP 204 (no content)."""
    created = client.post("/api/tasks", json={
        "intern_id": 1,
        "title": "Task to delete",
        "priority": "LOW",
    }).json()

    response = client.delete(f"/api/tasks/{created['id']}")
    assert response.status_code == 204

    # Confirm it's gone
    assert client.get(f"/api/tasks/{created['id']}").status_code == 404


def test_delete_task_not_found(client: TestClient):
    """Deleting a non-existent task returns 404."""
    response = client.delete("/api/tasks/999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/tasks/intern/{intern_id}
# ---------------------------------------------------------------------------

def test_list_intern_tasks(client: TestClient):
    """Tasks are correctly filtered by intern id."""
    # Create two tasks for intern 1, one for intern 2
    for title in ("Task A", "Task B"):
        client.post("/api/tasks", json={"intern_id": 1, "title": title, "priority": "LOW"})
    client.post("/api/tasks", json={"intern_id": 2, "title": "Task C", "priority": "LOW"})

    response = client.get("/api/tasks/intern/1")
    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert "Task A" in titles
    assert "Task B" in titles
    assert "Task C" not in titles
