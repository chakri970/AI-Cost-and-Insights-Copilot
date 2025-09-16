import streamlit as st
import requests
import os
import pandas as pd

API = st.sidebar.text_input('API URL', os.getenv('API_URL', 'http://localhost:8000'))

st.title('AI Cost & Insights Copilot')

# KPI / Cost by owner block
month = st.sidebar.text_input('Month (YYYY-MM)', '')
if st.sidebar.button('Load KPI') and month:
    try:
        r = requests.get(f'{API}/cost_by_owner', params={'month': month})
        r.raise_for_status()
        result = r.json()
        data = result.get("data", [])
        if data:
            df = pd.DataFrame(data, columns=["Owner", "Cost"])
            st.subheader(f"Cost by Owner for {month}")
            st.table(df)  # Groq-style table
        else:
            st.warning("No cost data found for this month.")
    except Exception as e:
        st.error(str(e))

# Ask the copilot
st.header('Ask the copilot')
q = st.text_input('Question')
if st.button('Ask') and q:
    try:
        r = requests.post(f'{API}/ask', json={'question': q})
        r.raise_for_status()
        data = r.json()

        # LLM answer
        st.subheader('Answer')
        st.write(data.get('answer'))

        # Sources
        st.subheader('Sources')
        st.write(data.get('sources'))

        # Table (if cost by owner query)
        table = data.get('table')
        if table:
            df = pd.DataFrame(table, columns=["Owner", "Cost"])
            st.subheader('Cost by Owner Table')
            st.table(df)

        # Suggestions
        if data.get('suggestions'):
            st.subheader('Suggestions')
            st.write(data.get('suggestions'))

    except Exception as e:
        st.error(str(e))