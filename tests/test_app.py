import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activity_data():
    return {
        "Chess Club": {
            "description": "Play chess",
            "schedule": "Fridays",
            "max_participants": 12,
            "participants": ["existing@example.edu"],
        },
        "Art Club": {
            "description": "Make art",
            "schedule": "Mondays",
            "max_participants": 18,
            "participants": [],
        },
    }


@pytest.fixture
def client(monkeypatch, activity_data):
    monkeypatch.setattr(app_module, "activities", activity_data)
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data_without_caching(client, activity_data):
    # Arrange
    expected_activities = activity_data

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(client, activity_data):
    # Arrange
    email = "new@example.edu"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert activity_data["Chess Club"]["participants"] == [
        "existing@example.edu",
        email,
    ]


def test_signup_rejects_duplicate_without_changing_participants(client, activity_data):
    # Arrange
    email = "existing@example.edu"
    participants_before = activity_data["Chess Club"]["participants"].copy()

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert activity_data["Chess Club"]["participants"] == participants_before


def test_signup_returns_not_found_for_unknown_activity(client, activity_data):
    # Arrange
    participants_before = activity_data["Chess Club"]["participants"].copy()

    # Act
    response = client.post(
        "/Unknown Club/signup",
        params={"email": "new@example.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert activity_data["Chess Club"]["participants"] == participants_before


def test_unregister_removes_participant(client, activity_data):
    # Arrange
    email = "existing@example.edu"

    # Act
    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert activity_data["Chess Club"]["participants"] == []


def test_unregister_returns_not_found_for_unknown_activity(client, activity_data):
    # Arrange
    participants_before = activity_data["Chess Club"]["participants"].copy()

    # Act
    response = client.delete(
        "/activities/Unknown Club/participants",
        params={"email": "existing@example.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert activity_data["Chess Club"]["participants"] == participants_before


def test_unregister_returns_not_found_for_unregistered_participant(client, activity_data):
    # Arrange
    participants_before = activity_data["Chess Club"]["participants"].copy()

    # Act
    response = client.delete(
        "/activities/Chess Club/participants",
        params={"email": "missing@example.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert activity_data["Chess Club"]["participants"] == participants_before
