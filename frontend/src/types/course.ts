export interface TeacherInfo {
  id: string;
  name: string;
  avatar?: string | null;
}

export interface Course {
  id: string;
  thumbnail: string;
  title: string;
  duration: string;
  students: number;
  teacher: string;
  teacherInfo?: TeacherInfo;
  description: string;
  category: string[];      // 多分类
}