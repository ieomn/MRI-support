<template>
  <view class="container">
    <view class="header">
      <text class="title">康复随访</text>
      <text class="subtitle">您好，{{ patientName }}</text>
    </view>

    <!-- 任务列表 -->
    <view class="task-section">
      <view class="section-title">待办任务 ({{ pendingTasks.length }})</view>

      <view
        v-for="task in pendingTasks"
        :key="task.id"
        class="task-card"
        @tap="goToTask(task)"
      >
        <view class="task-header">
          <text class="task-title">{{ task.task_title }}</text>
          <view class="task-status" :class="getStatusClass(task.status)">
            {{ getStatusText(task.status) }}
          </view>
        </view>
        <view class="task-content">
          <text v-if="task.task_description" class="task-desc">{{ task.task_description }}</text>
          <text class="task-date">计划时间: {{ formatDate(task.scheduled_date) }}</text>
        </view>
        <view class="task-action">
          <button v-if="task.status === 'pending'" size="mini" type="primary">去完成</button>
          <text v-else class="completed-text">已完成</text>
        </view>
      </view>

      <view v-if="pendingTasks.length === 0" class="empty-state">
        <text>🎉 暂无待办任务，继续保持！</text>
      </view>
    </view>

    <!-- 快捷入口 -->
    <view class="quick-section">
      <view class="section-title">快捷功能</view>
      <view class="quick-grid">
        <view class="quick-item" @tap="goToPage('health')">
          <view class="quick-icon">📝</view>
          <text class="quick-text">健康问卷</text>
        </view>
        <view class="quick-item" @tap="goToPage('report')">
          <view class="quick-icon">📄</view>
          <text class="quick-text">上传报告</text>
        </view>
        <view class="quick-item" @tap="goToPage('history')">
          <view class="quick-icon">📅</view>
          <text class="quick-text">随访记录</text>
        </view>
        <view class="quick-item" @tap="goToPage('contact')">
          <view class="quick-icon">📞</view>
          <text class="quick-text">联系医生</text>
        </view>
      </view>
    </view>

    <!-- 最近 AI 分析 -->
    <view v-if="latestAI" class="ai-section">
      <view class="section-title">最新 AI 分析</view>
      <view class="ai-card">
        <text class="ai-type">{{ analysisLabel[latestAI.analysis_type] || latestAI.analysis_type }}</text>
        <text v-if="latestAI.risk_level" class="risk-tag" :class="`risk-${latestAI.risk_level}`">
          {{ riskText[latestAI.risk_level] }}
        </text>
        <text class="ai-time">{{ latestAI.created_at }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api.js';

export default {
  data() {
    return {
      patientName: '',
      tasks: [],
      latestAI: null,
      analysisLabel: {
        segmentation: 'U-Net 分割',
        prediction: '预后预测',
        medgemma_report: 'MedGemma 影像分析',
        medgemma_prognosis: 'MedGemma 预后评估',
      },
      riskText: { low: '低风险', medium: '中风险', high: '高风险' },
    };
  },

  computed: {
    pendingTasks() {
      return this.tasks.filter((t) => t.status === 'pending' || t.status === 'overdue');
    },
  },

  onShow() {
    this.patientName = uni.getStorageSync('patient_name') || '患者';
    this.loadData();
  },

  methods: {
    async loadData() {
      try {
        const [taskRes, aiRes] = await Promise.all([
          api.getMyTasks(),
          api.getMyAIResults(),
        ]);
        if (taskRes.success) this.tasks = taskRes.data || [];
        if (aiRes.success && aiRes.data?.length) {
          this.latestAI = aiRes.data[aiRes.data.length - 1];
        }
      } catch (e) {
        console.error('加载数据失败:', e);
      }
    },

    formatDate(dateStr) {
      if (!dateStr) return '-';
      const d = new Date(dateStr);
      return `${d.getMonth() + 1}月${d.getDate()}日`;
    },

    getStatusText(status) {
      return { pending: '待完成', in_progress: '进行中', completed: '已完成', overdue: '已逾期' }[status] || status;
    },

    getStatusClass(status) {
      return `status-${status}`;
    },

    goToTask(task) {
      uni.navigateTo({ url: `/pages/task/task?id=${task.id}` });
    },

    goToPage(page) {
      uni.navigateTo({ url: `/pages/${page}/${page}` });
    },
  },
};
</script>

<style scoped>
.container { min-height: 100vh; background: #f5f5f5; padding: 20rpx; }
.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16rpx; padding: 40rpx; color: white; margin-bottom: 30rpx;
}
.title { font-size: 48rpx; font-weight: bold; display: block; margin-bottom: 16rpx; }
.subtitle { font-size: 28rpx; opacity: 0.9; }
.task-section, .quick-section, .ai-section { margin-bottom: 30rpx; }
.section-title { font-size: 32rpx; font-weight: bold; margin-bottom: 20rpx; padding-left: 10rpx; }
.task-card {
  background: white; border-radius: 12rpx; padding: 30rpx;
  margin-bottom: 20rpx; box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
}
.task-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; }
.task-title { font-size: 32rpx; font-weight: bold; }
.task-status { padding: 8rpx 20rpx; border-radius: 20rpx; font-size: 24rpx; }
.status-pending { background: #fff3e0; color: #f57c00; }
.status-completed { background: #e8f5e9; color: #2e7d32; }
.status-overdue { background: #ffebee; color: #c62828; }
.task-content { display: flex; flex-direction: column; gap: 12rpx; margin-bottom: 20rpx; }
.task-desc { font-size: 28rpx; color: #666; }
.task-date { font-size: 24rpx; color: #999; }
.task-action button { width: 100%; }
.completed-text { color: #4caf50; font-size: 28rpx; text-align: center; display: block; }
.empty-state { text-align: center; padding: 60rpx 0; color: #999; font-size: 28rpx; }
.quick-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20rpx; }
.quick-item {
  background: white; border-radius: 12rpx; padding: 40rpx;
  display: flex; flex-direction: column; align-items: center; gap: 16rpx;
  box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
}
.quick-icon { font-size: 64rpx; }
.quick-text { font-size: 28rpx; color: #333; }
.ai-card {
  background: white; border-radius: 12rpx; padding: 28rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04);
  display: flex; align-items: center; gap: 16rpx; flex-wrap: wrap;
}
.ai-type { font-size: 28rpx; font-weight: 500; color: #1890ff; }
.risk-tag {
  padding: 6rpx 18rpx; border-radius: 20rpx; font-size: 22rpx;
}
.risk-low { background: #e8f5e9; color: #2e7d32; }
.risk-medium { background: #fff3e0; color: #f57c00; }
.risk-high { background: #ffebee; color: #c62828; }
.ai-time { font-size: 24rpx; color: #999; margin-left: auto; }
</style>
