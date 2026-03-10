<script>
export default {
  onLaunch() {
    console.log('患者端启动');
    const token = uni.getStorageSync('patient_token');
    const pid = uni.getStorageSync('patient_id');
    if (!token || !pid) {
      uni.reLaunch({ url: '/pages/login/login' });
    }
  },
};
</script>

<style>
page {
  background: #f5f5f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
</style>
