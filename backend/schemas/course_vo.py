from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class CourseVO(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    startDate: datetime
    endDate: datetime
    hours: int
    studentCount: int = 0
    status: int  # 修改为整数
    is_public: bool = False  # 添加是否公开课字段
    semester: str
    createTime: datetime
    updateTime: datetime

    class Config:
        from_attributes = True

class TeacherInfoVO(BaseModel):
    id: str
    name: str
    avatar: str

class CourseDetailVO(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    startDate: datetime
    endDate: datetime
    hours: int
    studentCount: int = 0
    status: int  # 修改为整数
    is_public: bool = False  # 添加是否公开课字段
    semester: str
    createTime: datetime
    updateTime: datetime
    teacherInfo: TeacherInfoVO
    videoCount: int = 0
    materialCount: int = 0