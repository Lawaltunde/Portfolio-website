from flask_login import LoginManager, UserMixin
from flask import session

login_manager = LoginManager()

class User(UserMixin):
    def __init__(self, id, username, role='user'):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    user_details = session.get('user_details')
    if user_details and user_details.get('id') == user_id:
        return User(id=user_details['id'], username=user_details['username'], role=user_details['role'])
    return None