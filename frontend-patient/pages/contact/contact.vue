<template>
  <view class="contact-page">
    <view class="doctor-card" v-if="patient">
      <view class="doctor-avatar">👨‍⚕️</view>
      <view class="doctor-info">
        <text class="doctor-name">{{ patient.attending_doctor || '主治医生' }}</text>
        <text class="doctor-dept">{{ patient.department || '妇科肿瘤科' }}</text>
        <text class="doctor-hospital">{{ patient.hospital || '医院' }}</text>
      </view>
    </view>

    <view class="action-list">
      <view class="action-item" @tap="callDoctor">
        <text class="action-icon">📞</text>
        <view class="action-text">
          <text class="action-title">电话咨询</text>
          <text class="action-desc">工作日 8:00 - 17:00</text>
        </view>
        <text class="action-arrow">›</text>
      </view>

      <view class="action-item" @tap="goMessage">
        <text class="action-icon">💬</text>
        <view class="action-text">
          <text class="action-title">留言咨询</text>
          <text class="action-desc">医生将在24小时内回复</text>
        </view>
        <text class="action-arrow">›</text>
      </view>

      <view class="action-item" @tap="goEmergency">
        <text class="action-icon">🚨</text>
        <view class="action-text">
          <text class="action-title">紧急情况</text>
          <text class="action-desc">出现严重症状请立即拨打</text>
        </view>
        <text class="action-arrow">›</text>
      </view>
    </view>

    <!-- 留言区 -->
    <view v-if="showMessage" class="message-section">
      <text class="section-title">给医生留言</text>
      <textarea v-model="messageText" placeholder="描述您的问题或症状..." class="textarea" />
      <button class="send-btn" :loading="sending" @tap="sendMessage">发送留言</button>
    </view>

    <view class="info-card">
      <text class="info-title">温馨提示</text>
      <text class="info-item">• 术后出现大量出血请立即就医</text>
      <text class="info-item">• 体温超过 38.5°C 持续不退请及时就诊</text>
      <text class="info-item">• 伤口出现红肿、渗液请拍照上传</text>
      <text class="info-item">• 按时服药，不要自行停药或减量</text>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api.js';

export default {
  data() {
    return {
      patient: null,
      showMessage: false,
      messageText: '',
      sending: false,
    };
  },

  onLoad() {
    this.loadInfo();
  },

  methods: {
    async loadInfo() {
      try {
        const res = await api.getPatientInfo();
        if (res.success) this.patient = res.data;
      } catch (e) {
        console.error(e);
      }
    },

    callDoctor() {
      uni.makePhoneCall({
        phoneNumber: '0971-12345678',
        fail: () => {
          uni.showToast({ title: '请拨打 0971-12345678', icon: 'none', duration: 3000 });
        },
      });
    },

    goMessage() {
      this.showMessage = !this.showMessage;
    },

    goEmergency() {
      uni.showModal({
        title: '紧急情况',
        content: '如出现大出血、剧烈疼痛、高热等紧急症状，请立即拨打 120 或前往最近医院急诊。',
        confirmText: '拨打 120',
        cancelText: '知道了',
        success: (res) => {
          if (res.confirm) {
            uni.makePhoneCall({ phoneNumber: '120' });
          }
        },
      });
    },

    async sendMessage() {
      if (!this.messageText.trim()) {
        uni.showToast({ title: '请输入留言内容', icon: 'none' });
        return;
      }

      this.sending = true;
      try {
        const res = await api.submitRecord({
          task_id: 0,
          patient_id: api.getPatientId(),
          record_type: 'message',
          record_data: { message: this.messageText, timestamp: new Date().toISOString() },
        });
        if (res.success) {
          uni.showToast({ title: '留言已发送', icon: 'success' });
          this.messageText = '';
          this.showMessage = false;
        }
      } catch (e) {
        console.error(e);
      } finally {
        this.sending = false;
      }
    },
  },
};
</script>

<style scoped>
.contact-page { padding: 20rpx; }
.doctor-card {
  background: white; border-radius: 16rpx; padding: 36rpx;
  display: flex; align-items: center; gap: 28rpx; margin-bottom: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.06);
}
.doctor-avatar { font-size: 80rpx; }
.doctor-info { flex: 1; }
.doctor-name { display: block; font-size: 34rpx; font-weight: bold; margin-bottom: 8rpx; }
.doctor-dept { display: block; font-size: 26rpx; color: #667eea; margin-bottom: 4rpx; }
.doctor-hospital { display: block; font-size: 24rpx; color: #999; }

.action-list { margin-bottom: 20rpx; }
.action-item {
  background: white; border-radius: 12rpx; padding: 30rpx;
  display: flex; align-items: center; gap: 24rpx; margin-bottom: 12rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04);
}
.action-icon { font-size: 48rpx; }
.action-text { flex: 1; }
.action-title { display: block; font-size: 30rpx; font-weight: 500; margin-bottom: 4rpx; }
.action-desc { display: block; font-size: 24rpx; color: #999; }
.action-arrow { font-size: 36rpx; color: #ccc; }

.message-section {
  background: white; border-radius: 16rpx; padding: 36rpx; margin-bottom: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.06);
}
.section-title { font-size: 30rpx; font-weight: bold; display: block; margin-bottom: 16rpx; }
.textarea {
  width: 100%; border: 1px solid #e0e0e0; border-radius: 12rpx;
  padding: 20rpx; font-size: 28rpx; min-height: 150rpx; box-sizing: border-box;
  margin-bottom: 16rpx;
}
.send-btn {
  background: linear-gradient(135deg, #667eea, #764ba2); color: white;
  border: none; border-radius: 12rpx; font-size: 30rpx; padding: 20rpx 0;
}

.info-card {
  background: #fff8e1; border-radius: 16rpx; padding: 30rpx;
  border-left: 6rpx solid #ffc107;
}
.info-title { font-size: 30rpx; font-weight: bold; display: block; margin-bottom: 16rpx; color: #f57c00; }
.info-item { display: block; font-size: 26rpx; color: #666; line-height: 2; }
</style>
