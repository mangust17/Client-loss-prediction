<template>
  <div class="form">
    <input type="file" @change="handleFileUpload" accept=".csv" />
    <button @click="uploadCsv" :disabled="!csvFile">Предсказать для CSV</button>

    <NotificationBanner 
      v-if="error"
      :message="error"
      :isError="true"
    />

    <div ref="resultSection">
      <div v-if="csvResult.length" class="predictions-section">
        <h2>Результаты предсказаний</h2>
        <ReportDownload :predictions="csvResult" :plots="plotImages" />
        <table>
          <thead>
            <tr><th>Клиент</th><th>Отток</th><th>Вероятность</th></tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in csvResult" :key="i">
              <td>{{ row.id }}</td>
              <td>{{ row.churn ? 'Да' : 'Нет' }}</td>
              <td>{{ (row.probability * 100).toFixed(2) }}%</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="plots" class="plots-section">
        <h2>Графики анализа</h2>
        <PlotSection :plots="plots" @plots-rendered="handlePlotsRendered" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import axios from 'axios'
import * as Plotly from 'plotly.js-dist-min'
import PlotSection from './PlotSection.vue'
import ReportDownload from './ReportDownload.vue'
import NotificationBanner from './NotificationBanner.vue'
import '../assets/styles/main.css'

const API_BASE = import.meta.env.VITE_API_BASE;

const csvFile = ref(null)
const csvResult = ref([])
const plots = ref(null)
const plotImages = ref({})
const resultSection = ref(null)
const error = ref(null)

const handleFileUpload = (e) => {
  csvFile.value = e.target.files[0]
  error.value = null
}

const uploadCsv = async () => {
  try {
    error.value = null
    const form = new FormData()
    form.append('file', csvFile.value)
    const res = await axios.post(`${API_BASE}/predict-batch`, form)

    csvResult.value = res.data.predictions
    plots.value = res.data.plots

    await nextTick()
    resultSection.value?.scrollIntoView({ behavior: 'smooth' })
  } catch (err) {
    console.error('Ошибка при загрузке CSV:', err)
    if (err.response?.data?.detail) {
      error.value = err.response.data.detail
    } else if (err.response?.status === 422) {
      error.value = 'Файл имеет неправильный формат или отсутствуют необходимые поля. Пожалуйста, проверьте структуру CSV файла.'
    } else {
      error.value = 'Произошла ошибка при обработке файла. Пожалуйста, попробуйте еще раз.'
    }
  }
}

const handlePlotsRendered = async (plotRefs) => {
  try {
    plotImages.value = {
      probability_distribution: await Plotly.toImage(plotRefs.probabilityPlot, { format: 'png', width: 800, height: 400 }),
      churn_ratio: await Plotly.toImage(plotRefs.churnPlot, { format: 'png', width: 800, height: 400 }),
      monthly_charges_boxplot: await Plotly.toImage(plotRefs.chargesPlot, { format: 'png', width: 800, height: 400 })
    }
  } catch (error) {
    console.error('Ошибка при создании изображений графиков:', error)
  }
}
</script>
