from fastapi import APIRouter, Query
from typing import List, Optional
from database.Connect import db_connect
from Service.Logger import error_log


router = APIRouter(prefix="/alert", tags=["Alert"])


@router.get("/")
async def get_alert(groups: Optional[List[str]] = Query(None)):
    print(groups)
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT id FROM alerts WHERE id IN ({str(groups)[1:-1]})")
        try:
            res = cursor.fetchone()[0]
            return True
        except TypeError:
            return False
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.post("/")
async def add_alert(group_id: str):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"INSERT INTO alert VALUES ({group_id})")
        return True
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()
