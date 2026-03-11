<template>
  <view class="task-page">
    <view v-if="!task" class="loading">
      <text>加载中...</text>
    </view>

    <view v-else>
      <view class="task-header-card">
        <text class="task-name">{{ task.task_title }}</text>
        <view class="status-badge" :class="`badge-${task.status}`">
          {{ statusText[task.status] || task.status }}
        </view>
        <text class="task-date">计划日期: {{ formatDate(task.scheduled_date) }}</text>
        <text v-if="task.task_description" class="task-desc">{{ task.task_description }}</text>
      </view>

      <!-- 问卷类型任务 -->
      <view v-if="task.task_type === 'questionnaire' && task.status === 'pending'" class="section">
        <text class="section-title">请完成以下问卷</text>

        <view class="q-item" v-for="(q, i) in questions" :key="i">
          <text class="q-label">{{ i + 1 }}. {{ q.label }}</text>
          <radio-group @change="(e) => answers[q.key] = e.detail.value">
            <view class="q-options">
              <label v-for="opt in q.options" :key="opt" class="q-option">
                <radio :value="opt" :checked="answers[q.key] === opt" />
                <text>{{ opt }}</text>
              </label>
            </view>
          </radio-group>
        </view>

        <view class="q-item">
          <text class="q-label">补充说明（可选）</text>
          <textarea v-model="note" placeholder="描述您目前的身体状况..." class="textarea" />
        </view>

        <button class="submit-btn" :loading="submitting" @tap="submitQuestionnaire">提交问卷</button>
      </view>

      <!-- 上传类型任务 -->
      <view v-if="task.task_type === 'upload' && task.status === 'pending'" class="section">
        <text class="section-title">请上传检查报告</text>
        <text class="upload-hint">支持拍照或从相册选择报告图片</text>

        <view class="upload-area" @tap="chooseImage">
          <text class="upload-icon">📷</text>
          <text class="upload-text">点击上传</text>
        </view>

        <view v-if="uploadedFiles.length" class="file-list">
          <view v-for="(f, i) in uploadedFiles" :key="i" class="file-item">
            <text>✅ {{ f }}</text>
          </view>
        </view>

        <button class="submit-btn" :loading="submitting" :disabled="!uploadedFiles.length" @tap="submitUpload">
          提交报告
        </button>
      </view>

      <!-- 已完成 -->
      <view v-if="task.status === 'completed'" class="completed-section">
        <view class="done-icon">✅</view>
        <text class="done-text">该任务已完成</text>
        <text v-if="task.completed_date" class="done-date">
          完成时间: {{ formatDate(task.completed_date) }}
        </text>
      </view>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api.js';

