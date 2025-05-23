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

  const config = { responsive: true }

  const parse = (plot) => ({
    data: JSON.parse(plot).data,
    layout: {
      ...JSON.parse(plot).layout,
      autosize: true,
      width: null,
      height: null,
    }
  })

  Plotly.newPlot(probabilityPlot.value, ...Object.values(parse(props.plots.probability_distribution)), config)
  Plotly.newPlot(churnPlot.value, ...Object.values(parse(props.plots.churn_ratio)), config)
  Plotly.newPlot(chargesPlot.value, ...Object.values(parse(props.plots.monthly_charges_boxplot)), config)
}

onMounted(() => nextTick(renderPlots))
watch(() => props.plots, renderPlots)
</script>

