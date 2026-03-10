<template>
  <view class="history-page">
    <view class="tab-bar">
      <view
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-item"
        :class="{ active: activeTab === tab.key }"
        @tap="activeTab = tab.key"
      >
        {{ tab.label }}
      </view>
    </view>

    <!-- 全部任务 -->
    <view v-if="filteredTasks.length === 0" class="empty">
      <text>暂无{{ activeTab === 'all' ? '' : tabs.find(t => t.key === activeTab)?.label }}记录</text>
    </view>

    <view v-for="task in filteredTasks" :key="task.id" class="task-card" @tap="goToTask(task)">
      <view class="task-row">
        <text class="task-title">{{ task.task_title }}</text>
        <view class="badge" :class="`badge-${task.status}`">
          {{ statusText[task.status] || task.status }}
        </view>
      </view>
      <view class="task-meta">
        <text>类型: {{ typeText[task.task_type] || task.task_type }}</text>
        <text>计划: {{ formatDate(task.scheduled_date) }}</text>
      </view>
      <text v-if="task.completed_date" class="completed-info">
        ✅ 完成于 {{ formatDate(task.completed_date) }}
      </text>
    </view>

    <!-- AI 报告摘要 -->
    <view v-if="activeTab === 'ai' && aiResults.length" class="ai-section">
      <view v-for="r in aiResults" :key="r.id" class="ai-card">
        <view class="ai-header">
          <text class="ai-type">{{ analysisLabel[r.analysis_type] || r.analysis_type }}</text>
          <text class="ai-time">{{ r.created_at }}</text>
        </view>
        <text v-if="r.risk_level" class="risk-tag" :class="`risk-${r.risk_level}`">
          {{ riskText[r.risk_level] || r.risk_level }}
        </text>
        <text v-if="r.report_text" class="ai-summary">
          {{ r.report_text.length > 120 ? r.report_text.slice(0, 120) + '…' : r.report_text }}
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
      activeTab: 'all',
      tasks: [],
      aiResults: [],
      tabs: [
        { key: 'all', label: '全部' },
        { key: 'pending', label: '待完成' },
        { key: 'completed', label: '已完成' },
        { key: 'ai', label: 'AI 报告' },
      ],
      statusText: { pending: '待完成', completed: '已完成', overdue: '已逾期', in_progress: '进行中' },
      typeText: { questionnaire: '问卷', upload: '上传报告', call: '电话随访' },
      analysisLabel: {
        segmentation: 'U-Net 分割',
        prediction: '预后预测',
        medgemma_report: 'MedGemma 报告',
        medgemma_prognosis: 'MedGemma 预后',
      },
      riskText: { low: '低风险', medium: '中风险', high: '高风险' },
    };
  },

  computed: {
    filteredTasks() {
      if (this.activeTab === 'ai') return [];
      if (this.activeTab === 'all') return this.tasks;
      return this.tasks.filter((t) => t.status === this.activeTab);
    },
  },

  onLoad() {
    this.load();
  },

  methods: {
    async load() {
      try {
        const [taskRes, aiRes] = await Promise.all([
          api.getMyTasks(),
          api.getMyAIResults(),
        ]);
        if (taskRes.success) this.tasks = taskRes.data || [];
        if (aiRes.success) this.aiResults = aiRes.data || [];
      } catch (e) {
        console.error(e);
      }
    },

    formatDate(d) {
      if (!d) return '-';
      const dt = new Date(d);
      return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`;
    },

    goToTask(task) {
      uni.navigateTo({ url: `/pages/task/task?id=${task.id}` });
    },
  },
};
</script>

<style scoped>
.history-page { padding: 20rpx; }
.tab-bar {
  display: flex; background: white; border-radius: 12rpx;
  margin-bottom: 20rpx; overflow: hidden;
}
.tab-item {
  flex: 1; text-align: center; padding: 24rpx 0;
  font-size: 28rpx; color: #666; border-bottom: 4rpx solid transparent;
}
.tab-item.active { color: #667eea; border-bottom-color: #667eea; font-weight: bold; }
.empty { text-align: center; padding: 80rpx 0; color: #999; font-size: 28rpx; }
.task-card {
  background: white; border-radius: 12rpx; padding: 28rpx;
  margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04);
}
.task-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.task-title { font-size: 30rpx; font-weight: 500; }
.badge {
  padding: 6rpx 18rpx; border-radius: 20rpx; font-size: 22rpx;
}
.badge-pending { background: #fff3e0; color: #f57c00; }
.badge-completed { background: #e8f5e9; color: #2e7d32; }
.badge-overdue { background: #ffebee; color: #c62828; }
.task-meta { display: flex; gap: 24rpx; font-size: 24rpx; color: #999; }
.completed-info { display: block; font-size: 24rpx; color: #4caf50; margin-top: 8rpx; }

.ai-section { margin-top: 10rpx; }
.ai-card {
  background: white; border-radius: 12rpx; padding: 28rpx;
  margin-bottom: 16rpx; box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04);
}
.ai-header { display: flex; justify-content: space-between; margin-bottom: 12rpx; }
.ai-type { font-size: 28rpx; font-weight: 500; color: #1890ff; }
.ai-time { font-size: 24rpx; color: #999; }
.risk-tag {
  display: inline-block; padding: 6rpx 18rpx; border-radius: 20rpx;
  font-size: 22rpx; margin-bottom: 12rpx;
}
.risk-low { background: #e8f5e9; color: #2e7d32; }
.risk-medium { background: #fff3e0; color: #f57c00; }
.risk-high { background: #ffebee; color: #c62828; }
.ai-summary { font-size: 26rpx; color: #666; line-height: 1.6; }
</style>
