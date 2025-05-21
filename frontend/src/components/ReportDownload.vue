<template>
  <button @click="downloadPdf" class="download-button">Скачать PDF-отчет</button>
</template>

<script setup>
import axios from 'axios'
const props = defineProps(['predictions', 'plots'])

const downloadPdf = async () => {
  const response = await axios.post("http://127.0.0.1:5000/download-report", {
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
