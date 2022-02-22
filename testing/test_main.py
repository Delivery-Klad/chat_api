from os import environ
from rsa import newkeys, decrypt, PrivateKey, PublicKey, encrypt
from rsa.transform import int2bytes, bytes2int
from fastapi.testclient import TestClient
from bcrypt import hashpw, gensalt

from main import app, startup_event

client = TestClient(app)
private_key = None
access_token = None
user_id, user_id_second = None, None
chat_id = None
pubkey = PublicKey(15049509030952083278666101600713569448824656007572906706479549891512407119, 65537)
privkey = PrivateKey(15049509030952083278666101600713569448824656007572906706479549891512407119, 65537,
                     917616584336855894861677250964362433854474492036872405600057505598524513,
                     673146469521390393905835854479266324211, 22356960501705281671981512243455029)
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
def test_user_register_deleted():
    response = client.post("/auth/", json={"login": "deleted",
                                           "password": hash_password("test_password"),
                                           "pubkey": "test_pubkey",
                                           "email": "test_email@rambler.ru"})
    assert response.status_code == 200
    assert response.json() is None


def test_user_register_wrong_nickname():
    response = client.post("/auth/", json={"login": "test_login_gr",
                                           "password": hash_password("test_password"),
                                           "pubkey": "test_pubkey",
                                           "email": "test_email@rambler.ru"})
    assert response.status_code == 200
    assert response.json() is None


def test_user_register():
    response = client.post("/auth/", json={"login": "test_login",
                                           "password": hash_password("test_password"),
                                           "pubkey": "test_pubkey",
                                           "email": "test_email@rambler.ru"})
    assert response.status_code == 200
    assert response.json() is True


def test_user_register_exists():
    response = client.post("/auth/", json={"login": "test_login",
                                           "password": hash_password("test_password"),
                                           "pubkey": "test_pubkey",
                                           "email": "test_email@rambler.ru"})
    assert response.status_code == 200
    assert response.json() is False


def test_deleted_user_login():
    global access_token
    response = client.get("/auth/?login=deleted&password=deleted_password")
    assert response.status_code == 200
    assert response.json() is False


def test_user_login_wrong_password():
    global access_token
    response = client.get("/auth/?login=test_login&password=wrong_password")
    assert response.status_code == 200
    assert response.json() is False


def test_user_login_not_found():
    global access_token
    response = client.get("/auth/?login=fake_login&password=fake_password")
    assert response.status_code == 200
    assert response.json() is None


