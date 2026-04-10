import os
import sys

from app import create_app
app = create_app()
from services.personalized_recommendation_service import PersonalizedRecommendationService
from routes.auth import get_current_user

# Get the recommended
with app.app_context():
    # Pick a random user id or the specific one 
    from models.user import User
    student = User.query.filter_by(role='student').first()
    if student:
        user_id = str(student.id)
        print(f"Testing for user {student.username} ({user_id})")
        service = PersonalizedRecommendationService()
        res = service.get_personalized_learning_path(user_id=user_id)
        print("RESULT:")
        import json
        print(json.dumps(res, indent=4, ensure_ascii=False))
    else:
        print("No student found.")
