from dotenv import load_dotenv
load_dotenv()

from app import create_app
from models import User

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='admin').first()
    print(f"User: {user}")
    if user:
        print(f"Password hash: {user.password_hash[:50]}...")
        print(f"Check password: {user.check_password('admin123')}")
        
        # Test set_password
        user.set_password('admin123')
        print(f"New hash: {user.password_hash[:50]}...")
        print(f"Check new password: {user.check_password('admin123')}")