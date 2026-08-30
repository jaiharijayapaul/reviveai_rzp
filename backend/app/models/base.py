import uuid
from app.db.database import Base

def gen_uuid() -> str:
    return str(uuid.uuid4())
