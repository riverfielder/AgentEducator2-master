<template>
  <div class="code-training-container">
    <div class="header">
      <h2><i class="fas fa-code"></i> 智能代码实训与启发调试</h2>
      <el-button type="primary" @click="generateTask" :loading="loading">
        获取新任务 (知识点: 软件工程规范)
      </el-button>
    </div>

    <div class="content-wrapper">
      <div class="left-panel">
        <el-card class="task-card">
          <template #header>
            <div class="card-header">
              <span>当前实训任务</span>
            </div>
          </template>
          <div v-if="currentTask" class="task-content">
            <h3>{{ currentTask.title }}</h3>
            <div class="points">
              <el-tag v-for="tag in currentTask.knowledge_points" :key="tag" class="mx-1" type="success">
                {{ tag }}
              </el-tag>
            </div>
            <p>请在右侧修改代码，修复所有隐藏的逻辑漏洞以及优化命名/注释规范。</p>
            <el-alert title="提示" type="info" :description="currentTask.hints.join(' | ')" show-icon v-if="currentTask.hints && currentTask.hints.length" />
          </div>
          <el-empty v-else description="点击上方按钮获取训练任务" />
        </el-card>

        <el-card class="chat-card" v-if="currentTask">
          <template #header>
            <div class="card-header">
              <span>AI 导师启发 (提交次数: {{ attempts }}/3)</span>
            </div>
          </template>
          <div class="feedback-area" v-if="aiFeedback">
             <div class="status-badge">
               <el-tag :type="aiStatus === 'SUCCESS' ? 'success' : (aiStatus === 'MAX_TRIES_REACHED' ? 'danger' : 'warning')">
                 状态: {{ aiStatus === 'SUCCESS' ? '完美通过' : (aiStatus === 'MAX_TRIES_REACHED' ? '已给最终答案' : '尝试引导') }}
               </el-tag>
               <el-tag v-if="staticScore > 0" type="info">AST规范分: {{ staticScore }} / 100</el-tag>
             </div>
             <p class="mt-2">{{ aiFeedback }}</p>
             <div v-if="knowledgeLinks.length > 0" class="mt-2 text-sm text-blue-500">
                <strong>关联知识库：</strong>
                <ul>
                  <li v-for="link in knowledgeLinks" :key="link">《{{link}}》</li>
                </ul>
             </div>
          </div>
          <el-empty v-else description="提交代码后，AI大模型导师将给予启发式反馈" :image-size="60"/>
        </el-card>

        <el-card v-if="aiStatus === 'MAX_TRIES_REACHED'" class="mt-4">
             <template #header>
              <div class="card-header"><span class="text-red-500 ml-1"><i class="fas fa-exclamation-triangle"></i> 最终参考答案</span></div>
            </template>
            <pre class="bg-gray-100 p-3 rounded text-sm overflow-auto"><code>{{ currentTask.solution_code }}</code></pre>
        </el-card>
      </div>

      <div class="right-panel">
         <el-card class="editor-card h-full flex flex-col">
            <template #header>
              <div class="card-header flex justify-between items-center" style="display: flex; justify-content: space-between;">
                <span>代码编辑区</span>
                <el-button type="success" @click="submitCode" :loading="evaluating" :disabled="!currentTask || aiStatus === 'SUCCESS'">提交编译 & AI评审</el-button>
              </div>
            </template>
            <!-- A simple textarea instead of monaco for simplicity, but simulating code editor -->
            <el-input
                v-model="studentCode"
                type="textarea"
                :rows="20"
                placeholder="请在此输入或修改你的代码"
                class="font-mono"
            />
         </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { generateCodeTask, submitCodeReview } from '../api/index';

const loading = ref(false);
const evaluating = ref(false);

const currentTask = ref<any>(null);
const studentCode = ref('');
const attempts = ref(0);

const aiStatus = ref('');
const aiFeedback = ref('');
const knowledgeLinks = ref<string[]>([]);
const staticScore = ref(0);

const resetState = () => {
    studentCode.value = '';
    attempts.value = 0;
    aiStatus.value = '';
    aiFeedback.value = '';
    knowledgeLinks.value = [];
    staticScore.value = 0;
};

const generateTask = async () => {
    loading.value = true;
    try {
        resetState();
        const res = await generateCodeTask('软件测试与代码规范');
        if (res.data.code === 200 && res.data.data) {
            currentTask.value = res.data.data;
            studentCode.value = currentTask.value.bad_code;
            ElMessage.success('已获取新任务');
        } else {
            ElMessage.error(res.data.message || '获取失败');
        }
    } catch (e: any) {
        ElMessage.error(e.message || '网络错误');
    } finally {
        loading.value = false;
    }
};

const submitCode = async () => {
    if (!studentCode.value.trim()) {
        ElMessage.warning('代码不能为空');
        return;
    }
    
    attempts.value += 1;
    evaluating.value = true;
    try {
        const payload = {
            student_code: studentCode.value,
            task_info: currentTask.value,
            attempts: attempts.value,
            keyword: currentTask.value.knowledge_points.join(',')
        };
        const res = await submitCodeReview(payload);
        if (res.data.code === 200 && res.data.data) {
            const data = res.data.data;
            aiStatus.value = data.status;
            aiFeedback.value = data.feedback;
            knowledgeLinks.value = data.knowledge_links || [];
            staticScore.value = data.static_score || 0;
            
            if (aiStatus.value === 'SUCCESS') {
                ElMessage.success('恭喜！代码完全正确。');
            } else if (aiStatus.value === 'MAX_TRIES_REACHED') {
                ElMessage.warning('尝试次数已达上限，已提供答案演示！');
            }
        } else {
            ElMessage.error(res.data.message || '评审失败');
        }
    } catch (e: any) {
        ElMessage.error(e.message || '网络错误');
    } finally {
        evaluating.value = false;
    }
};
</script>

<style scoped>
.code-training-container {
    padding: 20px;
    height: 100vh;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
.header h2 {
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

.content-wrapper {
    display: flex;
    gap: 20px;
    flex: 1;
    height: calc(100% - 60px);
}

.left-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 15px;
    overflow-y: auto;
}

.right-panel {
    flex: 1.5;
    display: flex;
    flex-direction: column;
}

.points {
    margin: 10px 0;
    display: flex;
    gap: 8px;
}

.feedback-area {
    background-color: #f7f9fc;
    padding: 15px;
    border-radius: 6px;
    white-space: pre-wrap;
    line-height: 1.6;
}

.mt-2 { margin-top: 8px; }
.mt-4 { margin-top: 16px; }
.ml-1 { margin-left: 4px; }
.text-red-500 { color: #f56c6c; }
.text-blue-500 { color: #409eff; }
.text-sm { font-size: 14px; }
</style>
