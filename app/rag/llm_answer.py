import re
import sqlite3
from datetime import datetime
from openai import OpenAI
from anthropic import Anthropic
from app.core.config import settings


class AegisAgenticSystem:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
        self.db_path = settings.database_url.replace("sqlite:///", "")

    def _extract_risk_score(self, text: str) -> int:
        """
        Extract numeric risk score (1-5) from model output.
        Prefers Final Risk Score first, then Risk Score.
        """
        final_matches = re.findall(r"Final Risk Score:?\s*([1-5])", text, re.IGNORECASE)
        if final_matches:
            return int(final_matches[-1])

        matches = re.findall(r"Risk Score:?\s*([1-5])", text, re.IGNORECASE)
        if matches:
            return int(matches[-1])

        return 3

    def _normalize_topic_label(self, query: str) -> str:
        """
        Convert raw user query into a clean topic label for the Gold chart.
        """
        clean_query = (query or "").strip().lower()

        if "suez" in clean_query:
            return "suez canal"
        if "hormuz" in clean_query:
            return "strait of hormuz"
        if "oil" in clean_query:
            return "oil transit"
        if "iran" in clean_query:
            return "iran transit"
        if "shipping" in clean_query:
            return "shipping transit"

        return clean_query or "general risk"

    def save_to_gold_layer(self, query: str, final_report: str):
        """
        MEDALLION GOLD LAYER: Persist verified consensus output.
        """
        risk_score = self._extract_risk_score(final_report)
        normalized_topic = self._normalize_topic_label(query)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gold_risk_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    topic TEXT,
                    risk_score INTEGER,
                    full_report TEXT,
                    consensus_reached BOOLEAN
                )
            """)

            cursor.execute(
                """
                INSERT INTO gold_risk_index
                (timestamp, topic, risk_score, full_report, consensus_reached)
                VALUES (?, ?, ?, ?, ?)
                """,
                (datetime.now().isoformat(), normalized_topic, risk_score, final_report, True)
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"❌ Gold Layer Persistence Error: {e}")

    def _normalize_docs(self, docs: list) -> list:
        """
        Handle nested vector DB return formats safely.
        """
        if not docs:
            return []

        if isinstance(docs, list) and docs and isinstance(docs[0], list):
            return docs[0]

        return docs

    def _prepare_context(self, docs: list) -> str:
        """
        Convert retrieved docs into clean, readable source blocks for the LLMs.
        Also removes repeated titles to improve source diversity.
        """
        context_list = self._normalize_docs(docs)
        if not context_list:
            return ""

        unique_docs = []
        seen_titles = set()

        for doc in context_list:
            if isinstance(doc, dict):
                title = str(doc.get("title", "")).strip().lower()
                dedupe_key = title or str(doc)
            else:
                dedupe_key = str(doc).strip().lower()

            if dedupe_key in seen_titles:
                continue

            seen_titles.add(dedupe_key)
            unique_docs.append(doc)

        formatted_blocks = []

        for i, doc in enumerate(unique_docs[:8]):
            if isinstance(doc, dict):
                title = str(doc.get("title", "")).strip()
                summary = str(doc.get("summary", "") or doc.get("description", "")).strip()
                content = str(doc.get("content", "")).strip()
                source = str(doc.get("source", "Unknown")).strip()
                url = str(doc.get("url", "")).strip()
                published_at = str(doc.get("published_at", "") or doc.get("publishedAt", "")).strip()

                block = (
                    f"[Source {i+1}]\n"
                    f"Source Name: {source or 'Unknown'}\n"
                    f"Title: {title or 'Untitled'}\n"
                    f"Summary: {summary or 'N/A'}\n"
                    f"Content: {content or 'N/A'}\n"
                    f"Published At: {published_at or 'N/A'}\n"
                    f"URL: {url or 'N/A'}"
                )
            else:
                block = f"[Source {i+1}]\n{str(doc)}"

            formatted_blocks.append(block)

        return "\n\n".join(formatted_blocks)

    def _extract_anthropic_text(self, response) -> str:
        """
        Safely extract text from Anthropic response blocks.
        """
        if not hasattr(response, "content") or not response.content:
            return ""

        parts = []
        for block in response.content:
            text_value = getattr(block, "text", None)
            if text_value:
                parts.append(text_value.strip())

        return "\n".join(part for part in parts if part).strip()

    def generate_consensus_report(self, query: str, docs: list) -> str:
        """
        AGENTIC CONSENSUS: Lead Analyst vs Verification Critic.
        """
        formatted_context = self._prepare_context(docs)

        if not formatted_context.strip():
            return "⚠️ No context found. Run ingestion first."

        analyst_task = (
            "You are a Lead Geopolitical Risk Analyst.\n\n"
            "You must write a report using ONLY the provided context.\n"
            "Do NOT use outside knowledge.\n"
            "Do NOT invent facts.\n"
            "Every major claim must include bracket citations like [Source 1].\n"
            "Use the most relevant matching source for each claim.\n"
            "Do not reuse the same source for every claim unless the evidence truly comes from that same source.\n"
            "If evidence is weak, say the evidence is limited.\n"
            "Only write 'No evidence found' when absolutely nothing in the supplied context supports the claim.\n\n"
            "You MUST follow this exact structure:\n\n"
            "Geopolitical Risk Assessment: <short title>\n\n"
            "Introduction\n"
            "<2-4 sentences>\n\n"
            "Current Risk Factors\n"
            "1. <factor> [Source X]\n"
            "2. <factor> [Source Y]\n"
            "3. <factor> [Source Z]\n\n"
            "Mitigating Factors\n"
            "- <point> [Source X]\n"
            "- <point> [Source Y]\n\n"
            "Conclusion\n"
            "<short conclusion>\n\n"
            "Recommendations\n"
            "- <action>\n"
            "- <action>\n"
            "- <action>\n\n"
            "Risk Score: <number between 1 and 5 only>\n\n"
            "IMPORTANT:\n"
            "- You MUST output a numeric risk score only\n"
            "- Do NOT write 'Incomplete' instead of a number\n"
            "- Keep the report evidence-based, clear, and concise\n"
        )

        try:
            analyst_resp = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": analyst_task},
                    {"role": "user", "content": f"User Query:\n{query}\n\nContext Sources:\n{formatted_context}"}
                ]
            )
            analyst_report = analyst_resp.choices[0].message.content or ""
        except Exception as e:
            return f"❌ Analyst Agent failed: {str(e)}"

        critic_task = (
            "You are a strict Verification Critic.\n\n"
            "Your role is to verify the analyst's report using ONLY the provided context.\n"
            "Do NOT use outside knowledge.\n"
            "Do NOT hallucinate.\n"
            "If a claim is not clearly supported by the context, mark it unsupported.\n\n"
            "You MUST follow this exact structure and fill every section:\n\n"
            "Verification Report\n"
            "-------------------\n\n"
            "Supported Claims:\n"
            "- <claim> -> [Source X]\n"
            "- <claim> -> [Source Y]\n"
            "If none, write: None\n\n"
            "Unsupported Claims:\n"
            "- <claim> -> <reason>\n"
            "If none, write: None\n\n"
            "Missing Evidence:\n"
            "- <what is missing>\n"
            "If none, write: None\n\n"
            "Final Verdict:\n"
            "- Reliable\n"
            "or\n"
            "- Partially Reliable\n"
            "or\n"
            "- Unreliable\n\n"
            "Final Risk Score: <number between 1 and 5 only>\n\n"
            "IMPORTANT:\n"
            "- Do not leave any section blank\n"
            "- Be specific\n"
            "- Keep the output concise but complete\n"
            "- You MUST output a numeric final risk score\n"
        )

        try:
            critic_resp = self.anthropic_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1500,
                system=critic_task,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"User Query:\n{query}\n\n"
                            f"Analyst Report:\n{analyst_report}\n\n"
                            f"Context Sources:\n{formatted_context}"
                        )
                    }
                ]
            )

            final_critique = self._extract_anthropic_text(critic_resp)

            if not final_critique:
                final_critique = (
                    "Verification Report\n"
                    "-------------------\n\n"
                    "Supported Claims:\n"
                    "- None\n\n"
                    "Unsupported Claims:\n"
                    "- None\n\n"
                    "Missing Evidence:\n"
                    "- None\n\n"
                    "Final Verdict:\n"
                    "- Partially Reliable\n\n"
                    "Final Risk Score: 3"
                )

        except Exception as e:
            return f"❌ Critic Agent failed: {str(e)}"

        final_output = (
            f"## 🏛️ AGENTIC CONSENSUS REPORT\n\n"
            f"### LEAD ANALYST ASSESSMENT\n{analyst_report.strip()}\n\n"
            f"---\n"
            f"### CRITIC VERIFICATION\n{final_critique.strip()}"
        )

        self.save_to_gold_layer(query, final_output)
        return final_output