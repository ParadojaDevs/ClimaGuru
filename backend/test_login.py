from dotenv import load_dotenv
load_dotenv()

from app import create_app

app = create_app()
with app.test_client() as client:
    response = client.post('/login', json={'username': 'admin', 'password': 'admin123'})
    print('Status:', response.status_code)
    print('Response:', response.get_json())