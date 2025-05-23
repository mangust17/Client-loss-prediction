<template>
  <div class="form">
    <label>Тип оплаты:</label>
    <select v-model="formData.type">
      <option :value="0">Ежемесячно</option>
      <option :value="1">Раз в год-два</option>
    </select>

    <label>Электронный счёт:</label>
    <select v-model="formData.paperless_billing">
      <option :value="0">Нет</option>
      <option :value="1">Да</option>
    </select>

    <label>Метод оплаты:</label>
    <select v-model="formData.payment_method">
      <option :value="0">Банковская карта</option>
      <option :value="1">Счёт</option>
      <option :value="2">Электронный перевод</option>
      <option :value="3">Прочее</option>
    </select>

    <label>Ежемесячные платежи:</label>
    <input type="number" v-model.number="formData.monthly_charges" />

    <label>Общие платежи:</label>
    <input type="number" v-model.number="formData.total_charges" />

    <label>Продолжительность контракта (дней):</label>
    <input type="number" v-model.number="formData.contract_length_days" />

    <label>Пенсионер:</label>
    <select v-model="formData.senior_citizen">
      <option :value="0">Нет</option>
      <option :value="1">Да</option>
    </select>

    <label>Есть партнёр:</label>
    <select v-model="formData.partner">
      <option :value="0">Нет</option>
      <option :value="1">Да</option>
    </select>

    <label>Есть дети:</label>
    <select v-model="formData.dependents">
      <option :value="0">Нет</option>
      <option :value="1">Да</option>
    </select>

    <label>Множественные телефонные линии:</label>
    <select v-model="formData.MultipleLines">
      <option :value="0">Нет</option>
      <option :value="1">Да</option>
    </select>

    <button @click="predictChurn">Предсказать</button>

    <!-- Результат и точка прокрутки -->
    <div v-if="result" ref="resultBlock" style="margin-top: 2rem;">
      <h2>Результат</h2>
      <p><strong>Отток:</strong> {{ result.churn ? 'Да' : 'Нет' }}</p>
      <p><strong>Вероятность:</strong> {{ (result.probability * 100).toFixed(2) }}%</p>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE;

const formData = ref({
  type: 0,
  paperless_billing: 1,
  payment_method: 0,
  monthly_charges: 50.0,
  total_charges: 250.0,
  contract_length_days: 180,
  senior_citizen: 0,
  partner: 1,
  dependents: 0,
  MultipleLines: 1
})

const result = ref(null)
const resultBlock = ref(null)

const predictChurn = async () => {
  try {
    const response = await axios.post(`${API_BASE}/predict`, formData.value)
    result.value = response.data
    await nextTick()
    resultBlock.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  } catch (err) {
    console.error("Ошибка:", err)
  }
}
</script>
