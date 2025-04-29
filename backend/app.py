from flask import Flask, request, jsonify, send_file
import pickle
import pandas as pd
from flask_cors import CORS
import os
import matplotlib.pyplot as plt
import io
import seaborn as sns
import logging
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
from plotly.utils import PlotlyJSONEncoder
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
import tempfile
import plotly.io as pio

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

CATEGORY_MAPPINGS = {
    'type': {
        'Month-to-month': 0,
        'One year': 1,
        'Two year': 1
    },
    'paperless_billing': {
        'No': 0,
        'Yes': 1
    },
    'payment_method': {
        'Bank transfer (automatic)': 0,
        'Credit card (automatic)': 0,
        'Electronic check': 2,
        'Mailed check': 3
    },
    'senior_citizen': {
        'No': 0,
        'Yes': 1
    },
    'partner': {
        'No': 0,
        'Yes': 1
    },
    'dependents': {
        'No': 0,
        'Yes': 1
    },
    'MultipleLines': {
        'No': 0,
        'Yes': 1,
        'No phone service': 0
    }
}

model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
with open(model_path, "rb") as file:
    model = pickle.load(file)

model_features = model.feature_names_in_

def preprocess_data(df):
    """Предварительная обработка данных"""
    df = df.copy()
    for column, mapping in CATEGORY_MAPPINGS.items():
        if column in df.columns:
            if df[column].dtype in ['int64', 'float64']:
                continue
            df[column] = df[column].map(mapping)
            if df[column].isna().any():
                logger.warning(f"Найдены неизвестные значения в колонке {column}")
                df[column] = df[column].fillna(0)

    numeric_columns = ['monthly_charges', 'total_charges', 'contract_length_days']
    for column in numeric_columns:
        if column in df.columns:
            if df[column].dtype == 'object':
                df[column] = df[column].replace('[\$,]', '', regex=True).str.strip()
            df[column] = pd.to_numeric(df[column], errors='coerce')
            if df[column].isna().any():
                logger.warning(f"Найдены пропущенные значения в колонке {column}")
                df[column] = df[column].fillna(df[column].median())

    return df

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def index():
    return "Сервер работает"

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        df = pd.DataFrame([data])
        df = preprocess_data(df)
        prediction = model.predict(df)
        probability = model.predict_proba(df)[:, 1]
        return jsonify({
            "churn": int(prediction[0]),
            "probability": float(probability[0])
        })
    
    except Exception as e:
        logger.error(f"Ошибка в /predict: {str(e)}")
        return jsonify({"error": str(e)}), 400


@app.route("/predict-batch", methods=["POST"])
def predict_batch():
    try:
        logger.info("Получен запрос на /predict-batch")
        
        if 'file' not in request.files:
            logger.error("Файл не найден в запросе")
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.error("Пустое имя файла")
            return jsonify({"error": "No file selected"}), 400
        
        logger.info(f"Чтение файла: {file.filename}")
        df = pd.read_csv(file)
        logger.info(f"Прочитано строк: {len(df)}")
        logger.info(f"Колонки в файле: {df.columns.tolist()}")
        logger.info(f"Требуемые колонки модели: {model_features.tolist()}")
        
        missing_features = set(model_features) - set(df.columns)
        if missing_features:
            error_msg = f"В CSV отсутствуют следующие колонки: {', '.join(missing_features)}"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 400
        
        df = preprocess_data(df)
        df = df[model_features]
        predictions = model.predict(df)
        probabilities = model.predict_proba(df)[:, 1]
        results = pd.DataFrame({
            'id': range(len(df)),
            'churn': predictions,
            'probability': probabilities
        })

        plots = create_visualizations(df, predictions, probabilities)

        results = {
            'predictions': results.to_dict('records'),
            'plots': plots
        }
        
        logger.info("Предсказания успешно выполнены")
        return jsonify(results)
    
    except pd.errors.EmptyDataError:
        error_msg = "Загруженный CSV файл пуст"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 400
    except pd.errors.ParserError as e:
        error_msg = f"Ошибка при парсинге CSV файла: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 400
    except Exception as e:
        logger.error(f"Необработанная ошибка в /predict-batch: {str(e)}")
        return jsonify({"error": str(e)}), 400


