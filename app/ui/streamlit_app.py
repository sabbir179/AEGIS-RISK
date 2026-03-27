import requests
import streamlit as st
import pandas as pd
import plotly.express as px

API_BASE = "http://127.0.0.1:8000/api"

st.set_page_config(page_title="Aegis-Risk Live News Monitor", layout="wide")
st.title("Aegis-Risk Live News Monitor")
st.write("Monitor the latest supply-chain and geopolitical news updates.")

topic = st.text_input("Topic filter", value="")
limit = st.slider("Number of articles", min_value=1, max_value=20, value=10)

col1, col2 = st.columns(2)

with col1:
    if st.button("Refresh News Now"):
        try:
            response = requests.post(f"{API_BASE}/news/refresh", timeout=60)
            response.raise_for_status()
            data = response.json()
            st.success(
                f"Fetched: {data['fetched']} | Inserted: {data['inserted']} | Duplicates: {data['duplicates']}"
            )
        except Exception as exc:
            st.error(f"Refresh failed: {exc}")

with col2:
    if st.button("Load Latest News"):
        try:
            response = requests.get(
                f"{API_BASE}/news/latest",
                params={"topic": topic or None, "limit": limit},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            st.session_state["articles_data"] = data["articles"]
        except Exception as exc:
            st.error(f"Could not load news: {exc}")

articles_data = st.session_state.get("articles_data", [])

st.subheader("System Summary")
try:
    summary_response = requests.get(f"{API_BASE}/news/summary", timeout=30)
    summary_response.raise_for_status()
    summary = summary_response.json()

    c1, c2 = st.columns(2)
    c1.metric("Total Stored Articles", summary["total"])
    c2.metric("Average Risk Score", summary["avg_risk"])

    st.write("### Top Risk Articles")
    if summary["top_risks"]:
        for item in summary["top_risks"]:
            st.markdown(f"- [{item['title']}]({item['url']}) (Risk: {item['risk_score']})")
    else:
        st.info("No top risk articles yet.")
except Exception:
    st.warning("Could not load summary")

if articles_data:
    articles_data = sorted(
        articles_data,
        key=lambda x: x.get("risk_score", 0),
        reverse=True,
    )

    high_count = sum(1 for a in articles_data if a.get("risk_score", 0) >= 5)
    medium_count = sum(1 for a in articles_data if 3 <= a.get("risk_score", 0) < 5)
    low_count = sum(1 for a in articles_data if a.get("risk_score", 0) < 3)

    if high_count > 0:
        st.error(f"⚠️ {high_count} HIGH RISK articles detected")
    elif medium_count > 0:
        st.warning(f"⚠️ {medium_count} medium-risk articles detected")
    else:
        st.success("No high-risk articles currently detected")

    st.subheader("Risk Overview")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Articles", len(articles_data))
    m2.metric("High Risk", high_count)
    m3.metric("Medium Risk", medium_count)
    m4.metric("Low Risk", low_count)

    chart_rows = []
    for article in articles_data[:10]:
        title = article.get("title", "Untitled")
        short_title = title[:60] + "..." if len(title) > 60 else title
        chart_rows.append(
            {
                "title": short_title,
                "risk_score": article.get("risk_score", 0),
            }
        )

    df = pd.DataFrame(chart_rows)

    if not df.empty:
        st.subheader("Top Article Risk Scores")
        fig = px.bar(
            df,
            x="title",
            y="risk_score",
            title="Risk Score by Article",
        )
        st.plotly_chart(fig, width="stretch")

    st.subheader("Latest Articles")
    for article in articles_data:
        st.markdown(f"### [{article['title']}]({article['url']})")
        st.write(f"**Source:** {article.get('source', 'Unknown')}")
        st.write(f"**Published:** {article.get('published_at', 'Unknown')}")
        st.write(article.get("summary", "No summary available."))

        score = article.get("risk_score", 0)

        if score >= 5:
            st.error(f"Risk Score: {score} | HIGH")
        elif score >= 3:
            st.warning(f"Risk Score: {score} | MEDIUM")
        else:
            st.success(f"Risk Score: {score} | LOW")

        st.divider()
else:
    st.info("Click 'Load Latest News' to view articles.")

st.subheader("Ask the News Database")

user_question = st.text_input(
    "Ask a question about supply-chain risk",
    value="What evidence suggests oil and shipping disruption?"
)

if st.button("Ask AI Search"):
    try:
        response = requests.post(
            f"{API_BASE}/news/ask",
            json={"query": user_question},
            timeout=90,
        )
        response.raise_for_status()
        rag_data = response.json()

        st.write("### AI Answer")
        st.success(rag_data.get("answer", "No answer generated."))

        st.write("### Sources Used")
        if not rag_data["results"]:
            st.info("No results found.")
        else:
            for item in rag_data["results"]:
                meta = item.get("metadata", {})
                title = meta.get("title", "Untitled")
                source = meta.get("source", "Unknown")
                risk = meta.get("risk_score", 0)

                st.markdown(f"- **{title}** | Source: {source} | Risk: {risk}")

        st.write("### Search Results")
        if not rag_data["results"]:
            st.info("No results found.")
        else:
            for item in rag_data["results"]:
                meta = item.get("metadata", {})

                st.markdown(f"#### {meta.get('title', 'Untitled')}")
                st.write(f"**Source:** {meta.get('source', 'Unknown')}")
                st.write(f"**Risk Score:** {meta.get('risk_score', 0)}")
                st.write(item.get("document", "")[:500] + "...")
                st.divider()

    except Exception as exc:
        st.error(f"Could not run semantic search: {exc}")