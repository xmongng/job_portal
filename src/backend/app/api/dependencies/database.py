from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.persistence.database import get_db_session

# Route chỉ cần khai báo tham số kiểu DatabaseSession; FastAPI sẽ tự mở/đóng Session.
DatabaseSession = Annotated[Session, Depends(get_db_session)]
