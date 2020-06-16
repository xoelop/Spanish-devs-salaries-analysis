import pandas as pd
import numpy as np
import re

from pandas.api.types import CategoricalDtype

import requests

from io import BytesIO  # got moved to io in python3.

# url mobile dev
url = 'https://docs.google.com/spreadsheets/d/1nMluZe99qpAapf23xWLpP4v3LHektEZ7fDc4T7IXkeU'

# url web dev (front, back, fullstack)
url = 'https://docs.google.com/spreadsheets/d/14pfsWFpanG-RWmqBZnEYVQFw_rL09kAaxqvBRYjx5lE'

# url copy of the data by july 22
url_cached = 'https://docs.google.com/spreadsheets/d/1_5epZ0ViRtIyIEV5gOeeztA9_Tk-BzDPXJSPH0S-IRI'


def fetch_df(url=url, cached=False, url_cached=url_cached):
    if cached:
        url = url_cached
    url += '/export?gid=0&format=csv'

    r = requests.get(url)
    data = r.content

    base_df = pd.read_csv(BytesIO(data), skiprows=[0, 2])
    base_df.index += 4

    return base_df


column_renamings = {"Años de experiencia": "Years of experience",
                    "Mi posición": "Position",
                    "¿Qué hago en el trabajo?": 'Technologies',
                    'Tipo de empresa': 'Company type',
                    'Tamaño de la empresa': 'Company size',
                    'Mi salario bruto anual (SIN bonus)': 'Gross annual salary w/o bonus',
                    'Localización': 'Original location',
                    'Antigüedad en la empresa': 'Years in the company',
                    'Género': 'Gender',
                    'Horas de trabajo semanales': 'Hours per week',
                    '¿Cómo te pagan?': 'Are you fairly paid?',
                    'Comentarios (opcional)': 'Comments'}

company_renamings = {'Consultora': 'Consulting',
                     'Empresa de Producto': 'Product company',
                     'Estudio/Agencia': 'Studio/Agency',
                     'Start-up': 'Startup'}

gender_renamings = {'Hombre': 'Male',
                    'Mujer': 'Female',
                    'No binario': 'Non binary'}

well_paid_renamings = {'Bien pagado': 'Fairly paid',
                       'Mal pagado': 'Underpaid',
                       'Pagado en exceso': 'Overpaid'}

list_hour = ['/h', 'hora', 'hour']
list_day = ['/d', 'dia', 'día', 'day']

cat_years = CategoricalDtype(
    categories=['<3 years', '3-5 years', '5-10 years', '>10 years'], ordered=True)
cat_position = CategoricalDtype(categories=['Back-End',
                                            'Front-End',
                                            'FullStack'])
cat_type_company = CategoricalDtype(categories=['Consulting',
                                                'Product company',
                                                'Startup',
                                                'Studio/Agency',
                                                'Freelance'],
                                    ordered=True)
cat_size_company = CategoricalDtype(categories=['<25 people',
                                                '25-80 people',
                                                '80-150 people',
                                                '>150 people'],
                                    ordered=True)
cat_gender = CategoricalDtype(categories=['Female', 'Male', 'Non binary'])
cat_gender_2 = CategoricalDtype(categories=['Male', 'Female'])
cat_hours = CategoricalDtype(categories=['10-20 hours',
                                         '20-30 hours',
                                         '30-40 hours',
                                         '40-50 hours',
                                         '50-60 hours'],
                             ordered=True)
cat_well_paid = CategoricalDtype(categories=['Underpaid', 'Fairly paid', 'Overpaid'],
                                 ordered=True)

dtypes_cats = {
    'Years of experience': cat_years,
    'Position': cat_position,
    'Company type': cat_type_company,
    'Company size': cat_size_company,
    'Years in the company': cat_years,
    'Hours per week': cat_hours,
    'Are you fairly paid?': cat_well_paid,
}

no_null_cols = ['Years of experience',
                'Position',
                'Company type',
                'Company size',
                'Years in the company',
                'Are you fairly paid?',
                'Gross annual salary w/o bonus',
                'Original location'
                ]


url_EURUSD = 'http://free.currencyconverterapi.com/api/v5/convert?q=EUR_USD&compact=y'
try:
    EUR_USD = requests.get(url_EURUSD).json()['EUR_USD']['val']
    with open('eurusd.txt', mode='w') as f:
        f.write(str(EUR_USD))
except ConnectionError:
    with open('eurusd.txt') as f:
        EUR_USD = float(f.read())
    print('Connection error')


url_EURGBP = 'http://free.currencyconverterapi.com/api/v5/convert?q=EUR_GBP&compact=y'
try:
    EUR_GBP = requests.get(url_EURGBP).json()['EUR_GBP']['val']
    with open('eurGBP.txt', mode='w') as f:
        f.write(str(EUR_GBP))
