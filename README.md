# Aegis-Risk

Aegis-Risk is a live news monitoring starter project for geopolitical and supply-chain risk analysis.

## Features

- Live news ingestion via NewsAPI
- FastAPI backend
- Streamlit dashboard
- SQLite storage

## Run locally

uvicorn app.api.main:app --reload
streamlit run app/ui/streamlit_app.py
