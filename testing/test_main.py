from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
private_key = None
access_token = None


def hash_password(password):
    return password


def generate_keys():
    return


# region Auth
def test_user_register():
    response = client.post("/auth/", json={"login": "test_login",
                                           "password": hash_password("test_password"),
                                           "pubkey": generate_keys(),
                                           "email": "test_email@test.test"})
    assert response.status_code == 200
    assert response.json() == {"access_token": response.json()['access_token']}


def test_user_login():
    response = client.get("/auth/?login='test_login'&password=''test_password")
    assert response.status_code == 200
    assert response.json() == {"access_token": response.json()['access_token']}


def test_refresh_token():
    global access_token
    response = client.patch("/auth/", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() == {"access_token": response.json()['access_token']}


# endregion
# region Recovery
def test_send_recovery_code():
    response = client.get("/recovery/?login='test_login'")
    assert response.status_code == 200
    assert response.json() == {"Success": "Recovery code has been sent"}


def test_validate_recovery_code():
    response = client.post("/recovery/")
    assert response  # todo
# endregion
# region Users

# endregion
# region Chats

# endregion
# region Messages

# endregion
# region Files

# endregion
