<template>
  <button @click="downloadPdf" class="download-button">Скачать PDF-отчет</button>
</template>

<script setup>
import axios from 'axios'
const props = defineProps(['predictions', 'plots'])
const API_BASE = import.meta.env.VITE_API_BASE;

const downloadPdf = async () => {
  const response = await axios.post(`${API_BASE}/download-report`, {
    predictions: props.predictions,
    plots: props.plots
  }, { responseType: 'blob' })

  const blob = new Blob([response.data])
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'churn_report.pdf'
  link.click()
}
</script>
