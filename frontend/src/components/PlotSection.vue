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
const probabilityPlot = ref(null)
const churnPlot = ref(null)
const chargesPlot = ref(null)

const renderPlots = () => {
  if (!props.plots) return
  const { probability_distribution, churn_ratio, monthly_charges_boxplot } = props.plots

  Plotly.newPlot(probabilityPlot.value, JSON.parse(probability_distribution).data, JSON.parse(probability_distribution).layout)
  Plotly.newPlot(churnPlot.value, JSON.parse(churn_ratio).data, JSON.parse(churn_ratio).layout)
  Plotly.newPlot(chargesPlot.value, JSON.parse(monthly_charges_boxplot).data, JSON.parse(monthly_charges_boxplot).layout)
}

onMounted(() => nextTick(renderPlots))
watch(() => props.plots, renderPlots)
</script>
