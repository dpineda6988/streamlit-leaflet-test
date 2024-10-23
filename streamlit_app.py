# streamlit_app.py
#######################
# Import libraries
import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from google.cloud import bigquery
import folium
import folium.features
import requests
from streamlit_folium import st_folium, folium_static

#######################
# Page configuration
st.set_page_config(
    page_title="Population Growth Metrics Dashboard",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

#######################
# Load data from the BigQuery database in a DataFrame

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data()
def run_query(query):
    query_job = client.query(query)
    rows_raw = query_job.result()
    # Convert to list of dicts. Required for st.cache_data to hash the return value.
    rows = [dict(row) for row in rows_raw]

    # Load the query data into a DataFrame
    df = pd.DataFrame(rows)

    # Pivot the data into the desired format and reset the index
    df_pivoted = df.pivot_table(index=['year','country_name','country_code'],columns='indicator_name',values='value')
    final_df = df_pivoted.reset_index()

    # Replace NaN values with '0'
    final_df.fillna(0, inplace=True)
    return final_df

query = """
    SELECT year, country_name, country_code, indicator_name, value
    FROM `bigquery-public-data.world_bank_wdi.indicators_data`
    WHERE indicator_name IN (
            'GDP per capita (current US$)',
            'Fertility rate, total (births per woman)',
            'Urban population',
            'Rural population')
    AND NOT country_name in (
        'Latin America & Caribbean',
        'Latin America & Caribbean (excluding high income)',
        'Latin America & the Caribbean (IDA & IBRD countries)',
        'Least developed countries: UN classification',
        'Low & middle income',
        'Low income',
        'Lower middle income',
        'Middle East & North Africa',
        'Middle East & North Africa (excluding high income)',
        'Africa Eastern and Southern',
        'Africa Western and Central',
        'Arab World',
        'Caribbean small states',
        'Central Europe and the Baltics',
        'Early-demographic dividend',
        'East Asia & Pacific',
        'East Asia & Pacific (excluding high income)',
        'East Asia & Pacific (IDA & IBRD countries)',
        'Upper middle income',
        'World',
        'Middle East & North Africa (IDA & IBRD countries)',
        'Middle income',
        'North America',
        'OECD members',
        'Other small states',
        'Pacific island small states',
        'Post-demographic dividend',
        'Pre-demographic dividend',
        'Euro area',
        'Europe & Central Asia',
        'Europe & Central Asia (excluding high income)',
        'Europe & Central Asia (IDA & IBRD countries)',
        'European Union',
        'Fragile and conflict affected situations',
        'Heavily indebted poor countries (HIPC)',
        'High income',
        'Small states',
        'South Asia (IDA & IBRD)',
        'Sub-Saharan Africa',
        'Sub-Saharan Africa (excluding high income)',
        'Sub-Saharan Africa (IDA & IBRD countries)',
        'IBRD only',
        'IDA & IBRD total',
        'IDA blend',
        'IDA only',
        'IDA total',
        'Late-demographic dividend')
    ORDER BY year DESC, country_name, indicator_name
"""
final_df = run_query(query)

#######################
# Sidebar
with st.sidebar:
    st.title('Population Metrics Dashboard')
    # Create a list of the different indicators for the drop down menu
    series_names = ['Fertility rate, total (births per woman)', 'GDP per capita (current US$)', ]
    # Dropdown for indicator layers
    selected_metric = st.selectbox("Select Metric", series_names)
    # Slider to determine the year to be displayed
    slider_year = st.slider('Select a year', 1960, 2019, 2019)

    current_df = final_df[final_df['year']==slider_year]

#######################