def create_visualizations(df, predictions, probabilities):
    """Создание интерактивных графиков с помощью Plotly"""
    plots_dir = os.path.join(os.path.dirname(__file__), "static", "plots")
    os.makedirs(plots_dir, exist_ok=True)

    fig1 = px.histogram(
        x=probabilities,
        nbins=30,
        title='Распределение вероятностей оттока',
        labels={'x': 'Вероятность оттока', 'y': 'Количество клиентов'},
        color_discrete_sequence=['#42b983']
    )
    fig1.update_layout(
        template='plotly_white',
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    churn_counts = pd.Series(predictions).value_counts()
    fig2 = px.pie(
        values=churn_counts.values,
        names=['Остаются', 'Уходят'],
        title='Соотношение оттока клиентов',
        color_discrete_sequence=['#42b983', '#ff7f7f']
    )
    fig2.update_traces(
        textinfo='percent+label',
        pull=[0, 0.1],
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )
    fig2.update_layout(
        template='plotly_white',
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    fig3 = px.box(
        df,
        x=predictions,
        y='monthly_charges',
        color=predictions,
        title='Распределение ежемесячных платежей по группам оттока',
        labels={'x': 'Отток (0 - остаются, 1 - уходят)', 'y': 'Ежемесячные платежи'},
        color_discrete_sequence=['#42b983', '#ff7f7f']
    )
    fig3.update_layout(
        template='plotly_white',
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    plots = {
        'probability_distribution': json.dumps(fig1.to_dict(), cls=PlotlyJSONEncoder),
        'churn_ratio': json.dumps(fig2.to_dict(), cls=PlotlyJSONEncoder),
        'monthly_charges_boxplot': json.dumps(fig3.to_dict(), cls=PlotlyJSONEncoder)
    }
    
    return plots

@app.route("/plots/<plot_name>", methods=["GET"])
def get_plot(plot_name):
    try:
        plot_path = os.path.join(os.path.dirname(__file__), "static", "plots", plot_name)
        if not os.path.exists(plot_path):
            return jsonify({"error": "Plot not found"}), 404
        return send_file(plot_path, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 400

def create_pdf_report(predictions_df, plots_data):
    """Создание PDF отчета с результатами анализа"""
    # Создаем временный файл для PDF
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc = SimpleDocTemplate(temp_pdf.name, pagesize=landscape(letter))
    
    # Создаем список элементов для PDF
    elements = []
    styles = getSampleStyleSheet()
    
    # Добавляем заголовок
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    elements.append(Paragraph("Отчет по анализу оттока клиентов", title_style))
    elements.append(Spacer(1, 20))
    
    # Добавляем общую статистику
    total_clients = len(predictions_df)
    churn_clients = predictions_df['churn'].sum()
    churn_rate = (churn_clients / total_clients) * 100
    
    stats_style = ParagraphStyle(
        'Stats',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12,
        alignment=1  # Center alignment
    )
    
    elements.append(Paragraph(f"Общее количество клиентов: {total_clients}", stats_style))
    elements.append(Paragraph(f"Количество клиентов с прогнозируемым оттоком: {int(churn_clients)}", stats_style))
    elements.append(Paragraph(f"Процент оттока: {churn_rate:.2f}%", stats_style))
    elements.append(Spacer(1, 20))

    # Добавляем графики, если они есть
    if plots_data:
        elements.append(Paragraph("Визуализация результатов", styles['Heading2']))
        elements.append(Spacer(1, 12))

        # Создаем временные файлы для каждого графика
        plot_files = []
        
        try:
            # Распределение вероятностей
            if 'probability_distribution' in plots_data:
                fig1 = go.Figure(**json.loads(plots_data['probability_distribution']))
                temp_plot1 = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                pio.write_image(fig1, temp_plot1.name, format='png', width=800, height=400)
                plot_files.append(temp_plot1.name)
                img1 = Image(temp_plot1.name, width=7*inch, height=3.5*inch)
                elements.append(img1)
                elements.append(Spacer(1, 12))

            # Соотношение оттока
            if 'churn_ratio' in plots_data:
                fig2 = go.Figure(**json.loads(plots_data['churn_ratio']))
                temp_plot2 = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                pio.write_image(fig2, temp_plot2.name, format='png', width=800, height=400)
                plot_files.append(temp_plot2.name)
                img2 = Image(temp_plot2.name, width=7*inch, height=3.5*inch)
                elements.append(img2)
                elements.append(Spacer(1, 12))

            # Распределение платежей
            if 'monthly_charges_boxplot' in plots_data:
                fig3 = go.Figure(**json.loads(plots_data['monthly_charges_boxplot']))
                temp_plot3 = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                pio.write_image(fig3, temp_plot3.name, format='png', width=800, height=400)
                plot_files.append(temp_plot3.name)
                img3 = Image(temp_plot3.name, width=7*inch, height=3.5*inch)
                elements.append(img3)
                elements.append(Spacer(1, 20))
        except Exception as e:
            logger.error(f"Ошибка при создании графиков: {str(e)}")
    
    # Добавляем таблицу с детальными результатами
    elements.append(Paragraph("Детальные результаты по клиентам", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    # Создаем таблицу
    table_data = [['ID', 'Отток', 'Вероятность']]
    for _, row in predictions_df.iterrows():
        table_data.append([
            str(row['id']),
            'Да' if row['churn'] else 'Нет',
            f"{row['probability']*100:.2f}%"
        ])
    
    table = Table(table_data, colWidths=[2*inch, 2*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    
    # Создаем PDF
    doc.build(elements)

    # Удаляем временные файлы графиков
    try:
        for plot_file in plot_files:
            os.remove(plot_file)
    except:
        pass

    return temp_pdf.name

@app.route("/download-report", methods=["POST"])
def download_report():
    try:
        data = request.get_json()
        predictions_df = pd.DataFrame(data['predictions'])
        plots = data['plots']
        
        # Создаем PDF отчет
        pdf_path = create_pdf_report(predictions_df, plots)
        
        # Отправляем файл
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='churn_analysis_report.pdf'
        )
    except Exception as e:
        logger.error(f"Ошибка при создании PDF: {str(e)}")
        return jsonify({"error": str(e)}), 400
    finally:
        # Удаляем временный файл
        if 'pdf_path' in locals():
            try:
                os.remove(pdf_path)
            except:
                pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
