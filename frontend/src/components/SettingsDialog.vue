<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="1200"
    content-class="settings-dialog"
  >
    <v-card>
      <v-card-title class="text-h5 pa-4">
        系统设置
        <v-spacer></v-spacer>
        <v-btn icon @click="$emit('update:modelValue', false)">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text class="pa-4">
        <v-row>
          <!-- 基本设置卡片 -->
          <v-col cols="12" md="6">
            <v-card class="mb-4">
              <v-card-title class="text-h6">
                <v-icon start color="primary" class="me-2">mdi-cog</v-icon>
                基本设置
              </v-card-title>
              <v-card-text>
                <v-switch
                  v-model="settings.emailNotification"
                  label="邮件通知"
                  color="primary"
                  hide-details
                  class="mb-4"
                ></v-switch>
                <v-switch
                  v-model="settings.autoSave"
                  label="自动保存"
                  color="primary"
                  hide-details
                  class="mb-4"
                ></v-switch>
                <v-select
                  v-model="settings.language"
                  :items="languageOptions"
                  label="系统语言"
                  hide-details
                  class="mb-4"
                ></v-select>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- 视频处理设置卡片 -->
          <v-col cols="12" md="6">
            <v-card class="mb-4">
              <v-card-title class="text-h6">
                <v-icon start color="primary" class="me-2">mdi-video</v-icon>
                视频处理设置
              </v-card-title>
              <v-card-text>
                <v-select
                  v-model="settings.videoQuality"
                  :items="videoQualityOptions"
                  label="默认视频质量"
                  hide-details
                  class="mb-4"
                ></v-select>
                <v-select
                  v-model="settings.transcodeFormat"
                  :items="transcodeFormatOptions"
                  label="转码格式"
                  hide-details
                  class="mb-4"
                ></v-select>
                <v-switch
                  v-model="settings.autoTranscode"
                  label="自动转码"
                  color="primary"
                  hide-details
                  class="mb-4"
                ></v-switch>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- 帮助与支持卡片 -->
          <v-col cols="12" md="6">
            <v-card class="mb-4">
              <v-card-title class="text-h6">
                <v-icon start color="primary" class="me-2">mdi-help-circle</v-icon>
                帮助与支持
              </v-card-title>
              <v-card-text>
                <v-list>
                  <v-list-item
                    href="https://gitee.com/opguess/AgentEducator2"
                    target="_blank"
                    class="support-item"
                  >
                    <template v-slot:prepend>
                      <v-icon color="primary">mdi-book-open-variant</v-icon>
                    </template>
                    <v-list-item-title>帮助中心</v-list-item-title>
                    <template v-slot:append>
                      <v-icon>mdi-open-in-new</v-icon>
                    </template>
                  </v-list-item>

                  <v-divider class="my-2"></v-divider>

                  <v-list-item
                    @click="showFeedbackDialog = true"
                    class="support-item"
                  >
                    <template v-slot:prepend>
                      <v-icon color="primary">mdi-message-text</v-icon>
                    </template>
                    <v-list-item-title>意见反馈</v-list-item-title>
                    <template v-slot:append>
                      <v-icon>mdi-chevron-right</v-icon>
                    </template>
                  </v-list-item>

                  <v-divider class="my-2"></v-divider>

                  <v-list-item
                    @click="showCustomerServiceDialog = true"
                    class="support-item"
                  >
                    <template v-slot:prepend>
                      <v-icon color="primary">mdi-headset</v-icon>
                    </template>
                    <v-list-item-title>联系客服</v-list-item-title>
                    <template v-slot:append>
                      <v-icon>mdi-chevron-right</v-icon>
                    </template>
                  </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- 法律条款卡片 -->
          <v-col cols="12" md="6">
            <v-card class="mb-4">
              <v-card-title class="text-h6">
                <v-icon start color="primary" class="me-2">mdi-file-document-outline</v-icon>
                法律条款
              </v-card-title>
              <v-card-text>
                <v-list>
                  <v-list-item
                    @click="showUserAgreement = true"
                    class="policy-item"
                  >
                    <template v-slot:prepend>
                      <v-icon color="primary">mdi-file-document</v-icon>
                    </template>
                    <v-list-item-title>用户协议</v-list-item-title>
                    <template v-slot:append>
                      <v-icon>mdi-chevron-right</v-icon>
                    </template>
                  </v-list-item>
                  
                  <v-divider class="my-2"></v-divider>
                  
                  <v-list-item
                    @click="showPrivacyPolicy = true"
                    class="policy-item"
                  >
                    <template v-slot:prepend>
                      <v-icon color="primary">mdi-shield-account</v-icon>
                    </template>
                    <v-list-item-title>隐私政策</v-list-item-title>
                    <template v-slot:append>
                      <v-icon>mdi-chevron-right</v-icon>
                    </template>
                  </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- 版本信息 -->
          <v-col cols="12">
            <div class="version-info">
              <span class="text-caption text-medium-emphasis">
                v{{ currentVersion }}
                <v-btn
                  variant="text"
                  density="compact"
                  size="x-small"
                  class="ms-1"
                  :loading="checkingUpdate"
                  @click="checkUpdate"
                >
                  <v-icon size="small">mdi-update</v-icon>
                </v-btn>
              </span>
            </div>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 用户协议对话框 -->
    <v-dialog v-model="showUserAgreement" max-width="800">
      <v-card>
        <v-card-title class="text-h5">
          用户协议
          <v-spacer></v-spacer>
          <v-btn icon @click="showUserAgreement = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="agreement-content">
          <div class="text-body-1 pa-4">
            <h3 class="text-h6 mb-4">1. 服务条款</h3>
            <p class="mb-4">欢迎使用闻道教育平台。通过访问或使用我们的服务，您同意受本协议的约束。如果您不同意这些条款，请不要使用我们的服务。</p>
            
            <h3 class="text-h6 mb-4">2. 账户责任</h3>
            <p class="mb-4">您负责维护您账户的保密性，并对发生在您账户下的所有活动负责。</p>
            
            <h3 class="text-h6 mb-4">3. 知识产权</h3>
            <p class="mb-4">平台上的所有内容，包括但不限于文本、图形、标识、按钮图标、图像、音频剪辑、数字下载、数据编辑和软件，均为闻道教育平台或其内容提供者的财产。</p>
            
            <h3 class="text-h6 mb-4">4. 服务变更</h3>
            <p class="mb-4">我们保留随时修改或终止服务的权利，恕不另行通知。</p>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            variant="text"
            @click="showUserAgreement = false"
          >
            关闭
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 隐私政策对话框 -->
    <v-dialog v-model="showPrivacyPolicy" max-width="800">
      <v-card>
        <v-card-title class="text-h5">
          隐私政策
          <v-spacer></v-spacer>
          <v-btn icon @click="showPrivacyPolicy = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="privacy-content">
          <div class="text-body-1 pa-4">
            <h3 class="text-h6 mb-4">1. 信息收集</h3>
            <p class="mb-4">我们收集的信息包括但不限于：您提供的个人信息、使用我们服务时自动生成的信息、来自第三方的信息。</p>
            
            <h3 class="text-h6 mb-4">2. 信息使用</h3>
            <p class="mb-4">我们使用收集的信息来提供、维护、保护和改进我们的服务，开发新的服务，并保护闻道教育平台和我们的用户。</p>
            
            <h3 class="text-h6 mb-4">3. 信息共享</h3>
            <p class="mb-4">除非得到您的明确同意，我们不会与第三方共享您的个人信息。但我们可能会共享非个人身份信息，用于分析和改进服务。</p>
            
            <h3 class="text-h6 mb-4">4. 信息安全</h3>
            <p class="mb-4">我们采取适当的安全措施来保护您的信息免遭未经授权的访问、更改、披露或破坏。</p>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            variant="text"
            @click="showPrivacyPolicy = false"
          >
            关闭
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 意见反馈对话框 -->
    <v-dialog v-model="showFeedbackDialog" max-width="600">
      <v-card>
        <v-card-title class="text-h5">
          意见反馈
          <v-spacer></v-spacer>
          <v-btn icon @click="showFeedbackDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <v-form ref="feedbackForm" v-model="feedbackValid">
            <v-select
              v-model="feedback.type"
              :items="feedbackTypes"
              label="反馈类型"
              required
              class="mb-4"
            ></v-select>
            <v-textarea
              v-model="feedback.content"
              label="反馈内容"
              required
              :rules="[(v: string) => !!v || '请输入反馈内容']"
              rows="4"
              class="mb-4"
            ></v-textarea>
            <v-text-field
              v-model="feedback.contact"
              label="联系方式（选填）"
              placeholder="邮箱或手机号"
              class="mb-4"
            ></v-text-field>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            @click="submitFeedback"
            :loading="submittingFeedback"
            :disabled="!feedbackValid"
          >
            提交反馈
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 联系客服对话框 -->
    <v-dialog v-model="showCustomerServiceDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h5">
          联系客服
          <v-spacer></v-spacer>
          <v-btn icon @click="showCustomerServiceDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <v-list>
            <v-list-item>
              <template v-slot:prepend>
                <v-icon color="primary">mdi-email</v-icon>
              </template>
              <v-list-item-title>客服邮箱</v-list-item-title>
              <v-list-item-subtitle>wendaoSupport@163.com</v-list-item-subtitle>
            </v-list-item>

            <v-divider class="my-2"></v-divider>

            <v-list-item>
              <template v-slot:prepend>
                <v-icon color="primary">mdi-phone</v-icon>
              </template>
              <v-list-item-title>服务热线</v-list-item-title>
              <v-list-item-subtitle>400-114-514</v-list-item-subtitle>
            </v-list-item>

            <v-divider class="my-2"></v-divider>

            <v-list-item>
              <template v-slot:prepend>
                <v-icon color="primary">mdi-clock</v-icon>
              </template>
              <v-list-item-title>服务时间</v-list-item-title>
              <v-list-item-subtitle>周一至周五 9:00-18:00</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- 更新提示对话框 -->
    <v-dialog v-model="showUpdateDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h5">
          {{ hasUpdate ? '发现新版本' : '已是最新版本' }}
        </v-card-title>
        <v-card-text>
          <template v-if="hasUpdate">
            <p class="mb-2">最新版本：v{{ latestVersion }}</p>
            <p class="mb-4">{{ updateContent }}</p>
          </template>
          <template v-else>
            <p>当前已经是最新版本 v{{ currentVersion }}</p>
          </template>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            v-if="hasUpdate"
            color="primary"
            @click="startUpdate"
            :loading="updating"
          >
            立即更新
          </v-btn>
          <v-btn
            color="primary"
            variant="text"
            @click="showUpdateDialog = false"
          >
            {{ hasUpdate ? '稍后再说' : '确定' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits } from 'vue';
import { useSnackbar } from '../stores/snackbarStore';

const props = defineProps<{
  modelValue: boolean
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>();

const snackbar = useSnackbar();

// 设置数据
const settings = ref({
  emailNotification: true,
  autoSave: true,
  language: 'zh_CN',
  videoQuality: '720p',
  transcodeFormat: 'mp4',
  autoTranscode: true
});

// 选项数据
const languageOptions = [
  { title: '简体中文', value: '0' },
  { title: '汉语', value: '1' },
  { title: '普通话', value: '2' }
];

const videoQualityOptions = [
  { title: '480p', value: '480p' },
  { title: '720p', value: '720p' },
  { title: '1080p', value: '1080p' }
];

const transcodeFormatOptions = [
  { title: 'MP4', value: 'mp4' },
  { title: 'WebM', value: 'webm' },
  { title: 'HLS', value: 'hls' }
];

// 对话框控制
const showUserAgreement = ref(false);
const showPrivacyPolicy = ref(false);
const showFeedbackDialog = ref(false);
const showCustomerServiceDialog = ref(false);
const showUpdateDialog = ref(false);

// 意见反馈相关
const feedbackForm = ref(null);
const feedbackValid = ref(false);
const submittingFeedback = ref(false);
const feedback = ref({
  type: '',
  content: '',
  contact: ''
});

const feedbackTypes = [
  { title: '功能建议', value: 'feature' },
  { title: '问题反馈', value: 'bug' },
  { title: '其他', value: 'other' }
];

// 版本信息
const currentVersion = ref('1.0.0');
const latestVersion = ref('1.0.1');
const hasUpdate = ref(false);
const checkingUpdate = ref(false);
const updating = ref(false);
const updateContent = ref('1. 优化系统性能\n2. 修复已知问题\n3. 新增部分功能');

// 提交反馈
const submitFeedback = async () => {
  submittingFeedback.value = true;
  try {
    // TODO: 调用后端API提交反馈
    await new Promise(resolve => setTimeout(resolve, 1000));
    snackbar.show({
      text: '感谢您的反馈！',
      color: 'success'
    });
    showFeedbackDialog.value = false;
    feedback.value = {
      type: '',
      content: '',
      contact: ''
    };
  } catch (error) {
    snackbar.show({
      text: '提交失败，请稍后重试',
      color: 'error'
    });
  } finally {
    submittingFeedback.value = false;
  }
};

// 检查更新
const checkUpdate = async () => {
  checkingUpdate.value = true;
  try {
    // TODO: 调用后端API检查更新
    await new Promise(resolve => setTimeout(resolve, 1000));
    hasUpdate.value = true;
    showUpdateDialog.value = true;
  } catch (error) {
    snackbar.show({
      text: '检查更新失败，请稍后重试',
      color: 'error'
    });
  } finally {
    checkingUpdate.value = false;
  }
};

// 开始更新
const startUpdate = async () => {
  updating.value = true;
  try {
    // TODO: 调用后端API开始更新
    await new Promise(resolve => setTimeout(resolve, 2000));
    snackbar.show({
      text: '更新成功，即将重启应用',
      color: 'success'
    });
    setTimeout(() => {
      window.location.reload();
    }, 1500);
  } catch (error) {
    snackbar.show({
      text: '更新失败，请稍后重试',
      color: 'error'
    });
  } finally {
    updating.value = false;
  }
};
</script>

<style scoped>
/* 保持原有样式不变 */
/* ... 复制原有的 Settings.vue 中的 style 部分代码 ... */

:deep(.settings-dialog) {
  z-index: 200;
}

/* 确保内部对话框在设置对话框之上 */
:deep(.v-overlay) {
  z-index: 999 !important;
}

:deep(.v-dialog) {
  z-index: 1000 !important;
}

/* 确保内部对话框的遮罩层也在正确的层级 */
:deep(.v-overlay__scrim) {
  z-index: 998 !important;
}

/* 确保内部对话框的内容在最上层 */
:deep(.v-overlay__content) {
  z-index: 1001 !important;
}

.v-card {
  border-radius: 12px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.v-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 25px 0 rgba(0, 0, 0, 0.1);
}

.v-card-title {
  padding: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.v-card-text {
  padding: 20px;
}

.policy-item, .support-item {
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-radius: 8px;
}

.policy-item:hover, .support-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.agreement-content, .privacy-content {
  max-height: 60vh;
  overflow-y: auto;
}

.agreement-content h3, .privacy-content h3 {
  color: var(--v-theme-primary);
}

.agreement-content p, .privacy-content p {
  line-height: 1.6;
  color: rgba(var(--v-theme-on-surface), 0.87);
}

.version-info {
  position: fixed;
  bottom: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  background-color: rgba(var(--v-theme-surface), 0.8);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style> 