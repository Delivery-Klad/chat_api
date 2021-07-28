from database.Connect import db_connect
from database.Variables import admin_user, auth_handler
from Service.Logger import error_log
from fastapi import APIRouter, Depends
from rsa.transform import bytes2int

router = APIRouter(prefix="/database", tags=["Database"])


@router.get("/create")
async def create_tables(login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        if login == admin_user:
            cursor.execute('CREATE TABLE IF NOT EXISTS users(id BIGSERIAL NOT NULL UNIQUE PRIMARY KEY,'
                           'login TEXT NOT NULL UNIQUE,'
                           'password TEXT NOT NULL,'
                           'pubkey TEXT NOT NULL,'
                           'email TEXT NOT NULL,'
                           'last_activity TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS chats(id TEXT NOT NULL UNIQUE,'
                           'name TEXT NOT NULL UNIQUE,'
                           'owner BIGINT NOT NULL)')
            cursor.execute('CREATE TABLE IF NOT EXISTS messages(id BIGSERIAL NOT NULL UNIQUE PRIMARY KEY,'
                           'date TIMESTAMP NOT NULL,'
                           'from_id TEXT NOT NULL,'
                           'to_id TEXT NOT NULL,'
                           'message BYTEA NOT NULL,'
                           'message1 BYTEA,'
                           'read INTEGER NOT NULL)')
            cursor.execute('CREATE TABLE IF NOT EXISTS links(id BIGSERIAL NOT NULL UNIQUE PRIMARY KEY,'
                           'longlink TEXT NOT NULL)')
            connect.commit()
        return True
    except Exception as e:
        error_log(e)
        return e
    finally:
        cursor.close()
        connect.close()


@router.get("/check")
async def check_tables(table: str, login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        if table == "messages":
            json_dict = {}
            cursor.execute(f"SELECT * FROM {table}")
            res = cursor.fetchall()
            res.sort()
            json_dict.update({"count": len(res)})
            for i in range(len(res)):
                json_dict.update({f"item_{i}": {"id": res[i][0], "date": res[i][1], "from_id": res[i][2],
                                                "to_id": res[i][3], "message": bytes2int(res[i][4]),
                                                "message1": bytes2int(res[i][5]), "read": res[i][6]}})
            return json_dict
        if login == admin_user:
            cursor.execute(f"SELECT * FROM {table}")
            return cursor.fetchall()
        return False
    except Exception as e:
        error_log(e)
        return e
    finally:
        cursor.close()
        connect.close()


@router.delete("/drop")
async def drop_tables(table: str, login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        if login == admin_user:
            cursor.execute(f"DROP TABLE {table}")
            connect.commit()
        return True
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.get("/")
async def database(query: str, login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        if login == admin_user:
            if "select" in query.lower():
                return "Too use select operations /tables/check"
            cursor.execute(query)
            connect.commit()
            try:
                return cursor.fetchall()
            except Exception as e:
                print(e)
                return True
        return False
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()
