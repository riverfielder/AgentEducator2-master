from uuid import UUID
from pydantic import BaseModel

class UserVO(BaseModel):
    id: UUID
    name: str
    role: str
    token: str
