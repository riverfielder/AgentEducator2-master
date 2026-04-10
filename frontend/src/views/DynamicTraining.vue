<template>
  <div class="dynamic-training-container">
    <div class="header">
      <h2>针对性薄弱点训练: {{ keyword }}</h2>
      <el-button @click="router.back()">返回</el-button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-box">
      <el-icon class="is-loading"><Loading /></el-icon>
      <p>AI正在为您量身定制薄弱点训练题，请稍候...</p>
    </div>

    <!-- 答题区域 -->
    <div v-else-if="questions.length > 0" class="quiz-box">
      <div class="question-nav">
        题目导航：
        <el-button 
          v-for="(q, idx) in questions" 
          :key="idx" 
          :type="currentIndex === idx ? 'primary' : (answers[idx] !== undefined ? 'success' : 'default')"
          @click="currentIndex = idx"
          circle
        >{{ idx + 1 }}</el-button>
      </div>

      <div class="question-content">
        <h3>第 {{ currentIndex + 1 }} 题 ({{ getQuestionTypeName(currentQuestion.type) }})</h3>
        <p class="q-text">{{ currentQuestion.content }}</p>

        <!-- 单选/多选/填空 -->
        <div v-if="currentQuestion.type === 'single'">
          <el-radio-group v-model="answers[currentIndex]" class="opt-group">
            <el-radio v-for="(opt, oIdx) in currentQuestion.options" :key="oIdx" :value="opt.substring(0,1)">
              {{ opt }}
            </el-radio>
          </el-radio-group>
        </div>
        <div v-else-if="currentQuestion.type === 'multiple'">
          <el-checkbox-group v-model="answers[currentIndex]" class="opt-group">
            <el-checkbox v-for="(opt, oIdx) in currentQuestion.options" :key="oIdx" :value="opt.substring(0,1)">
              {{ opt }}
            </el-checkbox>
          </el-checkbox-group>
        </div>
        <div v-else-if="currentQuestion.type === 'blank'">
          <el-input v-model="answers[currentIndex]" placeholder="请输入答案"></el-input>
        </div>

        <!-- 主观题/代码题 -->
        <div v-else-if="currentQuestion.type === 'essay'" class="code-editor-area">
          <p class="hint">请在下方输入代码 (可使用 ```python 包裹)</p>
          <el-input 
            type="textarea" 
            :rows="12" 
            v-model="answers[currentIndex]" 
            placeholder="def solution():&#10;    pass"
            style="font-family: monospace;"
          ></el-input>
        </div>

        <div class="actions">
          <el-button @click="prevQuestion" :disabled="currentIndex === 0">上一题</el-button>
          <el-button @click="nextQuestion" v-if="currentIndex < questions.length - 1">下一题</el-button>
          <el-button type="success" @click="submitCurrent" v-if="!results[currentIndex]" :loading="grading">提交阅卷</el-button>
        </div>

        <!-- 评卷结果 -->
        <div v-if="results[currentIndex]" class="result-box" :class="{ 'is-correct': results[currentIndex].score > 0 }">
          <h4>批改结果：得 {{ results[currentIndex].score }} 分 (满分{{ currentQuestion.max_score }})</h4>
          <p><strong>反馈：</strong>{{ results[currentIndex].feedback }}</p>
          <p v-if="currentQuestion.explanation"><strong>解析：</strong>{{ currentQuestion.explanation }}</p>
          <p v-if="currentQuestion.reference"><strong>参考：</strong><pre>{{ currentQuestion.reference }}</pre></p>
        </div>
      </div>
    </div>
    
    <div v-else class="error-box">
      <el-empty description="未能生成题目，请重试"></el-empty>
      <el-button type="primary" @click="generateTraining">重新生成</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const keyword = ref(route.query.keyword as string || '基础知识')
const loading = ref(false)
const grading = ref(false)

const questions = ref<any[]>([])
const currentIndex = ref(0)
const answers = ref<any>({})
const results = ref<any>({})

const currentQuestion = computed(() => {
  return questions.value[currentIndex.value] || {}
})

const getQuestionTypeName = (type: string) => {
  const map: Record<string, string> = {
    'single': '单选题',
    'multiple': '多选题',
    'blank': '填空题',
    'essay': '代码主观题'
  }
  return map[type] || type
}

const generateTraining = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('wendao_token') || sessionStorage.getItem('wendao_token')
    const res = await axios.post('/api/training/generate', {
      keyword: keyword.value,
      count: 3
    }, {
      headers: { Authorization: `Bearer ${token}` }
    })
    
    if (res.data.code === 200) {
      let resultData = res.data.data;
      if (typeof resultData === 'string') {
        try {
          const match = resultData.match(/\[[\s\S]*\]/);
          if (match) {
            resultData = JSON.parse(match[0]);
          } else {
            resultData = JSON.parse(resultData);
          }
        } catch (e) {
          console.error('Failed to parse JSON string:', e);
        }
      }
      questions.value = resultData
      answers.value = {}
      results.value = {}
      currentIndex.value = 0
    } else {
      ElMessage.error(res.data.message || '生成失败')
    }
  } catch (e: any) {
    ElMessage.error('请求生成试卷异常' + e.message)
  } finally {
    loading.value = false
  }
}

const prevQuestion = () => {
  if (currentIndex.value > 0) currentIndex.value--
}

const nextQuestion = () => {
  if (currentIndex.value < questions.value.length - 1) currentIndex.value++
}

const submitCurrent = async () => {
  const ans = answers.value[currentIndex.value]
  if (!ans || (Array.isArray(ans) && ans.length === 0)) {
    ElMessage.warning('请先作答再提交！')
    return
  }

  grading.value = true
  try {
    const token = localStorage.getItem('wendao_token') || sessionStorage.getItem('wendao_token')
    const res = await axios.post('/api/training/grade', {
      keyword: keyword.value,
      question: currentQuestion.value,
      student_answer: ans
    }, {
      headers: { Authorization: `Bearer ${token}` }
    })

    if (res.data.code === 200) {
      results.value[currentIndex.value] = res.data.data
      ElMessage.success('批阅完成')
    } else {
      ElMessage.error(res.data.message || '批改失败')
    }
  } catch (e: any) {
    ElMessage.error('批改请求异常: ' + e.message)
  } finally {
    grading.value = false
  }
}

onMounted(() => {
  generateTraining()
})
</script>

<style scoped>
.dynamic-training-container {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
  background: #f9f9f9;
  min-height: 80vh;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.loading-box {
  text-align: center;
  margin-top: 100px;
  font-size: 18px;
  color: #666;
}
.is-loading {
  font-size: 40px;
  color: #409EFF;
  margin-bottom: 15px;
}
.quiz-box {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}
.question-nav {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}
.q-text {
  font-size: 16px;
  line-height: 1.6;
  margin-bottom: 20px;
}
.opt-group {
  display: flex;
  flex-direction: column;
  gap: 15px;
}
.code-editor-area {
  margin-bottom: 20px;
}
.hint {
  font-size: 13px;
  color: #999;
}
.actions {
  margin-top: 30px;
  display: flex;
  gap: 15px;
}
.result-box {
  margin-top: 30px;
  padding: 20px;
  background: #fdf6ec;
  border-radius: 4px;
  border-left: 5px solid #e6a23c;
}
.result-box.is-correct {
  background: #f0f9eb;
  border-left-color: #67c23a;
}
pre {
  background: #282c34;
  color: #abb2bf;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}
</style>