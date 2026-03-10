<template>
  <view class="health-page">
    <view class="card">
      <text class="card-title">术后健康自评问卷</text>
      <text class="card-desc">请如实填写，帮助医生了解您的恢复情况</text>
    </view>

    <view class="form-card">
      <view class="q-item" v-for="(q, i) in questions" :key="i">
        <text class="q-label">{{ i + 1 }}. {{ q.label }}</text>
        <view class="q-options">
          <view
            v-for="opt in q.options"
            :key="opt.value"
            class="q-chip"
            :class="{ active: answers[q.key] === opt.value }"
            @tap="answers[q.key] = opt.value"
          >
            {{ opt.label }}
          </view>
        </view>
      </view>

      <view class="q-item">
        <text class="q-label">其他症状或想说的话</text>
        <textarea v-model="note" placeholder="请描述..." class="textarea" />
      </view>

      <button class="submit-btn" :loading="submitting" @tap="submit">提交问卷</button>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api.js';

export default {
  data() {
    return {
      submitting: false,
      note: '',
      answers: {},
      questions: [
        { key: 'energy', label: '精力状况', options: [
          { value: 5, label: '精力充沛' }, { value: 4, label: '比较好' },
          { value: 3, label: '一般' }, { value: 2, label: '容易疲劳' }, { value: 1, label: '非常疲劳' },
        ]},
        { key: 'pain_score', label: '疼痛评分', options: [
          { value: 0, label: '无痛' }, { value: 1, label: '轻微' },
          { value: 2, label: '中等' }, { value: 3, label: '严重' },
        ]},
        { key: 'bleeding', label: '阴道出血', options: [
          { value: 'none', label: '无' }, { value: 'spotting', label: '点滴出血' },
          { value: 'moderate', label: '中等出血' }, { value: 'heavy', label: '大量出血' },
        ]},
        { key: 'appetite', label: '食欲', options: [
          { value: 'good', label: '正常' }, { value: 'fair', label: '略差' },
          { value: 'poor', label: '明显减退' }, { value: 'none', label: '几乎无食欲' },
        ]},
        { key: 'bowel', label: '排便情况', options: [
          { value: 'normal', label: '正常' }, { value: 'constipation', label: '便秘' },
          { value: 'diarrhea', label: '腹泻' }, { value: 'both', label: '交替出现' },
        ]},
        { key: 'urination', label: '排尿情况', options: [
          { value: 'normal', label: '正常' }, { value: 'frequent', label: '尿频' },
          { value: 'painful', label: '尿痛' }, { value: 'difficult', label: '排尿困难' },
        ]},
        { key: 'mood', label: '情绪状态', options: [
          { value: 'good', label: '良好' }, { value: 'anxious', label: '焦虑' },
          { value: 'depressed', label: '低落' }, { value: 'insomnia', label: '失眠' },
        ]},
        { key: 'wound', label: '伤口恢复', options: [
          { value: 'healed', label: '已愈合' }, { value: 'healing', label: '恢复中' },
          { value: 'red', label: '红肿' }, { value: 'infected', label: '疑似感染' },
        ]},
      ],
    };
  },

  methods: {
    async submit() {
      const unanswered = this.questions.filter((q) => this.answers[q.key] == null);
      if (unanswered.length) {
        uni.showToast({ title: `请回答"${unanswered[0].label}"`, icon: 'none' });
        return;
      }

      this.submitting = true;
      try {
        const allTasks = await api.getMyTasks('pending');
        const qTask = allTasks.success
          ? allTasks.data.find((t) => t.task_type === 'questionnaire')
          : null;

        const res = await api.submitRecord({
          task_id: qTask ? qTask.id : 0,
          patient_id: api.getPatientId(),
          record_type: 'questionnaire',
          record_data: { source: 'health_self_report', note: this.note },
          questionnaire_answers: this.answers,
        });

        if (res.success) {
          uni.showToast({ title: '提交成功，感谢！', icon: 'success' });
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
.health-page { padding: 20rpx; }
.card {
  background: linear-gradient(135deg, #667eea, #764ba2); color: white;
  border-radius: 16rpx; padding: 36rpx; margin-bottom: 20rpx;
}
.card-title { font-size: 36rpx; font-weight: bold; display: block; margin-bottom: 10rpx; }
.card-desc { font-size: 26rpx; opacity: 0.9; }
.form-card {
  background: white; border-radius: 16rpx; padding: 36rpx;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.06);
}
.q-item { margin-bottom: 36rpx; }
.q-label { display: block; font-size: 28rpx; font-weight: 500; margin-bottom: 16rpx; }
.q-options { display: flex; flex-wrap: wrap; gap: 12rpx; }
.q-chip {
  padding: 14rpx 28rpx; border: 1px solid #e0e0e0; border-radius: 30rpx;
  font-size: 26rpx; color: #666; background: #fafafa;
}
.q-chip.active {
  background: #667eea; color: white; border-color: #667eea;
}
.textarea {
  width: 100%; border: 1px solid #e0e0e0; border-radius: 12rpx;
  padding: 20rpx; font-size: 28rpx; min-height: 120rpx; box-sizing: border-box;
}
.submit-btn {
  background: linear-gradient(135deg, #667eea, #764ba2); color: white;
  border: none; border-radius: 12rpx; font-size: 30rpx; padding: 22rpx 0; margin-top: 16rpx;
}
</style>
