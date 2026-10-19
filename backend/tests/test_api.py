
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import ask as ask_module
from app.db.session import get_db


def fake_db():
    yield object()


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ask_returns_agent_answer(monkeypatch):
    app.dependency_overrides[get_db] = fake_db

    def fake_answer_with_agent(db, question, snapshot_id):
        assert question == "How much did I spend?"
        assert snapshot_id == "sample_a"
        return "Test answer: ₹1,000."

    monkeypatch.setattr(
        ask_module,
        "answer_with_agent",
        fake_answer_with_agent,
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/ask",
            json={
                "question": "How much did I spend?",
                "snapshot_id": "sample_a",
            },
        )

        assert response.status_code == 200
        assert response.json()["answer"] == "Test answer: ₹1,000."
    finally:
        app.dependency_overrides.clear()


def test_ask_rejects_invalid_request():
    client = TestClient(app)

    response = client.post(
        "/ask",
        json={
            "question": "Hi",
            "snapshot_id": "sample_a",
        },
    )

    assert response.status_code == 422
