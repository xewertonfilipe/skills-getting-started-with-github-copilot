import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        # Arrange - dados já estão preparados pela fixture reset_activities
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        for activity in expected_activities:
            assert activity in data

    def test_get_activities_includes_participants(self, client, reset_activities):
        # Arrange
        expected_participant = "michael@mergington.edu"

        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        assert expected_participant in data["Chess Club"]["participants"]

    def test_get_activities_includes_activity_details(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"

        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        activity = data[activity_name]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={new_email}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert new_email in data["message"]

        # Verify participant was added
        activities = client.get("/activities").json()
        assert new_email in activities[activity_name]["participants"]

    def test_signup_duplicate_student_returns_error(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # já existe

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={existing_email}"
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_for_nonexistent_activity_returns_404(
        self, client, reset_activities
    ):
        # Arrange
        fake_activity = "Fake Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{fake_activity}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_increments_participant_count(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        initial_count = len(
            client.get("/activities").json()[activity_name]["participants"]
        )
        new_email = "another@mergington.edu"

        # Act
        client.post(f"/activities/{activity_name}/signup?email={new_email}")

        # Assert
        final_count = len(
            client.get("/activities").json()[activity_name]["participants"]
        )
        assert final_count == initial_count + 1

    def test_signup_multiple_users_to_different_activities(
        self, client, reset_activities
    ):
        # Arrange
        email1 = "user1@mergington.edu"
        email2 = "user2@mergington.edu"

        # Act
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email1}"
        )
        response2 = client.post(
            f"/activities/Programming Class/signup?email={email2}"
        )

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200

        activities = client.get("/activities").json()
        assert email1 in activities["Chess Club"]["participants"]
        assert email2 in activities["Programming Class"]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/remove endpoint"""

    def test_remove_participant_success(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove?email={email_to_remove}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert email_to_remove in data["message"]

        # Verify participant was removed
        activities = client.get("/activities").json()
        assert email_to_remove not in activities[activity_name]["participants"]

    def test_remove_nonexistent_participant_returns_404(
        self, client, reset_activities
    ):
        # Arrange
        activity_name = "Chess Club"
        nonexistent_email = "nonexistent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove?email={nonexistent_email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]

    def test_remove_from_nonexistent_activity_returns_404(
        self, client, reset_activities
    ):
        # Arrange
        fake_activity = "Fake Activity"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{fake_activity}/remove?email={email}"
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_remove_decrements_participant_count(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        initial_count = len(
            client.get("/activities").json()[activity_name]["participants"]
        )

        # Act
        client.delete(f"/activities/{activity_name}/remove?email={email_to_remove}")

        # Assert
        final_count = len(
            client.get("/activities").json()[activity_name]["participants"]
        )
        assert final_count == initial_count - 1

    def test_remove_all_participants_from_activity(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        participants = [
            "michael@mergington.edu",
            "daniel@mergington.edu"
        ]

        # Act
        for email in participants:
            client.delete(f"/activities/{activity_name}/remove?email={email}")

        # Assert
        activities = client.get("/activities").json()
        assert len(activities[activity_name]["participants"]) == 0


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_signup_and_remove_workflow(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        new_email = "workflow@mergington.edu"

        # Act - signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={new_email}"
        )

        # Assert signup
        assert signup_response.status_code == 200
        activities = client.get("/activities").json()
        assert new_email in activities[activity_name]["participants"]

        # Act - remove
        remove_response = client.delete(
            f"/activities/{activity_name}/remove?email={new_email}"
        )

        # Assert remove
        assert remove_response.status_code == 200
        activities = client.get("/activities").json()
        assert new_email not in activities[activity_name]["participants"]

    def test_multiple_signups_and_removals(self, client, reset_activities):
        # Arrange
        activity_name = "Gym Class"
        emails = ["user1@mergington.edu", "user2@mergington.edu", "user3@mergington.edu"]
        initial_count = len(
            client.get("/activities").json()[activity_name]["participants"]
        )

        # Act - signup all
        for email in emails:
            client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert all added
        activities = client.get("/activities").json()
        current_count = len(activities[activity_name]["participants"])
        assert current_count == initial_count + len(emails)

        # Act - remove some
        client.delete(f"/activities/{activity_name}/remove?email={emails[0]}")
        client.delete(f"/activities/{activity_name}/remove?email={emails[1]}")

        # Assert partial removal
        activities = client.get("/activities").json()
        final_count = len(activities[activity_name]["participants"])
        assert final_count == initial_count + 1
        assert emails[0] not in activities[activity_name]["participants"]
        assert emails[1] not in activities[activity_name]["participants"]
        assert emails[2] in activities[activity_name]["participants"]
