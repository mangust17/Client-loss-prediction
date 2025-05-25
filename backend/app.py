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
from reportlab.lib.units import inch
import tempfile
import plotly.io as pio
import base64
from flask import send_from_directory
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from plotly.graph_objs import Figure

pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
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

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        df = pd.DataFrame([data])
        df = preprocess_data(df)
        prediction = model.predict(df)
        probability = model.predict_proba(df)[:, 1]
        final_probability = float(probability[0]) if prediction[0] == 1 else 1 - float(probability[0])
        return jsonify({
            "churn": int(prediction[0]),
            "probability": final_probability
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

        original_ids = df['id'].copy() if 'id' in df.columns else df.index.astype(str)
        
        df = preprocess_data(df)
        df = df[model_features]
        predictions = model.predict(df)
        probabilities = model.predict_proba(df)[:, 1]
        final_probabilities = [float(p) if pred == 1 else 1 - float(p) for pred, p in zip(predictions, probabilities)]
        results = pd.DataFrame({
            'id': original_ids,
            'churn': predictions,
            'probability': final_probabilities
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

def plot_from_json(json_str):
    fig_dict = json.loads(json_str)
    return Figure(fig_dict)


def create_visualizations(df, predictions, probabilities):
    """Создание интерактивных графиков с помощью Plotly"""
    plots_dir = os.path.join(os.path.dirname(__file__), "static", "plots")
    os.makedirs(plots_dir, exist_ok=True)

    fig1 = px.histogram(
    x=probabilities,
    nbins=30,
    labels={'x': 'Вероятность оттока', 'y': 'Количество клиентов'},
    color_discrete_sequence=['#42b983']
    )
    fig1.update_layout(
        title='Распределение вероятностей оттока',
        template='plotly_white',
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    churn_counts = pd.Series(predictions).value_counts().sort_index()
    fig2 = px.pie(
        values=churn_counts.values,
        names=['Остаются', 'Уходят'],
        color_discrete_sequence=['#ff7f7f', '#42b983']
    )
    fig2.update_traces(
        textinfo='percent+label',
        pull=[0, 0.1],
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )
    fig2.update_layout(
        title='Доля клиентов по оттоку',
        template='plotly_white',
        margin=dict(l=40, r=40, t=40, b=40)
    )

    fig3 = px.box(
        df,
        x=predictions,
        y='monthly_charges',
        color=predictions,
        labels={'x': 'Отток (0 - остаются, 1 - уходят)', 'y': 'Ежемесячные платежи'},
        color_discrete_sequence=['#42b983', '#ff7f7f']
    )
    fig3.update_layout(
        title='Платежи по статусу оттока',
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


def extract_base64_data(img_str):
    if ',' in img_str:
        return img_str.split(',')[1]
    return img_str


def create_pdf_report(predictions_df, plots_data):
    """Создание PDF отчета с визуализациями"""
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc = SimpleDocTemplate(temp_pdf.name, pagesize=landscape(letter))

    elements = []

    if not predictions_df.empty:
        try:
            table_data = [['ID', 'Отток', 'Вероятность']]

            for _, row in predictions_df.iterrows():
                churn_text = 'Да' if row['churn'] == 1 else 'Нет'
                probability = f"{row['probability'] * 100:.2f}%"
                table_data.append([str(row['id']), churn_text, probability])

            table = Table(table_data)

            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F81BD')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Arial'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#DCE6F1')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Arial'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')])
            ])
            
            table.setStyle(style)

            table._argW[0] = 2*inch 
            table._argW[1] = 1.5*inch
            table._argW[2] = 2*inch
            
            elements.append(table)
            elements.append(Spacer(1, 30))
            
        except Exception as e:
            logger.error(f"Ошибка при создании таблицы: {str(e)}")

    if plots_data:
        try:
            for key in ['probability_distribution', 'churn_ratio', 'monthly_charges_boxplot']:
                if key in plots_data:
                    # Извлекаем base64 данные из строки
                    img_data = extract_base64_data(plots_data[key])
                    img_bytes = base64.b64decode(img_data)
                    img = Image(io.BytesIO(img_bytes), width=8*inch, height=4*inch)
                    elements.append(img)
                    elements.append(Spacer(1, 20))
        except Exception as e:
            logger.error(f"Ошибка при добавлении графиков в PDF: {str(e)}")

    doc.build(elements)
    return temp_pdf.name

@app.route("/download-report", methods=["POST"])
def download_report():
    try:
        data = request.get_json()
        predictions_df = pd.DataFrame(data['predictions'])
        plots = data['plots']

        pdf_path = create_pdf_report(predictions_df, plots)

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
        if 'pdf_path' in locals():
            try:
                os.remove(pdf_path)
            except:
                pass

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_vue(path):
    static_folder = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
    if path and os.path.exists(os.path.join(static_folder, path)):
        return send_from_directory(static_folder, path)
    return send_from_directory(static_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)