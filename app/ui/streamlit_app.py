import re
from html import escape

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000/api"

st.set_page_config(
    page_title="RiskLens AI Monitor",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #07111d;
            --bg-soft: #0c1a2c;
            --panel: rgba(12, 26, 44, 0.86);
            --panel-strong: rgba(17, 34, 56, 0.96);
            --line: rgba(123, 163, 214, 0.22);
            --text: #edf3fb;
            --muted: #99abc4;
            --accent: #70d6ff;
            --accent-2: #f7b267;
            --good: #56d4a7;
            --warn: #ffd166;
            --bad: #ff7b72;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(112, 214, 255, 0.12), transparent 32%),
                radial-gradient(circle at top right, rgba(247, 178, 103, 0.10), transparent 28%),
                linear-gradient(180deg, #07111d 0%, #081424 45%, #0a1727 100%);
            color: var(--text);
            font-family: "Avenir Next", "Helvetica Neue", sans-serif;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1480px;
        }

        h1, h2, h3 {
            color: var(--text);
            font-family: "Avenir Next", "Helvetica Neue", sans-serif;
            letter-spacing: -0.02em;
        }

        p, label, .stMarkdown, .stCaption {
            color: var(--muted);
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(9, 20, 36, 0.98), rgba(11, 24, 42, 0.94));
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {
            color: var(--text);
        }

        .stTextInput input, .stTextArea textarea {
            background: rgba(10, 21, 37, 0.88);
            color: var(--text);
            border: 1px solid var(--line);
            border-radius: 14px;
        }

        .stSlider [data-baseweb="slider"] {
            padding-top: 0.25rem;
        }

        .stButton > button {
            width: 100%;
            min-height: 3rem;
            border-radius: 14px;
            border: 1px solid rgba(112, 214, 255, 0.28);
            background: linear-gradient(135deg, #12263d 0%, #0d1e31 100%);
            color: var(--text);
            font-weight: 700;
            letter-spacing: 0.01em;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
        }

        .stButton > button:hover {
            border-color: rgba(112, 214, 255, 0.55);
            color: white;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(14, 28, 46, 0.95), rgba(11, 22, 38, 0.92));
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            box-shadow: 0 18px 40px rgba(0, 0, 0, 0.16);
        }

        div[data-testid="stMetric"] label {
            color: var(--muted);
        }

        div[data-testid="stMetricValue"] {
            color: var(--text);
        }

        div[data-testid="stMetricDelta"] {
            color: var(--accent-2);
        }

        [data-testid="stTabs"] [role="tablist"] {
            gap: 0.75rem;
        }

        [data-testid="stTabs"] [role="tab"] {
            background: rgba(12, 26, 44, 0.78);
            border: 1px solid var(--line);
            border-radius: 999px;
            color: var(--muted);
            padding: 0.45rem 1rem;
        }

        [data-testid="stTabs"] [aria-selected="true"] {
            background: rgba(112, 214, 255, 0.12);
            border-color: rgba(112, 214, 255, 0.45);
            color: var(--text);
        }

        [data-testid="stExpander"] {
            background: rgba(11, 23, 39, 0.82);
            border: 1px solid var(--line);
            border-radius: 16px;
        }

        .hero {
            padding: 1.7rem 1.8rem;
            border: 1px solid var(--line);
            border-radius: 24px;
            background:
                linear-gradient(135deg, rgba(15, 32, 54, 0.96), rgba(10, 22, 37, 0.92));
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.22);
            margin-bottom: 1rem;
        }

        .hero-kicker {
            color: var(--accent);
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.72rem;
            font-weight: 700;
            margin-bottom: 0.8rem;
        }

        .hero-title {
            color: var(--text);
            font-size: 3rem;
            line-height: 1;
            font-weight: 800;
            margin: 0;
        }

        .hero-subtitle {
            color: var(--muted);
            margin-top: 0.85rem;
            font-size: 1rem;
            max-width: 60rem;
        }

        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            margin-top: 1rem;
        }

        .chip {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.45rem 0.8rem;
            border-radius: 999px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.03);
            color: var(--text);
            font-size: 0.86rem;
        }

        .section-card {
            padding: 1.15rem 1.2rem 1.25rem;
            border-radius: 20px;
            border: 1px solid var(--line);
            background: linear-gradient(180deg, rgba(14, 28, 46, 0.95), rgba(11, 23, 39, 0.92));
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.16);
        }

        .section-title {
            color: var(--text);
            font-size: 1.1rem;
            font-weight: 700;
            margin: 0 0 0.3rem;
        }

        .section-copy {
            color: var(--muted);
            font-size: 0.95rem;
            margin: 0;
        }

        .status-list {
            display: grid;
            gap: 0.65rem;
            margin-top: 0.9rem;
        }

        .status-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0.85rem;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(123, 163, 214, 0.15);
        }

        .status-label {
            color: var(--text);
            font-weight: 600;
        }

        .status-value {
            color: var(--accent);
            font-size: 0.86rem;
            font-weight: 700;
        }

        .agent-panel {
            padding: 1.2rem 1.25rem;
            border-radius: 20px;
            border: 1px solid var(--line);
            min-height: 20rem;
            background: linear-gradient(180deg, rgba(13, 27, 45, 0.96), rgba(10, 22, 36, 0.90));
        }

        .agent-label {
            display: inline-flex;
            align-items: center;
            padding: 0.32rem 0.7rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.9rem;
        }

        .agent-label.analyst {
            color: #81e6d9;
            background: rgba(86, 212, 167, 0.12);
        }

        .agent-label.critic {
            color: #ffd166;
            background: rgba(255, 209, 102, 0.12);
        }

        .agent-panel h3 {
            margin-top: 0;
        }

        .agent-panel p, .agent-panel li {
            color: var(--text);
            line-height: 1.65;
        }

        .agent-panel ul, .agent-panel ol {
            padding-left: 1.1rem;
        }

        .evidence-card {
            padding: 1rem 1rem 0.8rem;
            border-radius: 18px;
            border: 1px solid var(--line);
            background: rgba(12, 24, 40, 0.86);
            margin-bottom: 1rem;
        }

        .evidence-meta {
            color: var(--accent);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.72rem;
            font-weight: 700;
        }

        .evidence-title {
            color: var(--text);
            font-size: 1.02rem;
            font-weight: 700;
            margin: 0.45rem 0 0.6rem;
        }

        .evidence-copy {
            color: var(--muted);
            font-size: 0.93rem;
            line-height: 1.55;
        }

        .empty-state {
            padding: 1.1rem 1.15rem;
            border-radius: 18px;
            border: 1px dashed rgba(123, 163, 214, 0.35);
            background: rgba(10, 22, 36, 0.55);
            color: var(--muted);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_session_state() -> None:
    st.session_state.setdefault("articles_data", [])
    st.session_state.setdefault("gold_trends", [])
    st.session_state.setdefault("analyst_output", "")
    st.session_state.setdefault("critic_output", "")
    st.session_state.setdefault("raw_consensus_output", "")
    st.session_state.setdefault("verification_status", "Awaiting consensus run")
    st.session_state.setdefault("medallion_tier", "Gold")
    st.session_state.setdefault("last_refresh", {})
    st.session_state.setdefault("query_used", "")
    st.session_state.setdefault("last_loaded_topic", "Oil")
    st.session_state.setdefault("user_question", "Assess current risk to Oil transit.")


def split_consensus_sections(full_text: str) -> tuple[str, str]:
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
        analyst_text = parts[0].replace("## AGENTIC CONSENSUS REPORT", "").strip()
        critic_text = parts[1].strip()
    else:
        analyst_text = full_text.replace("## AGENTIC CONSENSUS REPORT", "").strip()

    return analyst_text, critic_text


def extract_risk_score(text: str) -> int | None:
    patterns = [
        r"risk score[^0-9]{0,10}([1-5])(?:\s*/\s*5)?",
        r"score[^0-9]{0,10}([1-5])(?:\s*/\s*5)?",
        r"\b([1-5])\s*/\s*5\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


def risk_label(score: int | None) -> str:
    if score is None:
        return "Pending"
    if score >= 5:
        return "Severe"
    if score >= 4:
        return "High"
    if score >= 3:
        return "Elevated"
    if score >= 2:
        return "Guarded"
    return "Low"


def format_topic(topic: str) -> str:
    cleaned = (topic or "").strip()
    return cleaned.title() if cleaned else "Global Monitoring"


def summarize_text(text: str | None, limit: int = 190) -> str:
    if not text:
        return "No summary available yet."
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def build_trend_dataframe(records: list[dict]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()

    df_gold = pd.DataFrame(records)
    if df_gold.empty:
        return df_gold

    df_gold["time"] = pd.to_datetime(df_gold["time"], errors="coerce")
    df_gold["score"] = pd.to_numeric(df_gold["score"], errors="coerce")
    df_gold["topic"] = df_gold["topic"].astype(str)
    df_gold = df_gold.dropna(subset=["time", "score"])
    return df_gold.sort_values("time")


def get_topic_trend_snapshot(df_gold: pd.DataFrame, topic: str) -> dict:
    if df_gold.empty:
        return {
            "current_score": None,
            "delta": None,
            "active_topic": format_topic(topic),
            "records": 0,
            "matched_exactly": False,
        }

    normalized_topic = (topic or "").strip().lower()
    topic_df = df_gold[df_gold["topic"].str.lower() == normalized_topic]
    matched_exactly = not topic_df.empty

    if topic_df.empty and normalized_topic:
        topic_df = df_gold[df_gold["topic"].str.lower().str.contains(normalized_topic, na=False)]

    if topic_df.empty:
        topic_df = df_gold

    current = topic_df.iloc[-1]
    previous = topic_df.iloc[-2] if len(topic_df) > 1 else None
    delta = None if previous is None else float(current["score"]) - float(previous["score"])

    return {
        "current_score": int(current["score"]),
        "delta": delta,
        "active_topic": format_topic(str(current["topic"])),
        "records": len(topic_df),
        "matched_exactly": matched_exactly,
    }


def render_card(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="section-card">
            <div class="section-title">{escape(title)}</div>
            <p class="section-copy">{escape(copy)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(topic: str, evidence_count: int, consensus_status: str, tracked_topic: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-kicker">Operational Dashboard</div>
            <h1 class="hero-title">RiskLens AI Monitor</h1>
            <p class="hero-subtitle">
                Evidence-backed geopolitical monitoring for energy transit routes, maritime chokepoints,
                and fast-moving strategic risk signals.
            </p>
            <div class="chip-row">
                <div class="chip">Focus topic: {escape(format_topic(topic))}</div>
                <div class="chip">Loaded evidence: {evidence_count}</div>
                <div class="chip">Consensus state: {escape(consensus_status)}</div>
                <div class="chip">Tracked timeline: {escape(tracked_topic)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_system_stack() -> None:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Model Stack</div>
            <p class="section-copy">Agent roles surfaced as a live intelligence workflow.</p>
            <div class="status-list">
                <div class="status-item">
                    <span class="status-label">Lead analyst</span>
                    <span class="status-value">GPT-4o</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Verification critic</span>
                    <span class="status-value">Claude 4.6</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Optional refiner</span>
                    <span class="status-value">Groq / Llama-3</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_agent_panel(title: str, label: str, css_class: str, body: str) -> None:
    st.markdown(
        f"""
            <div class="agent-label {css_class}">{escape(label)}</div>
            <div class="section-card">
                <div class="section-title">{escape(title)}</div>
                <p class="section-copy">Structured output from the {escape(label.lower())} role.</p>
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(body if body else "No output returned yet.")


def render_evidence_card(article: dict) -> None:
    source = article.get("source") or "Unknown source"
    title = article.get("title") or "Untitled article"
    summary = summarize_text(article.get("summary"))
    published_at = article.get("published_at") or "Unknown time"
    risk_score = article.get("risk_score")
    risk_text = f"Risk {risk_score}/5" if risk_score is not None else "Risk pending"

    st.markdown(
        f"""
        <div class="evidence-card">
            <div class="evidence-meta">{escape(source)} | {escape(risk_text)}</div>
            <div class="evidence-title">{escape(title)}</div>
            <div class="evidence-copy">{escape(summary)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Published: {published_at}")
    if article.get("url"):
        st.link_button("Open source article", article["url"], use_container_width=True)


inject_css()
init_session_state()

with st.sidebar:
    st.markdown("## RiskLens AI")
    st.caption("Command rail for ingestion, evidence retrieval, and risk analysis.")

    topic = st.text_input("Focus topic", value=st.session_state["last_loaded_topic"])
    limit = st.slider("Evidence load limit", 1, 50, 20)

    st.markdown("### Pipeline Controls")
    if st.button("Refresh Bronze Pipeline"):
        with st.spinner("Refreshing raw telemetry and promotion pipeline..."):
            try:
                response = requests.post(f"{API_BASE}/news/refresh", timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    st.session_state["last_refresh"] = result
                    st.success("Pipeline refresh completed.")
                else:
                    st.error(f"Refresh failed: {response.status_code}")
            except Exception as exc:
                st.error(f"Refresh failed: {exc}")

    if st.button("Load Silver Evidence"):
        try:
            response = requests.get(
                f"{API_BASE}/news/latest",
                params={"topic": topic, "limit": limit},
                timeout=60,
            )

            if response.status_code == 200:
                raw_data = response.json()
                articles = raw_data.get("articles", []) if isinstance(raw_data, dict) else raw_data
                st.session_state["articles_data"] = articles
                st.session_state["last_loaded_topic"] = topic or "Oil"
                if articles:
                    st.success(f"Loaded {len(articles)} articles into the dashboard.")
                    st.rerun()
                else:
                    st.warning("No articles matched that topic.")
            else:
                st.error(f"Load failed: {response.status_code}")
        except Exception as exc:
            st.error(f"Connection failed: {exc}")

    if st.button("Sync Gold Timeline"):
        try:
            response = requests.get(f"{API_BASE}/news/risk-indices", timeout=60)
            if response.status_code == 200:
                st.session_state["gold_trends"] = response.json()
                st.success("Risk timeline synced.")
                st.rerun()
            else:
                st.error(f"Timeline fetch failed: {response.status_code}")
        except Exception as exc:
            st.error(f"Timeline fetch failed: {exc}")

    st.markdown("### Mission Settings")
    render_system_stack()

    refresh_data = st.session_state["last_refresh"]
    if refresh_data:
        st.markdown("### Last Refresh")
        st.caption(
            "Fetched: "
            f"{refresh_data.get('fetched', 0)} | "
            f"Inserted: {refresh_data.get('inserted', 0)} | "
            f"Duplicates: {refresh_data.get('duplicates', 0)}"
        )

articles_data = st.session_state["articles_data"]
gold_df = build_trend_dataframe(st.session_state["gold_trends"])
trend_snapshot = get_topic_trend_snapshot(gold_df, topic)
consensus_score = extract_risk_score(st.session_state["analyst_output"])
consensus_label = risk_label(consensus_score)
consensus_state = st.session_state["verification_status"]

render_hero(
    topic=topic,
    evidence_count=len(articles_data),
    consensus_status=consensus_state,
    tracked_topic=trend_snapshot["active_topic"],
)

metric_columns = st.columns(4)

with metric_columns[0]:
    st.metric("Focus Topic", format_topic(topic), delta=f"{len(articles_data)} evidence items")

with metric_columns[1]:
    score_value = (
        f"{trend_snapshot['current_score']}/5"
        if trend_snapshot["current_score"] is not None
        else "Not synced"
    )
    delta_value = (
        f"{trend_snapshot['delta']:+.1f} vs prior point"
        if trend_snapshot["delta"] is not None
        else "Need at least two points"
    )
    st.metric("Timeline Risk", score_value, delta=delta_value)

with metric_columns[2]:
    st.metric("Consensus Grade", consensus_label, delta=consensus_state)

with metric_columns[3]:
    source_count = len({art.get("source") for art in articles_data if art.get("source")})
    st.metric("Source Diversity", source_count, delta=f"{trend_snapshot['records']} timeline points")

overview_tab, consensus_tab, evidence_tab = st.tabs(
    ["Overview", "Consensus Workspace", "Evidence Feed"]
)

with overview_tab:
    chart_col, ops_col = st.columns([1.8, 1])

    with chart_col:
        render_card(
            "Risk Timeline",
            "Track how risk scores move across monitored topics and compare the latest signal against recent history.",
        )

        if gold_df.empty:
            st.markdown(
                """
                <div class="empty-state">
                    Sync the Gold timeline from the sidebar to unlock the historical risk chart.
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            fig_gold = px.line(
                gold_df,
                x="time",
                y="score",
                color="topic",
                markers=True,
                color_discrete_sequence=["#70d6ff", "#f7b267", "#56d4a7", "#ff7b72"],
            )
            fig_gold.update_traces(line={"width": 3}, marker={"size": 8})
            fig_gold.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(8, 17, 29, 0.55)",
                font={"color": "#edf3fb", "family": "Avenir Next"},
                legend_title_text="Topic",
                margin={"l": 12, "r": 12, "t": 24, "b": 12},
                hovermode="x unified",
                xaxis={
                    "title": "",
                    "gridcolor": "rgba(123, 163, 214, 0.12)",
                    "zeroline": False,
                },
                yaxis={
                    "title": "Risk score",
                    "range": [0, 5.2],
                    "dtick": 1,
                    "gridcolor": "rgba(123, 163, 214, 0.12)",
                    "zeroline": False,
                },
            )
            st.plotly_chart(fig_gold, use_container_width=True)

    with ops_col:
        render_card(
            "Operations Snapshot",
            "Use the sidebar to refresh ingestion, load a focused evidence set, and sync the risk timeline before running a consensus query.",
        )

        snapshot_items = [
            ("Latest topic match", trend_snapshot["active_topic"]),
            ("Evidence loaded", str(len(articles_data))),
            ("Consensus query", st.session_state["query_used"] or "Not run yet"),
            ("Medallion tier", st.session_state["medallion_tier"]),
        ]

        snapshot_html = "".join(
            f"""
            <div class="status-item">
                <span class="status-label">{escape(label)}</span>
                <span class="status-value">{escape(str(value))}</span>
            </div>
            """
            for label, value in snapshot_items
        )
        st.markdown(
            f"""
            <div class="section-card">
                <div class="section-title">Live Signals</div>
                <div class="status-list">
                    {snapshot_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with consensus_tab:
    question_col, meta_col = st.columns([1.7, 1])

    with question_col:
        render_card(
            "Strategic Query",
            "Frame the operational question you want the analyst and critic to debate. The response is grounded in the currently loaded evidence set.",
        )
        st.text_area(
            "Question for the multi-model workflow",
            key="user_question",
            height=110,
        )

    with meta_col:
        render_card(
            "Run Conditions",
            "Consensus works best after you load topic-specific evidence. The result below is split into analyst reasoning and critic verification.",
        )
        st.caption(f"Evidence available: {len(articles_data)}")
        st.caption(f"Verification state: {consensus_state}")
        st.caption(f"Latest tracked topic: {trend_snapshot['active_topic']}")

    if st.button("Run Multi-Model Consensus"):
        if not articles_data:
            st.error("Load evidence first so the agent workflow has supporting context.")
        else:
            with st.spinner("Lead analyst and critic are debating the latest evidence..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/news/ask",
                        json={"query": st.session_state["user_question"]},
                        timeout=120,
                    )

                    if response.status_code == 200:
                        rag_data = response.json()
                        full_answer = rag_data.get("answer", "")
                        analyst_text, critic_text = split_consensus_sections(full_answer)

                        st.session_state["raw_consensus_output"] = full_answer
                        st.session_state["analyst_output"] = analyst_text
                        st.session_state["critic_output"] = critic_text
                        st.session_state["verification_status"] = rag_data.get(
                            "verification_status", "Consensus returned"
                        )
                        st.session_state["medallion_tier"] = rag_data.get("medallion_tier", "Gold")
                        st.session_state["query_used"] = rag_data.get(
                            "query", st.session_state["user_question"]
                        )
                        st.rerun()
                    else:
                        st.error(f"Consensus request failed: {response.status_code}")
                except Exception as exc:
                    st.error(f"Consensus request failed: {exc}")

    analyst_col, critic_col = st.columns(2)

    with analyst_col:
        render_agent_panel(
            title="Lead Analyst Assessment",
            label="Analyst",
            css_class="analyst",
            body=st.session_state["analyst_output"],
        )

    with critic_col:
        render_agent_panel(
            title="Critic Verification",
            label="Critic",
            css_class="critic",
            body=st.session_state["critic_output"],
        )

with evidence_tab:
    header_col, detail_col = st.columns([1.4, 1])

    with header_col:
        render_card(
            "Underlying Evidence",
            "Review the sources that currently anchor the dashboard. Each card highlights origin, summary, and any available risk score.",
        )

    with detail_col:
        render_card(
            "Coverage Summary",
            f"{len(articles_data)} loaded articles across {len({art.get('source') for art in articles_data if art.get('source')})} sources.",
        )

    if not articles_data:
        st.markdown(
            """
            <div class="empty-state">
                Load Silver evidence from the sidebar to populate the feed and unlock source-backed analysis.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        evidence_columns = st.columns(2)
        for index, article in enumerate(articles_data[:20]):
            with evidence_columns[index % 2]:
                render_evidence_card(article)
