from pydantic import BaseModel
from typing import Optional

class CourseCreateDTO(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    startDate: int  # 使用时间戳表示日期
    endDate: int    # 使用时间戳表示日期
    hours: int
    status: int  # 修改为整型: 0=upcoming, 1=active, 2=completed
    is_public: bool = False  # 新增字段：是否为公开课
    semester: str
        
class CourseEditDTO(CourseCreateDTO):
    pass
