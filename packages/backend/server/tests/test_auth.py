import json
from models.user import User

def test_register_and_login(client):
    """Test registering a new user and then logging in."""
    # Clear the user if it exists from a previous failed run
    User.query.filter_by(email='testuser@example.com').delete()

    # 1. Test user registration
    register_response = client.post('/api/auth/register', data=json.dumps({
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'password123'
    }), content_type='application/json')

    assert register_response.status_code == 201
    assert 'User registered successfully' in register_response.get_data(as_text=True)

    # 2. Test successful login
    login_response = client.post('/api/auth/login', data=json.dumps({
        'email': 'testuser@example.com',
        'password': 'password123'
    }), content_type='application/json')

    assert login_response.status_code == 200
    json_data = login_response.get_json()
    assert 'access_token' in json_data

    # 3. Test login with wrong password
    bad_login_response = client.post('/api/auth/login', data=json.dumps({
        'email': 'testuser@example.com',
        'password': 'wrongpassword'
    }), content_type='application/json')

    assert bad_login_response.status_code == 401
    assert 'Invalid credentials' in bad_login_response.get_data(as_text=True)
