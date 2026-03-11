<template>
  <view class="report-page">
    <view class="card">
      <text class="card-title">上传检查报告</text>
      <text class="card-desc">请拍照或从相册选取您的检查报告、化验单等</text>
    </view>

    <view class="upload-section">
      <view class="upload-area" @tap="chooseImage">
        <text class="upload-icon">📸</text>
        <text class="upload-text">点击拍照或选择图片</text>
        <text class="upload-hint">支持 JPG、PNG 格式，最多 6 张</text>
      </view>

      <view v-if="previews.length" class="preview-grid">
        <view v-for="(img, i) in previews" :key="i" class="preview-item">
          <image :src="img" mode="aspectFill" class="preview-img" @tap="previewImage(i)" />
          <view class="remove-btn" @tap="removeImage(i)">✕</view>
          <view v-if="uploadStatus[i] === 'done'" class="status-done">✓</view>
          <view v-if="uploadStatus[i] === 'uploading'" class="status-uploading">...</view>
        </view>
      </view>

      <view class="type-select">
        <text class="label">报告类型</text>
        <picker :range="reportTypes" @change="onTypeChange">
          <view class="picker-value">{{ selectedType || '请选择报告类型' }}</view>
        </picker>
      </view>

      <view class="note-area">
        <text class="label">备注说明</text>
        <textarea v-model="note" placeholder="补充说明（可选）" class="textarea" />
      </view>

      <button
        class="submit-btn"
        :loading="submitting"
        :disabled="!uploadedPaths.length"
        @tap="submit"
      >
        提交报告 ({{ uploadedPaths.length }} 个文件)
      </button>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api.js';

export default {
  data() {
    return {
      previews: [],
      uploadedPaths: [],
      uploadStatus: [],
      submitting: false,
      note: '',
      selectedType: '',
      reportTypes: ['血液检查', '影像报告', 'CT/MRI', '病理报告', '肿瘤标志物', '其他'],
    };
  },

  methods: {
    chooseImage() {
      const remaining = 6 - this.previews.length;
      if (remaining <= 0) {
        uni.showToast({ title: '最多上传 6 张', icon: 'none' });
        return;
      }

      uni.chooseImage({
        count: remaining,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          for (const path of res.tempFilePaths) {
            const idx = this.previews.length;
            this.previews.push(path);
            this.uploadStatus.push('uploading');
            this.doUpload(path, idx);
          }
        },
      });
    },

    async doUpload(path, idx) {
      try {
        const res = await api.uploadFile(path);
        if (res.success) {
          this.uploadedPaths.push(path.split('/').pop());
          this.$set(this.uploadStatus, idx, 'done');
        } else {
          this.$set(this.uploadStatus, idx, 'fail');
        }
      } catch {
        this.$set(this.uploadStatus, idx, 'fail');
        uni.showToast({ title: '上传失败', icon: 'none' });
      }
    },

    removeImage(i) {
      this.previews.splice(i, 1);
      this.uploadStatus.splice(i, 1);
      if (this.uploadedPaths[i]) this.uploadedPaths.splice(i, 1);
    },

    previewImage(i) {
      uni.previewImage({ urls: this.previews, current: this.previews[i] });
    },

    onTypeChange(e) {
      this.selectedType = this.reportTypes[e.detail.value];
    },

    async submit() {
      if (!this.selectedType) {
        uni.showToast({ title: '请选择报告类型', icon: 'none' });
        return;
      }

      this.submitting = true;
      try {
        const allTasks = await api.getMyTasks('pending');
        const uploadTask = allTasks.success
          ? allTasks.data.find((t) => t.task_type === 'upload')
          : null;

        const res = await api.submitRecord({
          task_id: uploadTask ? uploadTask.id : 0,
          patient_id: api.getPatientId(),
          record_type: 'upload',
          record_data: { report_type: this.selectedType, note: this.note },
          uploaded_files: this.uploadedPaths,
        });

        if (res.success) {
          uni.showToast({ title: '提交成功', icon: 'success' });
          setTimeout(() => uni.navigateBack(), 1200);
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
.report-page { padding: 20rpx; }
.card {
  background: linear-gradient(135deg, #43a047, #66bb6a); color: white;
  border-radius: 16rpx; padding: 36rpx; margin-bottom: 20rpx;
}
.card-title { font-size: 36rpx; font-weight: bold; display: block; margin-bottom: 10rpx; }
.card-desc { font-size: 26rpx; opacity: 0.9; }
.upload-section {
  background: white; border-radius: 16rpx; padding: 36rpx;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.06);
}
.upload-area {
  border: 2rpx dashed #ccc; border-radius: 16rpx; padding: 60rpx;
  text-align: center; margin-bottom: 24rpx;
}
.upload-icon { font-size: 64rpx; display: block; margin-bottom: 12rpx; }
.upload-text { font-size: 30rpx; color: #333; display: block; }
.upload-hint { font-size: 24rpx; color: #999; display: block; margin-top: 8rpx; }
.preview-grid { display: flex; flex-wrap: wrap; gap: 16rpx; margin-bottom: 24rpx; }
.preview-item { position: relative; width: 200rpx; height: 200rpx; }
.preview-img { width: 100%; height: 100%; border-radius: 12rpx; }
.remove-btn {
  position: absolute; top: -10rpx; right: -10rpx;
  background: #ff4d4f; color: white; width: 40rpx; height: 40rpx;
  border-radius: 50%; font-size: 24rpx; text-align: center; line-height: 40rpx;
}
.status-done {
  position: absolute; bottom: 8rpx; right: 8rpx;
  background: #4caf50; color: white; width: 36rpx; height: 36rpx;
  border-radius: 50%; font-size: 24rpx; text-align: center; line-height: 36rpx;
}
.status-uploading {
  position: absolute; bottom: 8rpx; right: 8rpx;
  background: #1890ff; color: white; width: 36rpx; height: 36rpx;
  border-radius: 50%; font-size: 20rpx; text-align: center; line-height: 36rpx;
}
.type-select { margin-bottom: 24rpx; }
.label { display: block; font-size: 28rpx; font-weight: 500; margin-bottom: 12rpx; }
.picker-value {
  border: 1px solid #e0e0e0; border-radius: 12rpx; padding: 20rpx 24rpx;
  font-size: 28rpx; color: #333;
}
.note-area { margin-bottom: 24rpx; }
.textarea {
  width: 100%; border: 1px solid #e0e0e0; border-radius: 12rpx;
  padding: 20rpx; font-size: 28rpx; min-height: 100rpx; box-sizing: border-box;
}
.submit-btn {
  background: linear-gradient(135deg, #43a047, #66bb6a); color: white;
  border: none; border-radius: 12rpx; font-size: 30rpx; padding: 22rpx 0;
}
</style>
