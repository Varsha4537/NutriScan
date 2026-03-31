from models.user import User, FoodScan
from models.database import db

class UserRepository:
    @staticmethod
    def get_by_username(username):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def create_user(username, password_hash, dietary_profile=None, name=None):
        user = User(username=username, password_hash=password_hash, 
                    dietary_profile=dietary_profile or [], name=name)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def get_by_id(user_id):
        return db.session.get(User, user_id)

    @staticmethod
    def save_dietary_profile(user_id, profile):
        user = UserRepository.get_by_id(user_id)
        if user:
            user.dietary_profile = profile
            db.session.commit()
            return True
        return False
