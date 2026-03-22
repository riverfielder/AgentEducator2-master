import { createRouter, createWebHistory } from 'vue-router'
import type { RouteLocationNormalized, NavigationGuardNext } from 'vue-router'
import Home from '../views/Home.vue'
import VideoPlayer from '../views/VideoPlayer.vue'
import CourseView from '../views/CourseView.vue'
import CourseHome from '../views/CourseHome.vue'
import Login from "../views/Login.vue";
import Register from "../views/Register.vue";
import TeacherHome from "../views/teacherViews/TeacherHome.vue";
import MaterialsManagement from "../views/teacherViews/MaterialsManagement.vue";
import CourseManagement from "../views/teacherViews/CourseAdmin.vue";
import UserProfile from "../views/UserProfile.vue";
// 已整合到PersonalizedRecommend.vue中
import Notebook from "../views/Notebook.vue"
import AIAssistant from "../views/AIAssistant.vue"
import StudentManagement from '../views/teacherViews/StudentManagement.vue';
import TaskMonitor from '../views/teacherViews/TaskMonitor.vue';
import PersonalizedRecommend from '../views/PersonalizedRecommend.vue'
import DynamicTraining from '../views/DynamicTraining.vue'
import Statistics from '../views/teacherViews/Statistics.vue';
import AllCourses from '../views/AllCourses.vue';
import TeacherLayout from '../layouts/TeacherLayout.vue';
// 导入课程视频管理组件
import CourseVideosManage from '../views/teacherViews/components/CourseVideosManage.vue';
// 导入新的课程详情管理组件
import CourseDetailManage from '../views/teacherViews/CourseDetailManage.vue';
// 导入缺少的组件或使用动态导入
const Assignments = () => import('../views/teacherViews/Assignments.vue')
const CreateAssignment = () => import('../views/teacherViews/CreateAssignment.vue')
import DocumentViewer from '@/views/DocumentViewer.vue'
import StudentAssignmentGradedDetail from '../views/StudentAssignmentGradedDetail.vue'
import StudentAssignmentDetail from '../views/StudentAssignmentDetail.vue'
import QuestionBank from '../views/teacherViews/QuestionBank.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home,
      meta: { layout: 'default' }
    },    {
      path: '/course/:courseId/video/:videoId',
      name: 'videoPlayer',
      component: VideoPlayer,
      meta: { layout: 'blank' }  // 修改为blank布局，没有侧边栏
    },
    {
      path: '/course/:courseId',
      name: 'courseHome',
      component: CourseHome,
      meta: { layout: 'default' }  // 使用默认布局，显示课程首页
    },
    {
      path: '/course/:courseId/redirect',
      name: 'courseView',
      component: () => import('../views/CourseView.vue'),
      meta: { layout: 'blank' }  // 保留旧的重定向页面作为备用
    },
    { 
      path: '/login', 
      component: Login,
      meta: { layout: 'blank' } 
    },
    { 
      path: '/register',
      component: Register,
      meta: { layout: 'blank' } 
    },
    { 
      path: '/teacherHome',
      component: TeacherHome,
      meta: { layout: 'teacher' }
    },
    { 
      path: '/materials', 
      name: 'MaterialsManagement',
      component: MaterialsManagement,
      meta: { layout: 'teacher' }
    },
    { 
      path: '/courses', 
      component: CourseManagement,
      meta: { layout: 'teacher' }
    },
    { 
      path: '/profile', 
      component: UserProfile,
      meta: { layout: 'default' }
    },
    {
      path: '/task-monitor',
      name: 'TaskMonitor',
      component: TaskMonitor,
      meta: { 
        requiresAuth: true,
        roles: ['teacher', 'admin'],
        layout: 'teacher'
      }
    },
    {
      path: '/create-assignment',
      name: 'createAssignment',
      component: CreateAssignment,
      meta: { 
        requiresAuth: true,
        roles: ['teacher'],
        layout: 'teacher'
      }
    },
    // 添加数据统计路由
    {
      path: '/statistics',
      name: 'Statistics',
      component: Statistics,
      meta: { 
        requiresAuth: true,
        roles: ['teacher', 'admin'],
        layout: 'teacher'
      }
    },
    // 添加缺少的路由
    {
      path: '/assignments',
      name: 'assignments',
      component: Assignments,
      meta: { 
        requiresAuth: true, 
        roles: ['teacher'], 
        layout: 'teacher' 
      }
    },
    // 教师智能助手路由
    {
      path: '/teacher-assistant',
      name: 'teacherAssistant',
      component: () => import('../views/teacherViews/TeacherAssistant.vue'),
      meta: { 
        requiresAuth: true, 
        roles: ['teacher'], 
        layout: 'teacher' 
      }
    },
    // 学生相关路由 - 学习进度路由重定向到个性化推荐页面
    { 
      path: '/learning-progress', 
      name: 'learningProgress', 
      redirect: '/personalized',
      meta: { layout: 'default' }
    },
    { 
      path: '/notebook', 
      name: 'notebook', 
      component: Notebook,
      meta: { layout: 'default' }
    },
    { 
      path: '/ai-assistant', 
      name: 'aiAssistant', 
      component: AIAssistant,
      meta: { layout: 'default' }
    },
    { 
      path: '/students',
      name: 'studentManagement',
      component: StudentManagement,
      meta: { layout: 'teacher' }
    },
    {
      path: '/CourseVideoManage/:id',
      name: 'courseVideosManage',
      component: CourseVideosManage,
      meta: { 
        requiresAuth: true, 
        roles: ['teacher'], 
        layout: 'teacher' 
      }
    },
    // 新的课程详情管理路由
    {
      path: '/course-detail-manage/:courseId',
      name: 'courseDetailManage',
      component: CourseDetailManage,
      meta: { 
        requiresAuth: true, 
        roles: ['teacher'], 
        layout: 'teacher' 
      }
    },    {
      path: '/all-courses',
      name: 'allCourses',
      component: AllCourses,
      meta: { layout: 'default' }
    },
    {
      path: '/personalized',
      name: 'personalized',
      component: PersonalizedRecommend,
      meta: { 
        layout: 'default',
        keepAlive: true  // 添加keep-alive支持
      }
    },
    {
      path: '/knowledge-map',
      name: 'KnowledgeMap',
      component: () => import('../views/KnowledgeMap.vue'),
      meta: {
        requiresAuth: true,
        title: '知识图谱',
        layout: 'default'
      }
    },
    {
      path: '/knowledge-point/:id',
      name: 'KnowledgePointDetail',
      component: () => import('../views/KnowledgePointDetail.vue'),
      meta: { requiresAuth: true, layout: 'default' }
    },
    // 添加教师端知识点详情路由
    {
      path: '/teacher-knowledge-detail/:id',
      name: 'TeacherKnowledgeDetail',
      component: () => import('../views/teacherViews/TeacherKnowledgeDetail.vue'),
      meta: { 
        requiresAuth: true,
        roles: ['teacher'],
        layout: 'teacher'
      }
    },
    // 移动端视频播放器路由
    {
      path: '/mobile/course/:courseId/video/:videoId',
      name: 'MobileVideoPlayer',
      component: () => import('../views/MobileVideoPlayer.vue'),
      meta: { 
        requiresAuth: true,
        layout: 'blank'
      }
    },
    // 学生端作业相关路由
    {
      path: '/student-assignments',
      name: 'studentAssignments',
      component: () => import('../views/StudentAssignmentList.vue'),
      meta: { layout: 'default' }
    },
    {
      path: '/student-assignments/:id/graded',
      name: 'studentAssignmentGradedDetail',
      component: StudentAssignmentGradedDetail,
      meta: { layout: 'default' }
    },
    {
      path: '/student-assignments/:id',
      name: 'studentAssignmentDetail',
      component: StudentAssignmentDetail,
      meta: { layout: 'default' }
    },
    {
      path: '/document/:documentId',
      name: 'DocumentViewer',
      component: DocumentViewer,
      meta: { requiresAuth: true, layout: 'blank' },
      props: true
    },
    {
      path: '/course/:courseId/document/:documentId',
      name: 'CourseDocumentViewer',
      component: DocumentViewer,
      meta: { requiresAuth: true, layout: 'blank' },
      props: true
    },
    // 批改作业路由
    {
      path: '/assignments/:id/mark',
      name: 'MarkAssignment',
      component: () => import('../views/teacherViews/MarkAssignment.vue'),
      meta: {
        requiresAuth: true,
        requiresTeacher: true,
        layout: 'teacher'
      }
    },
    {
      path: '/teacher-question-bank',
      name: 'teacherQuestionBank',
      component: QuestionBank,
      meta: {
        layout: 'teacher',
        requiresAuth: true,
        roles: ['teacher']      }
    },
    // 学生端题目详情页面
    {
      path: '/question/:id',
      name: 'questionDetail',
      component: () => import('../views/QuestionDetail.vue'),
      meta: { 
        layout: 'default',
        requiresAuth: false  // 暂时不需要认证，方便访问
      }
    },
    // 代码训练营
    {
      path: '/code-training',
      name: 'codeTraining',
      component: () => import('../views/CodeTrainingWorkstation.vue'),
      meta: { layout: 'default' }
    },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})

// 全局导航守卫，验证用户是否登录
router.beforeEach((to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
  const publicPages = ['/', '/login', '/register', '/learning-progress', '/notebook', '/ai-assistant'];
  const token = localStorage.getItem('wendao_token');

  const authRequired = !publicPages.includes(to.path);

  if (authRequired && !token) {
    return next('/login');
  }

  if ((to.path === '/login' || to.path === '/register') && token) {
    // 根据用户角色重定向到相应的首页
    const userRole = localStorage.getItem('wendao_user_role');
    if (userRole === 'teacher') {
      return next('/teacherHome');
    } else {
      return next('/');
    }
  }

  next();
});


export default router