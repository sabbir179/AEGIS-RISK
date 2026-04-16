import requests
import streamlit as st
import pandas as pd
import plotly.express as px

API_BASE = "http://127.0.0.1:8000/api"

st.set_page_config(page_title="Aegis-Risk: Agentic Consensus Monitor", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #f8f9fa; }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #0e1117;
        color: white;
        border: none;
    }
    </style>
""", unsafe_allow_html=True)


def split_consensus_sections(full_text: str) -> tuple[str, str]:
    """
    Split backend consensus text into analyst and critic sections safely.
    """
    if not full_text:
        return "", ""

    analyst_text = full_text
    critic_text = ""

    analyst_marker = "### LEAD ANALYST ASSESSMENT"
    critic_marker = "### CRITIC VERIFICATION"

    if analyst_marker in full_text and critic_marker in full_text:
        after_analyst = full_text.split(analyst_marker, 1)[1]

        if critic_marker in after_analyst:
            analyst_text = after_analyst.split(critic_marker, 1)[0].replace("---", "").strip()
        else:
            analyst_text = after_analyst.replace("---", "").strip()

        critic_text = full_text.split(critic_marker, 1)[1].strip()

    elif "---" in full_text:
        parts = full_text.split("---", 1)
        analyst_text = parts[0].replace("## 🏛️ AGENTIC CONSENSUS REPORT", "").strip()
        critic_text = parts[1].strip()

    else:
        analyst_text = full_text.replace("## 🏛️ AGENTIC CONSENSUS REPORT", "").strip()

    return analyst_text, critic_text


st.title("🛡️ Aegis-Risk | Agentic Geopolitical Monitor")
st.write("**Architecture:** Medallion (Bronze/Silver/Gold) | **Research Focus:** Multi-Model Adversarial Consensus")

# --- SIDEBAR ---
st.sidebar.header("System Intelligence")
st.sidebar.markdown("🟢 **Analyst:** GPT-4o\n\n🔵 **Critic:** Claude-4.6\n\n⚡ **Refiner:** Groq/Llama-3")
st.sidebar.divider()

topic = st.sidebar.text_input("Global Filter Topic", value="Oil")
limit = st.sidebar.slider("Article Ingestion Limit", 1, 50, 20)

# --- SESSION STATE ---
if "articles_data" not in st.session_state:
    st.session_state["articles_data"] = []

if "gold_trends" not in st.session_state:
    st.session_state["gold_trends"] = []

if "analyst_output" not in st.session_state:
    st.session_state["analyst_output"] = ""

if "critic_output" not in st.session_state:
    st.session_state["critic_output"] = ""

if "raw_consensus_output" not in st.session_state:
    st.session_state["raw_consensus_output"] = ""

# --- MAIN CONTROLS ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Trigger Bronze Ingestion"):
        with st.spinner("Ingesting Raw Telemetry..."):
            try:
                response = requests.post(f"{API_BASE}/news/refresh", timeout=60)
                if response.status_code == 200:
                    st.success("Bronze Layer Updated")
                else:
                    st.error(f"Ingestion failed: {response.status_code}")
            except Exception as e:
                st.error(f"Ingestion failed: {e}")

with col2:
    if st.button("📊 Load Silver Context"):
        try:
            response = requests.get(
                f"{API_BASE}/news/latest",
                params={"topic": topic, "limit": limit},
                timeout=60
            )

            if response.status_code == 200:
                raw_data = response.json()
                articles = raw_data.get("articles", []) if isinstance(raw_data, dict) else raw_data

                st.session_state["articles_data"] = articles

                if articles:
                    st.success(f"✅ Silver Layer: {len(articles)} articles loaded.")
                    st.rerun()
                else:
                    st.warning("⚠️ No articles found for this topic.")
            else:
                st.error(f"API Error: {response.status_code}")
        except Exception as e:
            st.error(f"Connection failed: {e}")

with col3:
    if st.button("📈 Fetch Gold Risk Trends"):
        try:
            response = requests.get(f"{API_BASE}/news/risk-indices", timeout=60)
            if response.status_code == 200:
                st.session_state["gold_trends"] = response.json()
                st.success("Gold Trends Synced")
            else:
                st.error(f"Fetch failed: {response.status_code}")
        except Exception as e:
            st.error(f"Fetch failed: {e}")

# --- GOLD LAYER VISUALIZATION ---
if st.session_state["gold_trends"]:
    st.subheader("🏛️ Gold Layer: Historical Risk Index")
    df_gold = pd.DataFrame(st.session_state["gold_trends"])

    if not df_gold.empty:
        df_gold["time"] = pd.to_datetime(df_gold["time"], errors="coerce")
        df_gold["score"] = pd.to_numeric(df_gold["score"], errors="coerce")
        df_gold = df_gold.dropna(subset=["time", "score"])
        df_gold = df_gold.sort_values("time")

        fig_gold = px.line(
            df_gold,
            x="time",
            y="score",
            color="topic",
            markers=True,
            template="plotly_white"
        )
        fig_gold.update_layout(yaxis_range=[0, 6])
        st.plotly_chart(fig_gold, width="stretch")

# --- AGENTIC WAR ROOM ---
st.divider()
st.subheader("🔎 Verifiable AI: Ask the Agents")
user_question = st.text_input("Enter strategic query:", value=f"Assess current risk to {topic} transit.")

has_context = len(st.session_state["articles_data"]) > 0

if st.button("🚀 Execute Multi-Model Consensus"):
    if not has_context:
        st.error("❌ Context Missing: Click 'Load Silver Context' above first. You must see articles in the 'Underlying Evidence' section below.")
    else:
        with st.spinner("Lead Analyst & Critic are debating..."):
            try:
                res = requests.post(
                    f"{API_BASE}/news/ask",
                    json={"query": user_question},
                    timeout=120
                )

                if res.status_code == 200:
                    rag_data = res.json()
                    full_answer = rag_data.get("answer", "")

                    analyst_text, critic_text = split_consensus_sections(full_answer)

                    st.session_state["raw_consensus_output"] = full_answer
                    st.session_state["analyst_output"] = analyst_text
                    st.session_state["critic_output"] = critic_text
                    st.rerun()
                else:
                    st.error(f"Agent Loop Error: {res.status_code}")
            except Exception as e:
                st.error(f"Loop failed: {e}")

# --- CONSENSUS OUTPUT DISPLAY ---
if st.session_state["analyst_output"] or st.session_state["critic_output"]:
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### 🏛️ Lead Analyst (GPT-4o)")
        st.info(st.session_state["analyst_output"] or "No analyst output returned.")

    with c2:
        st.markdown("### 🛡️ Verification Critic (Claude 4.6)")
        if st.session_state["critic_output"]:
            st.success(st.session_state["critic_output"])
        else:
            st.warning("No critic output returned.")

# --- SILVER LAYER DISPLAY ---
st.divider()
if st.session_state["articles_data"]:
    st.subheader(f"📰 Underlying Evidence ({len(st.session_state['articles_data'])} Articles)")

    for art in st.session_state["articles_data"][:20]:
        source = art.get("source", "News")
        title = art.get("title", "Untitled Article")
        summary = art.get("summary", "No summary available.")
        published_at = art.get("published_at", "N/A")
        url = art.get("url")

        with st.expander(f"{source} | {title}"):
            st.write(summary)
            st.caption(f"Published: {published_at}")
            if url:
                st.link_button("View Source", url)