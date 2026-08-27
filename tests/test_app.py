"""Backend API tests for the Mergington High School application."""

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index():
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_static_index_is_available():
    # Arrange
    static_index_path = "/static/index.html"

    # Act
    response = client.get(static_index_path)

    # Assert
    assert response.status_code == 200
    assert "Mergington High School" in response.text


def test_get_activities_returns_activity_details():
    # Arrange
    expected_activity = activities["Chess Club"]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"] == expected_activity
    assert isinstance(response.json()["Chess Club"]["participants"], list)
    assert "max_participants" in response.json()["Chess Club"]


def test_signup_adds_participant_to_activity():
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in client.get("/activities").json()[activity_name]["participants"]


def test_signup_rejects_duplicate_participant():
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


@pytest.mark.parametrize(
    "activity_name,email,expected_status,expected_detail",
    [
        ("Unknown Club", "student@mergington.edu", 404, "Activity not found"),
        ("Chess Club", None, 422, None),
    ],
)
def test_signup_rejects_invalid_requests(
    activity_name, email, expected_status, expected_detail
):
    # Arrange
    request_params = {} if email is None else {"email": email}

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params=request_params
    )

    # Assert
    assert response.status_code == expected_status
    if expected_detail:
        assert response.json()["detail"] == expected_detail


def test_unregister_removes_participant_from_activity():
    # Arrange
    activity_name = "Programming Class"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in client.get("/activities").json()[activity_name]["participants"]


def test_unregister_rejects_missing_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "not.signed.up@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


@pytest.mark.parametrize(
    "activity_name,email,expected_status,expected_detail",
    [
        ("Unknown Club", "student@mergington.edu", 404, "Activity not found"),
        ("Chess Club", None, 422, None),
    ],
)
def test_unregister_rejects_invalid_requests(
    activity_name, email, expected_status, expected_detail
):
    # Arrange
    request_params = {} if email is None else {"email": email}

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup", params=request_params
    )

    # Assert
    assert response.status_code == expected_status
    if expected_detail:
        assert response.json()["detail"] == expected_detail
