from sqlalchemy.orm import Session
import database.models as db_models


def some_func(db: Session):
    db.execute(f"")
    db.commit()
