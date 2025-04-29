import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import FunctionTransformer
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder,StandardScaler,MinMaxScaler,RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder

from catboost import CatBoostClassifier
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import GridSearchCV

from sklearn.metrics import make_scorer
from sklearn.metrics import precision_score, recall_score, roc_auc_score, accuracy_score

import pickle

contract = pd.read_csv('datasets/contract_new.csv', delimiter=',',parse_dates=True)
personal = pd.read_csv('datasets/personal_new.csv', delimiter=',')
internet = pd.read_csv('datasets/internet_new.csv', delimiter=',')
phone = pd.read_csv('datasets/phone_new.csv', delimiter=',')

contract.columns = [
    'id', 'begin_date', 'end_date', 'type', 'paperless_billing', 
    'payment_method', 'monthly_charges', 'total_charges']


contract['total_charges'] = contract['total_charges'].replace(' ', 0).astype(float)

UPLOAD_DATE = '2020-02-01'
upload_date = pd.Timestamp(UPLOAD_DATE)
contract['begin_date'] = contract['begin_date'].astype('datetime64[ns]')
contract.loc[contract['end_date'] == 'No', 'end_date'] = UPLOAD_DATE
contract['end_date'] = contract['end_date'].astype('datetime64[ns]')

contract['contract_length_days'] = (contract['end_date'] - contract['begin_date']).dt.days

contract['left'] = contract['end_date'].apply(lambda x: 1 if pd.notnull(x) and x < upload_date else 0)
contract = contract.drop(columns=['begin_date', 'end_date'])

personal.columns = [
    'id', 'gender', 'senior_citizen', 'partner', 'dependents']

internet.columns = [
    'id', 'internet_service', 'online_security', 'online_backup', 'device_protection','tech_support','streaming_tv','streaming_movies']
    
contract = contract.set_index('id')
personal = personal.set_index('id')
internet = internet.set_index('id')
phone = phone.set_index('customerID')
df = contract.join(personal, how='left').join(internet, how='left').join(phone, how='left').fillna('Нет услуги')

df['internet_services'] = df[['online_security', 'online_backup', 'device_protection', 
                             'tech_support', 'streaming_tv', 'streaming_movies','internet_service']].apply(
                             lambda row: 1 if 'Yes' in row.values else 0, axis=1)
df = df.drop(columns=['online_security', 'online_backup', 'device_protection', 
                      'tech_support', 'streaming_tv', 'streaming_movies','internet_service'])

df = df.drop(columns=['internet_services', 'gender'])
df.duplicated().sum()
df = df.drop_duplicates()

ohe_columns = ['type', 'paperless_billing', 'payment_method','senior_citizen','partner','dependents','MultipleLines']

for i in ohe_columns:
    df[i]=df[i].astype('category').cat.codes

RANDOM_STATE = 80724
TEST_SIZE = 0.25

X = df.drop('left', axis=1)
y = df['left']


num_columns = ['monthly_charges', 'total_charges','contract_length_days']

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE
)

preprocessing = ColumnTransformer(
    [
        ('num', StandardScaler(), num_columns)
    ],
    remainder='passthrough'
)

pipe_final = Pipeline(
    [
        ('preprocessor', preprocessing),
        ('models', CatBoostClassifier(random_state=RANDOM_STATE, silent=True))
    ]
)

param_grid = [
    {
        'models': [CatBoostClassifier(random_state=RANDOM_STATE, silent=True)],
        'models__depth': [1, 5, 9],
        'models__learning_rate': [0.01, 0.1, 0.2],
        'models__iterations': [100, 200, 300],
        'preprocessor__num': [StandardScaler(), MinMaxScaler(), 'passthrough']
    }
]

scoring = {
    'roc_auc': 'roc_auc',
    'accuracy': 'accuracy',
    'precision': 'precision',
    'recall': 'recall'
}


grid_cat_2 = GridSearchCV(
    pipe_final,
    param_grid=param_grid,
    cv=3,
    scoring=scoring,
    refit='roc_auc',
    verbose=2,
    n_jobs=-1
)

grid_cat_2.fit(X_train, y_train)

print('Лучшая модель и ее параметры:\n\n', grid_cat_2.best_estimator_)
best_index = grid_cat_2.best_index_
cv_results = grid_cat_2.cv_results_
best_model = grid_cat_2.best_estimator_

print('ROC AUC:', cv_results['mean_test_roc_auc'][best_index])
print('Accuracy:', cv_results['mean_test_accuracy'][best_index])
print('Precision:', cv_results['mean_test_precision'][best_index])
print('Recall:', cv_results['mean_test_recall'][best_index])

with open("model.pkl", "wb") as file:
    pickle.dump(best_model, file)