<template>
  <view class="container">
    <view class="header">
      <text class="title">康复随访</text>
      <text class="subtitle">您好，{{ patientName }}</text>
    </view>

    <!-- 任务列表 -->
    <view class="task-section">
      <view class="section-title">待办任务</view>
      
      <view 
        v-for="task in tasks" 
        :key="task.id" 
        class="task-card"
        @tap="goToTask(task)"
      >
        <view class="task-header">
          <text class="task-title">{{ task.task_title }}</text>
          <view 
            class="task-status" 
            :class="getStatusClass(task.status)"
          >
            {{ getStatusText(task.status) }}
          </view>
        </view>
        
        <view class="task-content">
          <text class="task-desc">{{ task.task_description }}</text>
          <text class="task-date">计划时间: {{ formatDate(task.scheduled_date) }}</text>
        </view>

        <view class="task-action">
          <button 
            v-if="task.status === 'pending'" 
            size="mini" 
            type="primary"
          >
            去完成
          </button>
          <text v-else class="completed-text">已完成</text>
        </view>
      </view>

      <view v-if="tasks.length === 0" class="empty-state">
        <text>暂无待办任务</text>
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
  </view>
</template>

<script>
export default {
  data() {
    return {
      patientName: '张阿姨',
      patientId: 1,
      tasks: []
    }
  },
  
  onLoad() {
    this.loadTasks();
  },
  
  methods: {
    // 加载随访任务
    async loadTasks() {
      try {
        const res = await uni.request({
          url: `${this.$apiBase}/followup/tasks/patient/${this.patientId}`,
          method: 'GET'
        });
        
        if (res.data.success) {
          this.tasks = res.data.data;
        }
      } catch (error) {
        console.error('加载任务失败:', error);
        uni.showToast({
          title: '加载失败',
          icon: 'none'
        });
      }
    },
    
    // 格式化日期
    formatDate(dateStr) {
      if (!dateStr) return '-';
      const date = new Date(dateStr);
      return `${date.getMonth() + 1}月${date.getDate()}日`;
    },
    
    // 获取状态文本
    getStatusText(status) {
      const map = {
        'pending': '待完成',
        'in_progress': '进行中',
        'completed': '已完成',
        'overdue': '已逾期'
      };
      return map[status] || status;
    },
    
    // 获取状态样式
    getStatusClass(status) {
      return `status-${status}`;
    },
    
    // 跳转到任务详情
    goToTask(task) {
      uni.navigateTo({
        url: `/pages/task/task?id=${task.id}`
      });
    },
    
    // 跳转到其他页面
    goToPage(page) {
      uni.navigateTo({
        url: `/pages/${page}/${page}`
      });
    }
  }
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background: #f5f5f5;
  padding: 20rpx;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16rpx;
  padding: 40rpx;
  color: white;
  margin-bottom: 30rpx;
}

.title {
  font-size: 48rpx;
  font-weight: bold;
  display: block;
  margin-bottom: 16rpx;
}

.subtitle {
  font-size: 28rpx;
  opacity: 0.9;
}

.task-section, .quick-section {
  margin-bottom: 40rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 20rpx;
  padding-left: 10rpx;
}

.task-card {
  background: white;
  border-radius: 12rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.task-title {
  font-size: 32rpx;
  font-weight: bold;
}

.task-status {
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
  font-size: 24rpx;
}

.status-pending {
  background: #fff3e0;
  color: #f57c00;
}

.status-completed {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-overdue {
  background: #ffebee;
  color: #c62828;
}

.task-content {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-bottom: 20rpx;
}

.task-desc {
  font-size: 28rpx;
  color: #666;
}

.task-date {
  font-size: 24rpx;
  color: #999;
}

.task-action button {
  width: 100%;
}

.completed-text {
  color: #4caf50;
  font-size: 28rpx;
  text-align: center;
  display: block;
}

.empty-state {
  text-align: center;
  padding: 80rpx 0;
  color: #999;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}

.quick-item {
  background: white;
  border-radius: 12rpx;
  padding: 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
  box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
}

.quick-icon {
  font-size: 64rpx;
}

.quick-text {
  font-size: 28rpx;
  color: #333;
}
</style>

