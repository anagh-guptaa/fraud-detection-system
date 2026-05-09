from sqlalchemy.orm import Session
from backend.database.models import Transaction

def create_transaction(db: Session, transaction_data: dict):
    transaction=Transaction(user_id=transaction_data["user_id"],amount=transaction_data["amount"],merchant=transaction_data["merchant"],location=transaction_data["location"],device_id=transaction_data["device_id"],timestamp=transaction_data["timestamp"])
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

def get_all_transaction(db: Session):
    return db.query(Transaction).all()

def get_user_transactions(db: Session,user_id: int):
    return (db.query(Transaction).filter(Transaction.user_id==user_id).all())

