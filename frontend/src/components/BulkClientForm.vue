<template>
  <div class="form">
    <input type="file" @change="handleFileUpload" accept=".csv" />
    <button @click="uploadCsv" :disabled="!csvFile">Предсказать для CSV</button>
    <ReportDownload v-if="csvResult.length" :predictions="csvResult" :plots="plotImages" />

    <table v-if="csvResult.length">
      <thead><tr><th>Клиент</th><th>Отток</th><th>Вероятность</th></tr></thead>
      <tbody>
        <tr v-for="(row, i) in csvResult" :key="i">
          <td>{{ row.id }}</td><td>{{ row.churn ? 'Да' : 'Нет' }}</td><td>{{ (row.probability * 100).toFixed(2) }}%</td>
        </tr>
      </tbody>
    </table>

    <PlotSection v-if="plots" :plots="plots" />
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import axios from 'axios'
import PlotSection from './PlotSection.vue'
import ReportDownload from './ReportDownload.vue'

const csvFile = ref(null)
const csvResult = ref([])
const plots = ref(null)
const plotImages = ref({})

const handleFileUpload = (e) => csvFile.value = e.target.files[0]

const uploadCsv = async () => {
  const form = new FormData()
  form.append('file', csvFile.value)
  const res = await axios.post("http://127.0.0.1:5000/predict-batch", form)
  csvResult.value = res.data.predictions
  plots.value = res.data.plots
}
</script>
