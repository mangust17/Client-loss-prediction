<template>
  <div class="app-wrapper">
    <div class="container">
      <h1>Предсказание оттока клиентов</h1>

      <div class="form-mode-toggle">
        <button @click="mode = 'single'">Одиночный клиент</button>
        <button @click="mode = 'bulk'">CSV-файл</button>
      </div>

      <div v-if="mode === 'single'" class="form">
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

        <div v-if="result">
          <h2>Результат</h2>
          <p><strong>Отток:</strong> {{ result.churn ? "Да" : "Нет" }}</p>
          <p><strong>Вероятность:</strong> {{ (result.probability * 100).toFixed(2) }}%</p>
        </div>
      </div>

      <div v-if="mode === 'bulk'" class="form">
        <label>Загрузите CSV-файл с пользователями:</label>
        <div class="file-upload-container">
          <input type="file" @change="handleFileUpload" accept=".csv" />
          <a href="#" @click.prevent="downloadSampleCsv" class="download-sample">
            Скачать пример CSV файла
          </a>
        </div>
        <button @click="uploadCsv" :disabled="!csvFile">Предсказать для CSV</button>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div v-if="csvResult.length">
          <h2>Результаты предсказания</h2>
          <div class="actions-container">
            <button @click="downloadPdfReport" class="download-button">
              Скачать PDF-отчет
            </button>
          </div>
          <table>
            <thead>
              <tr><th>Клиент</th><th>Отток</th><th>Вероятность</th></tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in csvResult" :key="index">
                <td>{{ row.id }}</td>
                <td>{{ row.churn ? 'Да' : 'Нет' }}</td>
                <td>{{ (row.probability * 100).toFixed(2) }}%</td>
              </tr>
            </tbody>
          </table>

          <h2>Визуализация результатов</h2>
          <div class="plots-container">
            <div class="plot">
              <h3>Распределение вероятностей оттока</h3>
              <div ref="probabilityPlot" style="width: 100%; height: 400px;"></div>
            </div>
            <div class="plot">
              <h3>Соотношение оттока клиентов</h3>
              <div ref="churnPlot" style="width: 100%; height: 400px;"></div>
            </div>
            <div class="plot">
              <h3>Распределение ежемесячных платежей</h3>
              <div ref="chargesPlot" style="width: 100%; height: 400px;"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue';
import axios from 'axios';
import * as Plotly from 'plotly.js-dist-min';

const mode = ref('single');
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
});
const result = ref(null);
const csvFile = ref(null);
const csvResult = ref([]);
const error = ref(null);
const plots = ref(null);

const probabilityPlot = ref(null);
const churnPlot = ref(null);
const chargesPlot = ref(null);

onMounted(() => {
  nextTick(() => {
    if (probabilityPlot.value) {
      Plotly.newPlot(probabilityPlot.value, [], { title: 'Распределение вероятностей оттока' });
    }
    if (churnPlot.value) {
      Plotly.newPlot(churnPlot.value, [], { title: 'Соотношение оттока клиентов' });
    }
    if (chargesPlot.value) {
      Plotly.newPlot(chargesPlot.value, [], { title: 'Распределение ежемесячных платежей' });
    }
  });
});

const predictChurn = async () => {
  try {
    error.value = null;
    const response = await axios.post("http://127.0.0.1:5000/predict", formData.value);
    result.value = response.data;
  } catch (err) {
    error.value = err.response?.data?.error || "Произошла ошибка при отправке запроса";
    console.error("Ошибка:", err);
  }
};

const handleFileUpload = (event) => {
  error.value = null;
  csvFile.value = event.target.files[0];
};

