<template>
  <div class="container">
    <h1>Предсказание оттока клиентов</h1>
    <div class="form-mode-toggle">
      <button @click="mode = 'single'">Одиночный клиент</button>
      <button @click="mode = 'bulk'">CSV-файл</button>
    </div>

    <transition name="fade" mode="out-in">
      <component 
        :is="currentComponent" 
        :plots="plots"
        :error="error"
        :csvResult="csvResult"
        :probabilityPlot="probabilityPlot"
        :churnPlot="churnPlot"
        :chargesPlot="chargesPlot"
        @update:plots="plots = $event"
        @update:error="error = $event"
        @update:csvResult="csvResult = $event"
        @download-report="downloadPdfReport"
      />
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import SingleClientForm from './components/SingleClientForm.vue'
import BulkClientForm from './components/BulkClientForm.vue'
import axios from 'axios'
import * as Plotly from 'plotly.js-dist-min'

const mode = ref('single')
const error = ref(null)
const plots = ref(null)
const csvResult = ref([])
const probabilityPlot = ref(null)
const churnPlot = ref(null)
const chargesPlot = ref(null)

const currentComponent = computed(() =>
  mode.value === 'single' ? SingleClientForm : BulkClientForm
)

const downloadPdfReport = async () => {
  try {
    error.value = null;

    // Получаем изображения графиков
    const plotImages = {};
    
    if (plots.value) {
      const probabilityData = JSON.parse(plots.value.probability_distribution);
      const churnData = JSON.parse(plots.value.churn_ratio);
      const chargesData = JSON.parse(plots.value.monthly_charges_boxplot);

      const probabilityImg = await Plotly.toImage(probabilityPlot.value, {
        format: 'png',
        width: 800,
        height: 400
      });
      plotImages.probability_distribution = probabilityImg;
      
      const churnImg = await Plotly.toImage(churnPlot.value, {
        format: 'png',
        width: 800,
        height: 400
      });
      plotImages.churn_ratio = churnImg;
      
      const chargesImg = await Plotly.toImage(chargesPlot.value, {
        format: 'png',
        width: 800,
        height: 400
      });
      plotImages.monthly_charges_boxplot = chargesImg;
    }

    const response = await axios.post(
      "http://127.0.0.1:5000/download-report",
      {
        predictions: csvResult.value,
        plots: plotImages
      },
      { responseType: 'blob' }
    );
    
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'churn_analysis_report.pdf');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (err) {
    error.value = "Ошибка при скачивании отчета";
    console.error("Ошибка:", err);
  }
};
</script>