except ConnectionError:
    with open('eurGBP.txt') as f:
        EUR_GBP = float(f.read())
    print('Connection error')


def parse_salary(string, EURUSD=EUR_USD, EURGBP=EUR_GBP):
    string = string.replace(',00', '').replace('.', '')
    ints = [int(i) for i in re.findall(r'\d+', string)]
    if len(ints) == 0:
        return np.nan
    value = max(ints)
    if '£' in string:
        value = value / EURGBP
    elif '$' in string:
        value = value / EURUSD

    # Check if the value is the hourly salary
    if (np.array([string.find(el) for el in list_hour]) >= 0).any():
        value = value * 8 * 252
    # Check if the value is the daily salary
    elif (np.array([string.find(el) for el in list_day]) >= 0).any():
        value = value * 252

    return np.round(value, decimals=2)


list_remote = ['remote', 'remoto', 'desde', 'para']


def parse_location(location):
    if (np.array([location.lower().find(el) for el in list_remote]) >= 0).any():
        true_location = 'Remote'
#         print(location)
    elif 'madrid' in  location.lower():
        true_location = 'Madrid'
    elif location.lower() == 'barcelona':
        true_location = 'Barcelona'
    elif location.lower() == 'sevilla':
        true_location = 'Sevilla'
    elif location.lower() in ['bilbao', 'san sebastián']:
        true_location = 'País Vasco'
    elif location.lower() in ['alicante', 'valencia']:
        true_location = 'Comunidad Valenciana'
    elif location.lower() == 'londres':
        true_location = 'London'
    elif location.lower() == 'málaga':
        true_location = 'Málaga'
    else:
        true_location = 'Other'
#         true_location = location
    return true_location


def clean_df(df, EURUSD=EUR_USD, two_genders=True):
    # Translate the column names into English
    df = df.rename(columns=column_renamings)
    # Drop rows where some of the data of the columns to be analyzed is missing
    df = df.dropna(axis='index', subset=no_null_cols)

    # Simple translations of some words in some cells
    for col in ['Years of experience', 'Years in the company']:
        df[col] = df[col].str.replace(
            '5-10', '5-10 ').str.replace('años', 'years')
    df['Company size'] = df['Company size'].str.replace('personas', 'people')
    df['Hours per week'] = df['Hours per week'].str.replace('horas', 'hours')

    # Translate company types
    for key in company_renamings:
        df['Company type'] = df['Company type'].str.replace(
            key, company_renamings[key])

    # Translate genders
    for key in gender_renamings:
        df['Gender'] = df['Gender'].str.replace(key, gender_renamings[key])

    # Translate Are you fairly paid?
    for key in well_paid_renamings:
        df['Are you fairly paid?'] = df['Are you fairly paid?'].str.replace(
            key, well_paid_renamings[key])

    # Convert the dtype of the categories columns to a category
    df = df.astype(dtype=dtypes_cats)

    if two_genders:
        df.Gender = df.Gender.astype(dtype=cat_gender_2)
    else:
        df.Gender = df.Gender.astype(dtype=cat_gender)

    # Fill cells of the col 'Hours per week' to 30-40
    df['Hours per week'].fillna('30-40 hours', inplace=True)

    # Drop any values in the columns that is not a valid element from the categories
    df = df.dropna(axis='index', subset=dtypes_cats.keys())

    df['Gross salary (EUR)'] = df['Gross annual salary w/o bonus'].apply(parse_salary)
    df['Gross salary (USD)'] = (df['Gross salary (EUR)'] * EURUSD).apply(np.round, decimals=2)

    # Drop rows where the salary is 0
    df = df[df['Gross salary (EUR)'] != 0]

    # Drop rows with no location
    df = df[~df['Original location'].isna()]

    # Convert type of col Comments to string
    df['Comments'] = df['Comments'].astype(str)
    df['Comments'] = df['Comments'].replace('nan', '')

    df['Location'] = df['Original location'].apply(parse_location)

    # substitute NaN by '' in the Technologies column
    df['Technologies'].fillna('', inplace=True)

    # If an ashole puts data in new cols the following dropna would wipe out the entire df
    valid_cols = ['Years of experience', 'Position', 'Technologies',
                  'Company type', 'Company size', 'Gross annual salary w/o bonus',
                  'Original location', 'Years in the company', 'Gender', 'Hours per week',
                  'Are you fairly paid?', 'Comments', 'Gross salary (EUR)',
                  'Gross salary (USD)', 'Location']

    df = df[valid_cols]

    # Drop rows where some of the data of the columns to be analyzed is missing
    df = df.dropna(axis='index', subset=df.columns[df.columns!='Comments'])

    # Reset index to make indexing and error reading easier
    df = df.reset_index()

    return df
