<template>
  <div class="code-training-container">
    <div class="header">
      <h2><i class="fas fa-code"></i> 智能代码实训与启发调试</h2>
      <div class="header-buttons">
        <el-button type="primary" @click="generateTask('debug')" :loading="loadingDebug" :disabled="loadingRefactor">
          <i class="fas fa-bug" v-if="!loadingDebug"></i> 获取 Debug 专项题
        </el-button>
        <el-button type="warning" @click="generateTask('refactor')" :loading="loadingRefactor" :disabled="loadingDebug">
          <i class="fas fa-broom" v-if="!loadingRefactor"></i> 获取代码质量重构题
        </el-button>
      </div>
    </div>

    <div class="content-wrapper">
      <div class="left-panel">
        <el-card class="task-card" :class="{'debug-card': currentTaskType === 'debug', 'refactor-card': currentTaskType === 'refactor'}">
          <template #header>
            <div class="card-header">
              <span>当前实训任务</span>
              <el-tag v-if="currentTaskType" :type="currentTaskType === 'debug' ? 'danger' : 'warning'" size="small" effect="dark">
                {{ currentTaskType === 'debug' ? 'Debug专项' : '代码质量重构' }}
              </el-tag>
            </div>
          </template>
          <div v-if="currentTask" class="task-content">
            <h3>{{ currentTask.title }}</h3>
            <div class="points">
              <el-tag v-for="tag in currentTask.knowledge_points" :key="tag" class="mx-1" type="success">
                {{ tag }}
              </el-tag>
              <el-tag v-if="currentTaskType === 'debug'" type="danger" class="mx-1">逻辑Bug修复</el-tag>
              <el-tag v-else type="warning" class="mx-1">列未关闭引论</el-tag>
            </div>
            <p v-if="currentTaskType === 'debug'">
              请在右侧修改代码，修复所有隐藏的逻辑漏洞以及优化命名/注释规范。
            </p>
            <p v-else>
              请在右侧重构代码，解决代码冗余、命名不规范、高耦合等代码质量问题。
            </p>
            <el-alert title="提示" type="info" :description="currentTask.hints.join(' | ')" show-icon v-if="currentTask.hints && currentTask.hints.length" :closable="true" />
          </div>
          <el-empty v-else description="点击上方按钮获取训练任务" />
        </el-card>

        <el-card class="chat-card" v-if="currentTask">
          <template #header>
            <div class="card-header">
              <span>AI 导师启发 (提交次数: {{ attempts }}/5)</span>
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
                <div style="display: flex; gap: 8px;">
                  <el-button type="info" @click="runCode" :loading="running" :disabled="!currentTask">
                    <i class="fas fa-play" v-if="!running"></i> 运行代码
                  </el-button>
                  <el-button type="success" @click="submitCode" :loading="evaluating" :disabled="!currentTask || aiStatus === 'SUCCESS'">
                    提交编译 &amp; AI评审
                  </el-button>
                </div>
              </div>
            </template>
            <el-input
                v-model="studentCode"
                type="textarea"
                :rows="15"
                placeholder="请在此输入或修改你的代码"
                class="font-mono"
            />
            <div v-if="runOutput" class="run-output">
              <div class="run-output-header">
                <span><i class="fas fa-terminal"></i> 运行输出</span>
                <el-button size="small" text @click="runOutput = ''">清除</el-button>
              </div>
              <pre class="run-output-content">{{ runOutput }}</pre>
            </div>
         </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import apiClient from '../api/index';
import { generateCodeTask, submitCodeReview } from '../api/index';

const loadingDebug = ref(false);
const loadingRefactor = ref(false);
const evaluating = ref(false);
const running = ref(false);

const currentTask = ref<any>(null);
const currentTaskType = ref('');
const studentCode = ref('');
const attempts = ref(0);
const runOutput = ref('');

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
    runOutput.value = '';
};

const generateTask = async (taskType: string) => {
    if (taskType === 'debug') {
        loadingDebug.value = true;
    } else {
        loadingRefactor.value = true;
    }
    try {
        resetState();
        currentTaskType.value = taskType;
        const res = await generateCodeTask('软件测试与代码规范', taskType);
        if (res.data.code === 200 && res.data.data) {
            currentTask.value = res.data.data;
            studentCode.value = currentTask.value.bad_code;
            ElMessage.success(taskType === 'debug' ? '已获取Debug专项题' : '已获取代码质量重构题');
        } else {
            ElMessage.error(res.data.message || '获取失败');
        }
    } catch (e: any) {
        ElMessage.error(e.message || '网络错误');
    } finally {
        loadingDebug.value = false;
        loadingRefactor.value = false;
    }
};

const runCode = async () => {
    if (!studentCode.value.trim()) {
        ElMessage.warning('代码不能为空');
        return;
    }
    running.value = true;
    try {
        const res = await apiClient.post('/api/code_training/run_code', {
            student_code: studentCode.value
        });
        if (res.data.code === 200 && res.data.data) {
            runOutput.value = res.data.data.output || '(无输出)';
        } else {
            runOutput.value = res.data.message || '运行失败';
        }
    } catch (e: any) {
        runOutput.value = e.message || '网络错误';
    } finally {
        running.value = false;
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

.header-buttons {
    display: flex;
    gap: 12px;
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

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.points {
    margin: 10px 0;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.feedback-area {
    background-color: #f7f9fc;
    padding: 15px;
    border-radius: 6px;
    white-space: pre-wrap;
    line-height: 1.6;
}

.run-output {
    margin-top: 12px;
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    overflow: hidden;
}

.run-output-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background-color: #1e1e1e;
    color: #dcdcdc;
    font-size: 13px;
}

.run-output-content {
    padding: 12px;
    background-color: #2d2d2d;
    color: #dcdcdc;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.5;
    margin: 0;
    max-height: 200px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
}

.status-badge {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.mt-2 { margin-top: 8px; }
.mt-4 { margin-top: 16px; }
.ml-1 { margin-left: 4px; }
.text-red-500 { color: #f56c6c; }
.text-blue-500 { color: #409eff; }
.text-sm { font-size: 14px; }

.debug-card :deep(.el-card__header) {
    border-left: 4px solid #f56c6c;
}
.refactor-card :deep(.el-card__header) {
    border-left: 4px solid #e6a23c;
}
</style>
