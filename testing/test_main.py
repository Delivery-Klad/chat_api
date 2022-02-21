from os import environ
from fastapi.testclient import TestClient
from bcrypt import hashpw, gensalt
from main import app, startup_event

client = TestClient(app)
private_key = None
access_token = None
user_id = None
startup_event()


def hash_password(password):
    hashed_pass = hashpw(password.encode("utf-8"), gensalt())
    return str(hashed_pass)[2:-1]


# region Service
def test_service_awake():
    response = client.get("/service/")
    assert response.status_code == 200
    assert len(response.json().split(" ")) == 2


# endregion
# region Auth
def test_user_register():
    response = client.post("/auth/", json={"login": "test_login",
                                           "password": hash_password("test_password"),
                                           "pubkey": "test_pubkey",
                                           "email": "test_email@rambler.ru"})
    assert response.status_code == 200
    assert response.json() is True


def test_user_login():
    global access_token
    response = client.get("/auth/?login=test_login&password=test_password")
    assert response.status_code == 200
    access_token = response.json()
    assert response.json() == access_token


def test_get_random_users():
    response = client.get("/user/?random=true")
    assert response.status_code == 200
    assert {"id": response.json()[0]['id'],
            "login": response.json()[0]['login'],
            "last_activity": response.json()[0]['last_activity']} in response.json()


def test_get_user_id():
    global user_id
    response = client.get("/user/?login=test_login&user_id=true")
    assert response.status_code == 200
    user_id = response.json()
    assert str(response.json()).isnumeric()


def test_user_find():
    response = client.get("/user/?login=test_log&find=true")
    assert response.status_code == 200
    assert response.json() == [{"id": user_id, "login": "test_login",
                                "last_activity": response.json()[0]['last_activity']}]


def test_get_user_name():
    response = client.get(f"/user/?id={user_id}&name=true")
    assert response.status_code == 200
    assert response.json() == "test_login"


def test_get_user_pubkey():
    response = client.get(f"/user/?id={user_id}&pubkey=true")
    assert response.status_code == 200
    assert response.json() == "test_pubkey"


def test_get_user_groups():
    response = client.get(f"/user/?id={user_id}&groups=true")
    assert response.status_code == 200
    assert response.json() == []


def test_update_user_password():
    response = client.patch("/user/", json={"old_password": "test_password",
                                            "new_password": hash_password("new_test_password")},
                            headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is True


def test_update_user_password_wrong():
    response = client.patch("/user/", json={"old_password": "wrong_password",
                                            "new_password": hash_password("new_test_password")},
                            headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is False


def test_update_user_pubkey():
    response = client.put("/user/", json={"pubkey": "test_user_pubkey_new"},
                          headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is True


def test_refresh_token():
    global access_token
    response = client.patch("/auth/", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    access_token = response.json()
    assert response.json() == access_token


def test_service_hex_by_user():
    response = client.patch("/service/?hex_length=10",
                            headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is None


# endregion
# region Recovery
def test_send_recovery_code():
    response = client.get("/recovery/?login=test_login")
    assert response.status_code == 200
    assert response.json() is True


def test_validate_recovery_wrong_code():
    response = client.post("/recovery/", json={"code": 1234567,
                                               "login": "test_login",
                                               "password": hash_password("test_password")})
    assert response.json() is False


def test_validate_recovery_wrong_login():
    response = client.post("/recovery/", json={"code": 1234567,
                                               "login": "tester_login",
                                               "password": hash_password("test_password")})
    assert response.json() is False


def test_validate_recovery_code():
    from Routers.Recovery import recovery_codes
    code = recovery_codes[len(recovery_codes) - 1].split("_")
    response = client.post("/recovery/", json={"code": code[len(code) - 1],
                                               "login": "test_login",
                                               "password": hash_password("test_password")})
    assert response.json() is True


def test_send_recovery_code_wrong():
    response = client.get("/recovery/?login=tesdsfdfsfsdft_10gin")
    assert response.status_code == 200
    assert response.json() is None


# endregion
# region Users

# endregion
# region Chats

# endregion
# region Messages

# endregion
# region Files

# endregion
# region Delete user
def test_delete_user():
    response = client.delete("/user/", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is True


# endregion
# region Admin
def test_admin_login():
    global access_token
    response = client.get(f"/auth/?login={environ.get('key')}&password={environ.get('adm_psw')}")
    assert response.status_code == 200
    access_token = response.json()
    assert response.json() == access_token


def test_service_hex():
    response = client.patch("/service/?hex_length=10",
                            headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert len(response.json()) == 20

# endregion
# pytest --cov-report term-missing --cov=Routers