def test_user_login():
    global access_token
    response = client.get("/auth/?login=test_login&password=test_password")
    assert response.status_code == 200
    access_token = response.json()
    assert response.json() == access_token


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
    assert {"id": user_id, "login": "test_login",
            "last_activity": response.json()[0]['last_activity']} in response.json()


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
    global privkey, pubkey
    (local_pubkey, local_privkey) = newkeys(1024)
    pubkey = local_pubkey
    privkey = local_privkey
    response = client.put("/user/", json={"pubkey": str(local_pubkey)[10:-1]},
                          headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is True


# endregion
# region Chats
def test_second_user_register():
    (test_pubkey, test_privkey) = newkeys(1024)
    test_pubkey = str(test_pubkey)[10:-1]
    response = client.post("/auth/", json={"login": "test_login_second",
                                           "password": hash_password("test_password"),
                                           "pubkey": test_pubkey,
                                           "email": "test_email_second@rambler.ru"})
    assert response.status_code == 200
    assert response.json() is True


def test_get_user_id_second():
    global user_id_second
    response = client.get("/user/?login=test_login_second&user_id=true")
    assert response.status_code == 200
    user_id_second = response.json()
    assert str(response.json()).isnumeric()


def test_create_chat_wrong_format():
    response = client.post("/chat/", json={"name": "wrong_name_format"},
                           headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is False


def test_create_chat():
    response = client.post("/chat/", json={"name": "test_chat_gr"},
                           headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is True


def test_create_chat_duplicate():
    response = client.post("/chat/", json={"name": "test_chat_gr"},
                           headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is None


def test_get_chat_id():
    global chat_id
    response = client.get("/chat/?chat_id=true&name=test_chat_gr")
    chat_id = response.json()
    assert response.status_code == 200
    assert response.json() == chat_id


def test_get_chat_name():
    response = client.get(f"/chat/?chat_name=true&id={chat_id}")
    assert response.status_code == 200
    assert response.json() == "test_chat_gr"


def test_get_all_chats_messages():
    response = client.put("/chat/?all=true", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    message = decrypt(int2bytes(response.json()[0]['message']), privkey)
    assert message.decode('utf-8') == f"Chat created id={chat_id}"
    json = {"user_id": chat_id, "username": "test_chat_gr", "message": response.json()[0]['message'], "read": 0}
    assert response.json()[0] == json


def test_get_chat_users():
    response = client.put(f"/chat/?chat_users=true&id={chat_id}",
                          headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() == [[user_id]]


def test_invite_chat_not_owner():
    response = client.patch("/chat/", json={"name": "some_fake_chat_gr", "user": "1"},
                            headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is False


def test_invite_chat_fake_user():
    response = client.patch("/chat/", json={"name": "test_chat_gr", "user": "-3"},
                            headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is False


def test_invite_chat():
    response = client.patch("/chat/", json={"name": "test_chat_gr", "user": f"{user_id_second}"},
                            headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is True


def test_invite_chat_duplicate():
    response = client.patch("/chat/", json={"name": "test_chat_gr", "user": f"{user_id_second}"},
                            headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is False


def test_get_chat_users_second():
    response = client.put(f"/chat/?chat_users=true&id={chat_id}",
                          headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() == [[user_id], [user_id_second]]


def test_kick_chat_not_owner():
    response = client.delete("/chat/", json={"name": "some_fake_chat_gr", "user": "1"},
                             headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is False


def test_kick_chat():
    response = client.delete("/chat/", json={"name": "test_chat_gr", "user": f"{user_id_second}"},
                             headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is True


# endregion
# region Alerts
def test_get_alert_groups():
    response = client.get(f"/alert/{user_id}/")
    assert response.status_code == 200
    assert response.json() == [[chat_id]]


def test_get_alert_none_group():
    response = client.get("/alert/")
    assert response.status_code == 200
    assert response.json() is False


def test_get_alert_empty():
    response = client.get(f"/alert/?groups=g0")
    assert response.status_code == 200
    assert response.json() is False


def test_create_alert_wrong_owner():
    response = client.post("/alert/?group_id=g0",
                           headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is False


def test_create_alert():
    response = client.post(f"/alert/?group_id={chat_id}",
                           headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is True


def test_get_alert():
    response = client.get(f"/alert/?groups={chat_id}")
    assert response.status_code == 200
    assert response.json() == [[response.json()[0][0]]]


def test_delete_alert_wrong_owner():
    response = client.delete("/alert/?group_id=g0",
                             headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is False


def test_delete_alert():
    response = client.delete(f"/alert/?group_id={chat_id}",
                             headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is True


# endregion
# region Messages
def test_get_self_message_empty():
    response = client.get(f"/messages/?chat_id={user_id}&is_chat=0&max_id=0",
                          headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json()['count'] == 0


def test_get_chat_message_empty():
    response = client.get(f"/messages/?chat_id={chat_id}&is_chat=1&max_id=0",
                          headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json()['count'] == 0


def test_send_message_self():
    response = client.post("/messages/",
                           json={"is_chat": False,
                                 "destination": user_id,
                                 "message": bytes2int(encrypt("self_message".encode('utf-8'), pubkey)),
                                 "message1": bytes2int(encrypt("self_message".encode('utf-8'), pubkey))},
                           headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200


def test_send_message_chat():
    response = client.post("/messages/",
                           json={"is_chat": True,
                                 "sender": chat_id,
                                 "destination": user_id,
                                 "message": bytes2int(encrypt("self_message".encode('utf-8'), pubkey))},
                           headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200


def test_get_self_message():
    response = client.get(f"/messages/?chat_id={user_id}&is_chat=0&max_id=0",
                          headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['item_0'] == {"date": response.json()['item_0']['date'],
                                         "from_id": "test_login", "to_id": f"{user_id}",
                                         "message": response.json()['item_0']['message'],
                                         "message1": response.json()['item_0']['message1'],
                                         "read": response.json()['item_0']['read']}


def test_get_chat_message():
    response = client.get(f"/messages/?chat_id={chat_id}&is_chat=1&max_id=0",
                          headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json()['count'] == 2
    assert response.json()['item_0'] == {"date": response.json()['item_0']['date'],
                                         "from_id": "Service", "to_id": f"{user_id}",
                                         "message": response.json()['item_0']['message'],
                                         "message1": response.json()['item_0']['message1'],
                                         "read": response.json()['item_0']['read']}


def test_send_message_to_other():
    response = client.post("/messages/",
                           json={"is_chat": False,
                                 "destination": user_id_second,
                                 "message": bytes2int(encrypt("self_message".encode('utf-8'), pubkey)),
                                 "message1": bytes2int(encrypt("self_message".encode('utf-8'), pubkey))},
                           headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200


def test_get_other_message():
    response = client.get(f"/messages/?chat_id={user_id_second}&is_chat=0&max_id=0",
                          headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json()['count'] == 1
    assert response.json()['item_0'] == {"date": response.json()['item_0']['date'],
                                         "from_id": "test_login", "to_id": f"{user_id_second}",
                                         "message": response.json()['item_0']['message'],
                                         "message1": response.json()['item_0']['message1'],
                                         "read": response.json()['item_0']['read']}


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
# region Delete
def test_user_login_to_delete():
    global access_token
    response = client.get("/auth/?login=test_login_second&password=test_password")
    assert response.status_code == 200
    access_token = response.json()
    assert response.json() == access_token


def test_send_message_to_deleted():
    response = client.post("/messages/", json={"is_chat": False,
                                               "destination": user_id,
                                               "message": 12345,
                                               "message1": 12345},
                           headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 500


def test_delete_second_user():
    response = client.delete("/user/", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json() is True


def test_clear_tests():
    from Service.Methods import db_connect
    connect, cursor = db_connect()
    cursor.execute(f"DELETE FROM members WHERE group_id='{chat_id}'")
    connect.commit()
    cursor.execute(f"DELETE FROM chats WHERE id='{chat_id}'")
    connect.commit()
    cursor.close()
    connect.close()
# endregion
# pytest --cov-report term-missing --cov=Routers
