<template>
  <div class="notification-banner" :class="{ 'error': isError }">
    <div class="notification-content">
      <span class="notification-icon">{{ isError ? '⚠️' : 'ℹ️' }}</span>
      <p>{{ message }}</p>
    </div>
  </div>
</template>

<script setup>
import '../assets/styles/main.css'

defineProps({
  message: {
    type: String,
    required: true
  },
  isError: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.notification-banner {
  padding: 1rem;
  margin: 1rem 0;
  border-radius: 8px;
  background-color: #f0f7ff;
  border: 1px solid #b3d4ff;
}

.notification-banner.error {
  background-color: #fff0f0;
  border-color: #ffb3b3;
}

.notification-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.notification-icon {
  font-size: 1.2rem;
}

p {
  margin: 0;
  color: #333;
  font-size: 0.9rem;
  line-height: 1.4;
}
</style> 