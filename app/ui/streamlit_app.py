import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000/api"

st.set_page_config(page_title="Aegis-Risk Live News Monitor", layout="wide")
st.title("Aegis-Risk Live News Monitor")

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

            st.subheader("Latest Articles")
            if not data["articles"]:
                st.info("No articles found.")
            else:
                for article in data["articles"]:
                    st.markdown(f"### [{article['title']}]({article['url']})")
                    st.write(f"**Source:** {article.get('source', 'Unknown')}")
                    st.write(f"**Published:** {article.get('published_at', 'Unknown')}")
                    st.write(article.get("summary", "No summary available."))
                    st.divider()
        except Exception as exc:
            st.error(f"Could not load news: {exc}")