export default {
  data() {
    return {
      taskId: 0,
      task: null,
      submitting: false,
      note: '',
      answers: {},
      uploadedFiles: [],
      statusText: { pending: '待完成', completed: '已完成', overdue: '已逾期', in_progress: '进行中' },
      questions: [
        { key: 'general', label: '总体感觉如何？', options: ['很好', '一般', '不太好', '很差'] },
        { key: 'pain', label: '是否有腹部疼痛？', options: ['无', '轻微', '中等', '严重'] },
        { key: 'bleeding', label: '是否有异常出血？', options: ['无', '少量', '中等', '大量'] },
        { key: 'appetite', label: '食欲如何？', options: ['正常', '略差', '明显减退', '几乎无'] },
        { key: 'sleep', label: '睡眠质量如何？', options: ['很好', '一般', '较差', '失眠'] },
        { key: 'mood', label: '情绪状态如何？', options: ['良好', '一般', '焦虑', '抑郁'] },
      ],
    };
  },

  onLoad(options) {
    this.taskId = parseInt(options.id || '0');
    this.loadTask();
  },

  methods: {
    async loadTask() {
      try {
        const res = await api.getMyTasks();
        if (res.success) {
          this.task = res.data.find((t) => t.id === this.taskId) || null;
          if (!this.task) {
            uni.showToast({ title: '任务不存在', icon: 'none' });
          }
        }
      } catch (e) {
        console.error(e);
      }
    },

    formatDate(d) {
      if (!d) return '-';
      const dt = new Date(d);
      return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`;
    },

    async submitQuestionnaire() {
      const unanswered = this.questions.filter((q) => !this.answers[q.key]);
      if (unanswered.length) {
        uni.showToast({ title: `请回答第 ${this.questions.indexOf(unanswered[0]) + 1} 题`, icon: 'none' });
        return;
      }

      this.submitting = true;
      try {
        const res = await api.submitRecord({
          task_id: this.taskId,
          patient_id: api.getPatientId(),
          record_type: 'questionnaire',
          record_data: { note: this.note },
          questionnaire_answers: this.answers,
        });
        if (res.success) {
          uni.showToast({ title: '提交成功', icon: 'success' });
          setTimeout(() => uni.navigateBack(), 1000);
        }
      } catch (e) {
        console.error(e);
      } finally {
        this.submitting = false;
      }
    },

    chooseImage() {
      uni.chooseImage({
        count: 3,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: async (res) => {
          for (const path of res.tempFilePaths) {
            try {
              const r = await api.uploadFile(path);
              if (r.success) {
                this.uploadedFiles.push(path.split('/').pop());
              }
            } catch (e) {
              uni.showToast({ title: '上传失败', icon: 'none' });
            }
          }
        },
      });
    },

    async submitUpload() {
      this.submitting = true;
      try {
        const res = await api.submitRecord({
          task_id: this.taskId,
          patient_id: api.getPatientId(),
          record_type: 'upload',
          record_data: {},
          uploaded_files: this.uploadedFiles,
        });
        if (res.success) {
          uni.showToast({ title: '提交成功', icon: 'success' });
          setTimeout(() => uni.navigateBack(), 1000);
        }
      } catch (e) {
        console.error(e);
      } finally {
        this.submitting = false;
      }
    },
  },
};
</script>

<style scoped>
.task-page { padding: 20rpx; min-height: 100vh; }
.loading { text-align: center; padding: 100rpx 0; color: #999; }

.task-header-card {
  background: white; border-radius: 16rpx; padding: 36rpx;
  margin-bottom: 24rpx; box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.06);
}
.task-name { font-size: 36rpx; font-weight: bold; display: block; margin-bottom: 12rpx; }
.status-badge {
  display: inline-block; padding: 6rpx 20rpx; border-radius: 20rpx;
  font-size: 24rpx; margin-bottom: 16rpx;
}
.badge-pending { background: #fff3e0; color: #f57c00; }
.badge-completed { background: #e8f5e9; color: #2e7d32; }
.badge-overdue { background: #ffebee; color: #c62828; }
.task-date { display: block; font-size: 26rpx; color: #888; margin-bottom: 8rpx; }
.task-desc { display: block; font-size: 28rpx; color: #666; margin-top: 12rpx; }

.section {
  background: white; border-radius: 16rpx; padding: 36rpx;
  margin-bottom: 24rpx; box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.06);
}
.section-title { font-size: 32rpx; font-weight: bold; display: block; margin-bottom: 24rpx; }

.q-item { margin-bottom: 32rpx; }
.q-label { display: block; font-size: 28rpx; font-weight: 500; margin-bottom: 16rpx; }
.q-options { display: flex; flex-wrap: wrap; gap: 16rpx; }
.q-option { display: flex; align-items: center; gap: 8rpx; font-size: 26rpx; min-width: 40%; }

.textarea {
  width: 100%; border: 1px solid #e0e0e0; border-radius: 12rpx;
  padding: 20rpx; font-size: 28rpx; min-height: 120rpx; box-sizing: border-box;
}

.submit-btn {
  background: linear-gradient(135deg, #667eea, #764ba2); color: white;
  border: none; border-radius: 12rpx; font-size: 30rpx; padding: 22rpx 0; margin-top: 24rpx;
}

.upload-hint { font-size: 26rpx; color: #999; display: block; margin-bottom: 20rpx; }
.upload-area {
  border: 2rpx dashed #ccc; border-radius: 16rpx; padding: 60rpx;
  text-align: center; margin-bottom: 20rpx;
}
.upload-icon { font-size: 64rpx; display: block; }
.upload-text { font-size: 28rpx; color: #666; }
.file-list { margin-bottom: 16rpx; }
.file-item { font-size: 26rpx; color: #4caf50; padding: 8rpx 0; }

.completed-section { text-align: center; padding: 80rpx 0; }
.done-icon { font-size: 80rpx; }
.done-text { display: block; font-size: 32rpx; color: #4caf50; font-weight: bold; margin: 20rpx 0 10rpx; }
.done-date { display: block; font-size: 26rpx; color: #999; }
</style>
