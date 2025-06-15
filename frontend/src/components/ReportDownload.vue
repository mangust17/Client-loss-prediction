<template>
  <div class="report-download">
    <button @click="downloadReport" class="download-button">Скачать PDF отчет</button>
    <NotificationBanner 
      message="Обратите внимание: предсказания модели являются теоретическими и могут содержать погрешности. Результаты следует использовать как ориентировочные данные для принятия решений."
    />
  </div>
</template>

<script setup>
import axios from 'axios'
import NotificationBanner from './NotificationBanner.vue'
import '../assets/styles/main.css'

const props = defineProps({
  predictions: {
    type: Array,
    required: true
  },
  plots: {
    type: Object,
    required: true
  }
})

const downloadReport = async () => {
  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE}/download-report`,
      {
        predictions: props.predictions,
        plots: props.plots
      },
      {
        responseType: 'blob'
      }
    )

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'churn_analysis_report.pdf')
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    console.error('Ошибка при скачивании отчета:', error)
  }
}
</script>

<style scoped>
.report-download {
  margin: 1rem 0;
}

.download-button {
  padding: 0.5rem 1rem;
  background-color: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s;
}

.download-button:hover {
  background-color: #1976D2;
}
</style>
