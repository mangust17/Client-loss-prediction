<template>
  <div class="form">
    <input type="file" @change="handleFileUpload" accept=".csv" />
    <button @click="uploadCsv" :disabled="!csvFile">Предсказать для CSV</button>

    <div ref="resultSection">
      <ReportDownload v-if="csvResult.length" :predictions="csvResult" :plots="plotImages" />
      <table v-if="csvResult.length">
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

      <PlotSection v-if="plots" :plots="plots" @plots-rendered="handlePlotsRendered" />
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import axios from 'axios'
import * as Plotly from 'plotly.js-dist-min'
import PlotSection from './PlotSection.vue'
import ReportDownload from './ReportDownload.vue'

const API_BASE = import.meta.env.VITE_API_BASE;

const csvFile = ref(null)
const csvResult = ref([])
const plots = ref(null)
const plotImages = ref({})
const resultSection = ref(null)

const handleFileUpload = (e) => csvFile.value = e.target.files[0]

const uploadCsv = async () => {
  try {
    const form = new FormData()
    form.append('file', csvFile.value)
    const res = await axios.post(`${API_BASE}/predict-batch`, form)

    csvResult.value = res.data.predictions
    plots.value = res.data.plots

    await nextTick()
    resultSection.value?.scrollIntoView({ behavior: 'smooth' })
  } catch (error) {
    console.error('Ошибка при загрузке CSV:', error)
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