const uploadCsv = async () => {
  if (!csvFile.value) return;
  
  error.value = null;
  csvResult.value = [];
  plots.value = null;
  
  const form = new FormData();
  form.append("file", csvFile.value);
  
  try {
    const response = await axios.post("http://127.0.0.1:5000/predict-batch", form, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    if (response.data.error) {
      error.value = response.data.error;
      return;
    }
    
    csvResult.value = response.data.predictions;
    plots.value = response.data.plots;
    
    if (response.data.plots) {
      await nextTick(); 
      
      try {
        const probabilityData = JSON.parse(response.data.plots.probability_distribution);
        const churnData = JSON.parse(response.data.plots.churn_ratio);
        const chargesData = JSON.parse(response.data.plots.monthly_charges_boxplot);

        if (!probabilityPlot.value || !churnPlot.value || !chargesPlot.value) {
          error.value = "Элементы для графиков не найдены";
          return;
        }

        Plotly.newPlot(probabilityPlot.value, probabilityData.data, probabilityData.layout);
        Plotly.newPlot(churnPlot.value, churnData.data, churnData.layout);
        Plotly.newPlot(chargesPlot.value, chargesData.data, chargesData.layout);
      } catch (plotError) {
        console.error("Ошибка при отображении графиков:", plotError);
        error.value = "Ошибка при отображении графиков";
      }
    }
  } catch (err) {
    error.value = err.response?.data?.error || "Произошла ошибка при загрузке файла";
    console.error("Ошибка загрузки csv:", err);
  }
};

const downloadSampleCsv = () => {
  const headers = ['type', 'paperless_billing', 'payment_method', 'monthly_charges', 
                  'total_charges', 'contract_length_days', 'senior_citizen', 
                  'partner', 'dependents', 'MultipleLines'];
  
  const sampleData = [
    ['Month-to-month', 'Yes', 'Electronic check', '50.55', '150.65', '30', 'No', 'Yes', 'No', 'No'],
    ['One year', 'No', 'Bank transfer (automatic)', '75.20', '902.40', '365', 'Yes', 'No', 'Yes', 'Yes'],
    ['Two year', 'Yes', 'Credit card (automatic)', '100.35', '2408.40', '730', 'No', 'Yes', 'No', 'Yes']
  ];

  const csvContent = [
    headers.join(','),
    ...sampleData.map(row => row.join(','))
  ].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.setAttribute('download', 'sample_customers.csv');
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const downloadPdfReport = async () => {
  try {
    error.value = null;
    const response = await axios.post(
      "http://127.0.0.1:5000/download-report",
      {
        predictions: csvResult.value,
        plots: plots.value
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

watch(mode, () => {
  if (probabilityPlot.value) Plotly.purge(probabilityPlot.value);
  if (churnPlot.value) Plotly.purge(churnPlot.value);
  if (chargesPlot.value) Plotly.purge(chargesPlot.value);
});
</script>

<style>
.app-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  width: 100%;
}

.container { 
  padding: 20px;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.single-center-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}

.form { 
  display: flex; 
  flex-direction: column; 
  align-items: center;
  width: 100%; 
  max-width: 400px; 
  margin: 0 auto; 
  text-align: left;
}

input, select, button { 
  margin: 5px 0; 
  padding: 10px; 
  font-size: 16px; 
  width: 100%;
  box-sizing: border-box;
}

button { 
  background-color: #42b983; 
  color: white; 
  border: none; 
  cursor: pointer; 
}

.form-mode-toggle { 
  display: flex; 
  gap: 20px; 
  justify-content: center; 
  margin-bottom: 20px; 
}

table { 
  margin: 20px auto; 
  border-collapse: collapse; 
  width: 90%; 
  text-align: center;
}

th, td { 
  border: 1px solid #ccc; 
  padding: 8px; 
  text-align: center; 
}

th { 
  background-color: #eee; 
}

.plots-container {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 30px;
  margin-top: 30px;
  padding: 20px;
  width: 100%;
}

.plot {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 600px;
  height: 500px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.plot h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #2c3e50;
  font-size: 1.2em;
  text-align: center;
}

.plot div {
  width: 100%;
  height: 450px;
  flex-grow: 1;
}

.error-message {
  color: #dc3545;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
  padding: 10px;
  margin: 10px 0;
  text-align: center;
}

.file-upload-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin: 10px 0;
}

.download-sample {
  color: #42b983;
  text-decoration: none;
  font-size: 14px;
}

.download-sample:hover {
  text-decoration: underline;
}

.actions-container {
  margin: 20px 0;
  display: flex;
  justify-content: center;
  gap: 10px;
}

.download-button {
  background-color: #2c3e50;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s;
}

.download-button:hover {
  background-color: #34495e;
}
</style>
