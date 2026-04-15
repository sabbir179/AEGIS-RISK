import requests
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

API_BASE = "http://127.0.0.1:8000/api"

st.set_page_config(page_title="Aegis-Risk: Agentic Consensus Monitor", layout="wide")

# Custom CSS for a professional Research Dashboard
st.markdown("""
    <style>
    .stApp { background: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #0e1117; color: white; }
    .agent-box { padding: 20px; border-radius: 10px; border: 1px solid #ddd; background: white; height: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Aegis-Risk | Agentic Geopolitical Monitor")
st.write("**Architecture:** Medallion (Bronze/Silver/Gold) | **Research Focus:** Multi-Model Adversarial Consensus")

# --- SIDEBAR: SYSTEM STATUS ---
st.sidebar.header("System Intelligence")
st.sidebar.markdown("🟢 **Analyst:** GPT-4o\n\n🔵 **Critic:** Claude-4.6\n\n⚡ **Refiner:** Groq/Llama-3")
st.sidebar.divider()

topic = st.sidebar.text_input("Global Filter Topic", value="Suez Canal")
limit = st.sidebar.slider("Article Ingestion Limit", 1, 50, 20)

# Initialize Session States
if "articles_data" not in st.session_state: st.session_state["articles_data"] = []
if "gold_trends" not in st.session_state: st.session_state["gold_trends"] = []

# --- MAIN CONTROLS ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Trigger Bronze Ingestion"):
        with st.spinner("Ingesting Raw Telemetry..."):
            try:
                requests.post(f"{API_BASE}/news/refresh", timeout=60)
                st.success("Bronze Layer Updated")
            except Exception as e: st.error(f"Ingestion failed: {e}")

with col2:
    if st.button("📊 Load Silver Context"):
        try:
            response = requests.get(f"{API_BASE}/news/latest", params={"topic": topic, "limit": limit})
            if response.status_code == 200:
                st.session_state["articles_data"] = response.json().get("articles", [])
                st.toast("Silver context loaded from ChromaDB")
        except Exception as e: st.error(f"Load failed: {e}")

with col3:
    if st.button("📈 Fetch Gold Risk Trends"):
        try:
            response = requests.get(f"{API_BASE}/news/risk-indices")
            if response.status_code == 200:
                st.session_state["gold_trends"] = response.json()
                if not st.session_state["gold_trends"]:
                    st.warning("Gold Layer is empty. Run a Consensus Query first.")
                else:
                    st.success(f"Fetched {len(st.session_state['gold_trends'])} data points.")
        except Exception as e: st.error(f"Fetch failed: {e}")

# --- GOLD LAYER VISUALIZATION ---
if st.session_state["gold_trends"]:
    st.subheader("🏛️ Gold Layer: Historical Risk Index")
    df_gold = pd.DataFrame(st.session_state["gold_trends"])
    
    if not df_gold.empty:
        # DATA CLEANING FOR PLOTLY
        df_gold['time'] = pd.to_datetime(df_gold['time'])
        df_gold['score'] = pd.to_numeric(df_gold['score'])
        df_gold = df_gold.sort_values('time')

        fig_gold = px.line(
            df_gold, 
            x='time', 
            y='score', 
            color='topic',
            title="Geopolitical Risk Volatility (Verified Consensus)",
            markers=True, 
            line_shape="linear",
            template="plotly_white"
        )
        # Ensure Y-axis stays on the 1-5 or 1-10 scale
        fig_gold.update_layout(yaxis_range=[0, df_gold['score'].max() + 1])
        st.plotly_chart(fig_gold, use_container_width=True)

# --- THE AGENTIC WAR ROOM ---
st.divider()
st.subheader("🔎 Verifiable AI: Ask the Agents")
user_question = st.text_input("Enter strategic query (e.g., 'Suez Canal Risk'):", value="Assess the current risk to Suez Canal transit.")

if st.button("🚀 Execute Multi-Model Consensus"):
    with st.spinner("Lead Analyst & Critic are debating..."):
        try:
            res = requests.post(f"{API_BASE}/news/ask", json={"query": user_question}, timeout=120)
            if res.status_code == 200:
                rag_data = res.json()
                full_answer = rag_data.get("answer", "")

                # Split display for "Adversarial Effect"
                if "---" in full_answer:
                    parts = full_answer.split("---")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("### 🏛️ Lead Analyst (GPT-4o)")
                        st.info(parts[0].replace("## 🏛️ AGENTIC CONSENSUS REPORT", ""))
                    with c2:
                        st.markdown("### 🛡️ Verification Critic (Claude 4.6)")
                        st.success(parts[1])
                    st.caption("✅ Data persists to Gold Tier upon consensus completion.")
                else:
                    st.markdown(full_answer)
            else:
                st.error(f"Backend Error: {res.status_code}")
        except Exception as e:
            st.error(f"Agentic loop failed: {e}")

# --- SILVER LAYER CONTEXT ---
st.divider()
if st.session_state["articles_data"]:
    st.subheader("📰 Recent Context (Silver Layer)")
    for art in st.session_state["articles_data"][:5]:
        with st.expander(f"{art['title']}"):
            st.write(f"**Source:** {art.get('source')} | **Date:** {art.get('published_at')}")
            st.write(art.get('summary'))
            if art.get('url'):
                st.link_button("View Original Source", art['url'])