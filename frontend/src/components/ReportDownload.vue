<template>
  <div class="report-download">
    <button @click="downloadReport">Скачать PDF отчет</button>
  </div>
</template>

<script setup>
import axios from 'axios'

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
</style>
