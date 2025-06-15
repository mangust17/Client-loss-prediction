<template>
  <div class="form">
    <NotificationBanner 
      v-if="error"
      :message="error"
      :isError="true"
    />

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
    <input type="number" v-model.number="formData.monthly_charges" @input="updateTotalCharges" />

    <label>Общие платежи (авто):</label>
    <input type="number" :value="formData.total_charges" readonly />

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

    <div v-if="result" ref="resultBlock" class="predictions-section">
      <h2>Результат</h2>
      <p><strong>Отток:</strong> {{ result.churn ? 'Да' : 'Нет' }}</p>
      <p><strong>Вероятность:</strong> {{ (result.probability * 100).toFixed(2) }}%</p>
      
      <NotificationBanner 
        message="Обратите внимание: предсказания модели являются теоретическими и могут содержать погрешности. Результаты следует использовать как ориентировочные данные для принятия решений."
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import axios from 'axios'
import NotificationBanner from './NotificationBanner.vue'
import '../assets/styles/main.css'

const API_BASE = import.meta.env.VITE_API_BASE;

const formData = ref({
  type: 0,
  paperless_billing: 1,
  payment_method: 0,
  monthly_charges: 50.0,
  total_charges: 600.0,
  contract_length_days: 180,
  senior_citizen: 0,
  partner: 1,
  dependents: 0,
  MultipleLines: 1
})

const result = ref(null)
const resultBlock = ref(null)
const error = ref(null)

const updateTotalCharges = () => {
  formData.value.total_charges = +(formData.value.monthly_charges * 12).toFixed(2)
}

const predictChurn = async () => {
  try {
    error.value = null
    const response = await axios.post(`${API_BASE}/predict`, formData.value)
    result.value = response.data
    await nextTick()
    resultBlock.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  } catch (err) {
    console.error("Ошибка:", err)
    if (err.response?.data?.detail) {
      error.value = err.response.data.detail
    } else if (err.response?.status === 422) {
      error.value = 'Пожалуйста, проверьте правильность введенных данных. Все поля должны быть заполнены корректно.'
    } else {
      error.value = 'Произошла ошибка при обработке запроса. Пожалуйста, попробуйте еще раз.'
    }
  }
}

watch(() => formData.value.monthly_charges, updateTotalCharges, { immediate: true })
</script>
