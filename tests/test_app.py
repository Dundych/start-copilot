import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
import copy

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities

client = TestClient(app)

# Original activities data for resetting
ORIGINAL_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    }
}


@pytest.fixture
def reset_activities():
    """Reset activities to clean state before and after each test"""
    # Arrange: Reset to original state
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    
    yield
    
    # Cleanup
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, reset_activities):
        """Verify /activities endpoint returns all registered activities"""
        # Arrange: endpoint is ready
        
        # Act: fetch activities
        response = client.get("/activities")
        data = response.json()
        
        # Assert: response contains all activities
        assert response.status_code == 200
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_returns_correct_structure(self, reset_activities):
        """Verify activities have required fields"""
        # Arrange: endpoint is ready
        
        # Act: fetch activities
        response = client.get("/activities")
        data = response.json()
        
        # Assert: each activity has required fields
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_get_activities_shows_current_participants(self, reset_activities):
        """Verify activities show current participant list"""
        # Arrange: activities with known participants
        
        # Act: fetch activities
        response = client.get("/activities")
        data = response.json()
        
        # Assert: participants are correctly listed
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_student_success(self, reset_activities):
        """Verify new student can successfully sign up for an activity"""
        # Arrange: new student email and activity
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Act: sign up for activity
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert: signup succeeds and returns confirmation
        assert response.status_code == 200
        data = response.json()
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_signup_adds_to_participants_list(self, reset_activities):
        """Verify signup actually adds student to participants"""
        # Arrange: new student and activity
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Act: sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert: student is in participants list
        response = client.get("/activities")
        activities_data = response.json()
        assert email in activities_data[activity]["participants"]
    
    def test_signup_duplicate_fails(self, reset_activities):
        """Verify duplicate signup is rejected"""
        # Arrange: student already in Chess Club
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Act: attempt duplicate signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert: request fails with 400 and descriptive message
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity_fails(self, reset_activities):
        """Verify signup fails for non-existent activity"""
        # Arrange: invalid activity name
        email = "student@mergington.edu"
        activity = "Nonexistent Club"
        
        # Act: attempt signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert: request fails with 404
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_multiple_activities(self, reset_activities):
        """Verify student can sign up for multiple activities"""
        # Arrange: one student, multiple activities
        email = "multistudent@mergington.edu"
        
        # Act: sign up for two different activities
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        response2 = client.post(f"/activities/Gym Class/signup?email={email}")
        
        # Assert: both signups succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Assert: student appears in both activities
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Gym Class"]["participants"]
    
    def test_signup_with_special_characters_in_email(self, reset_activities):
        """Verify signup works with special characters in email"""
        # Arrange: email with special characters
        email = "student+test@mergington.edu"
        activity = "Chess Club"
        
        # Act: sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert: signup succeeds
        assert response.status_code == 200


class TestUnregisterEndpoint:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant_success(self, reset_activities):
        """Verify student can unregister from an activity"""
        # Arrange: student in Chess Club
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Act: unregister
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Assert: unregister succeeds
        assert response.status_code == 200
        data = response.json()
        assert email in data["message"]
    
    def test_unregister_removes_from_participants(self, reset_activities):
        """Verify unregister actually removes student from activity"""
        # Arrange: student in Chess Club
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Act: unregister
        client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Assert: student no longer in participants
        response = client.get("/activities")
        data = response.json()
        assert email not in data[activity]["participants"]
    
    def test_unregister_nonexistent_participant_fails(self, reset_activities):
        """Verify unregister fails for non-existent participant"""
        # Arrange: student not in any activity
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        # Act: attempt unregister
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Assert: request fails with 404
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Participant not found"
    
    def test_unregister_nonexistent_activity_fails(self, reset_activities):
        """Verify unregister fails for non-existent activity"""
        # Arrange: invalid activity
        email = "student@mergington.edu"
        activity = "Nonexistent Club"
        
        # Act: attempt unregister
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Assert: request fails with 404
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_then_signup_again(self, reset_activities):
        """Verify student can re-signup after unregistering"""
        # Arrange: new student and activity
        email = "returningstu@mergington.edu"
        activity = "Chess Club"
        
        # Act: sign up
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Act: unregister
        response2 = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response2.status_code == 200
        
        # Act: sign up again
        response3 = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert: re-signup succeeds
        assert response3.status_code == 200
        
        # Assert: student is registered
        response = client.get("/activities")
        data = response.json()
        assert email in data[activity]["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_index(self, reset_activities):
        """Verify root endpoint redirects to static index"""
        # Arrange: client ready
        
        # Act: access root endpoint without following redirects
        response = client.get("/", follow_redirects=False)
        
        # Assert: response is redirect to /static/index.html
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestIntegrationScenarios:
    """Integration tests for realistic workflows"""
    
    def test_full_signup_and_unregister_workflow(self, reset_activities):
        """Verify complete signup and unregister workflow"""
        # Arrange: setup test data
        email = "workflow@mergington.edu"
        activity = "Programming Class"
        
        # Act: sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert: signup successful
        assert signup_response.status_code == 200
        
        # Act: verify in list
        list_response = client.get("/activities")
        
        # Assert: student appears in activity
        assert email in list_response.json()[activity]["participants"]
        
        # Act: unregister
        unregister_response = client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Assert: unregister successful
        assert unregister_response.status_code == 200
        
        # Act: verify removed from list
        list_response = client.get("/activities")
        
        # Assert: student no longer in activity
        assert email not in list_response.json()[activity]["participants"]
    
    def test_multiple_students_same_activity(self, reset_activities):
        """Verify multiple students can join the same activity"""
        # Arrange: multiple students
        students = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        activity = "Chess Club"
        
        # Act: all students sign up
        for email in students:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            # Assert: each signup succeeds
            assert response.status_code == 200
        
        # Act: fetch activities
        response = client.get("/activities")
        data = response.json()
        
        # Assert: all students in participants list
        for email in students:
            assert email in data[activity]["participants"]
