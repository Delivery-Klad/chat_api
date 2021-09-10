from fastapi import APIRouter
from typing import Optional
from database.Connect import db_connect
from Service.Logger import error_log

router = APIRouter(prefix="/alert", tags=["Alert"])


@router.get("/")
async def get_alert(groups: Optional[str] = None):
    if groups is None:
        return False
    groups = groups.split(",")
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT id FROM alerts WHERE id_group IN ({str(groups)[1:-1]})")
        try:
            res = cursor.fetchall()
            if not res:
                return False
            return res
        except TypeError:
            return False
    except Exception as e:
        error_log(e)
        return False
    finally:
        cursor.close()
        connect.close()


@router.post("/")
async def add_alert(group_id: str):
    connect, cursor = db_connect()
    try:
        cursor.execute("SELECT COUNT(*) FROM alerts")
        max_id = int(cursor.fetchone()[0]) + 1
        cursor.execute(f"INSERT INTO alerts VALUES ({max_id}, '{group_id}')")
        connect.commit()
        return True
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.get("/{user}")
async def get_alert_groups(user: int):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT group_id FROM members WHERE user_id={user}")
        return cursor.fetchall()
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()
