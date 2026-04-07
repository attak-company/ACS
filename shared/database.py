# Shared module - Database connection
# Responsibility: Database connection configuration

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Initialize database
db = SQLAlchemy()

# Initialize login manager
login_manager = LoginManager()

def init_database(app):
    """Initialize database"""
    # Configure database - temporarily use SQLite for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///acs_dev.db'
    print("Using SQLite database (development mode)")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Set login view
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Load user"""
    from .models import User
    return User.query.get(int(user_id))
