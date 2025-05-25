<template>
  <div class="plots-container">
    <div class="plot" ref="probabilityPlot"></div>
    <div class="plot" ref="churnPlot"></div>
    <div class="plot" ref="chargesPlot"></div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch, nextTick } from 'vue'
import * as Plotly from 'plotly.js-dist-min'

const props = defineProps(['plots'])
const emit = defineEmits(['plots-rendered'])

const probabilityPlot = ref(null)
const churnPlot = ref(null)
const chargesPlot = ref(null)

const renderPlots = async () => {
  if (!props.plots) return
  
  try {
    const { probability_distribution, churn_ratio, monthly_charges_boxplot } = props.plots

    await Plotly.newPlot(probabilityPlot.value, JSON.parse(probability_distribution).data, JSON.parse(probability_distribution).layout)
    await Plotly.newPlot(churnPlot.value, JSON.parse(churn_ratio).data, JSON.parse(churn_ratio).layout)
    await Plotly.newPlot(chargesPlot.value, JSON.parse(monthly_charges_boxplot).data, JSON.parse(monthly_charges_boxplot).layout)

    emit('plots-rendered', {
      probabilityPlot: probabilityPlot.value,
      churnPlot: churnPlot.value,
      chargesPlot: chargesPlot.value
    })
  } catch (error) {
    console.error('Ошибка при отрисовке графиков:', error)
  }
}

onMounted(() => nextTick(renderPlots))
watch(() => props.plots, renderPlots)
</script>


