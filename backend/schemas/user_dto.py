from pydantic import BaseModel, validator
# 在 backend/schemas/user_dto.py 文件中添加
from dataclasses import dataclass
from typing import Optional

@dataclass
class UserUpdateProfileDTO:
    username: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None

class UserLoginDTO(BaseModel):
    email: str
    password: str

class UserRegisterDTO(BaseModel):
    username: str
    email: str
    password: str
    role: str = "student"  # 默认为student角色
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = ["student", "teacher"]
        if v not in valid_roles:
            raise ValueError(f"角色必须是 {', '.join(valid_roles)} 中的一个")
        return v