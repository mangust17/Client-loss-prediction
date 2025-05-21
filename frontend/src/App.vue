<template>
  <div class="container">
    <h1>Предсказание оттока клиентов</h1>
    <div class="form-mode-toggle">
      <button @click="mode = 'single'">Одиночный клиент</button>
      <button @click="mode = 'bulk'">CSV-файл</button>
    </div>

    <transition name="fade" mode="out-in">
      <component :is="currentComponent" />
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import SingleClientForm from './components/SingleClientForm.vue'
import BulkClientForm from './components/BulkClientForm.vue'

const mode = ref('single')

const currentComponent = computed(() =>
  mode.value === 'single' ? SingleClientForm : BulkClientForm
)
</script>
