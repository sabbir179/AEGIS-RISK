import logging
import json
import re
import sqlite3
from datetime import datetime
from openai import OpenAI
from anthropic import Anthropic
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMGenerationError(Exception):
    """Raised when an LLM response cannot be generated or parsed safely."""


class AegisAgenticSystem:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
        self.db_path = settings.database_url.replace("sqlite:///", "")
        self.last_audit = {}

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

        conn = None
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
            logger.info("Saved consensus report to Gold Layer for topic: %s", normalized_topic)

        except Exception as e:
            logger.exception("Gold Layer Persistence Error: %s", e)
        finally:
            if conn:
                conn.close()

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

    def _extract_openai_text(self, response) -> str:
        """
        Safely extract text from OpenAI chat completion responses.
        """
        choices = getattr(response, "choices", None)
        if not choices:
            return ""

        first_choice = choices[0]
        message = getattr(first_choice, "message", None)
        content = getattr(message, "content", None)
        return str(content).strip() if content else ""

    def _default_critic_feedback(self, reason: str) -> dict:
        return {
            "unsupported_claims": [],
            "missing_evidence": ["Critic review could not be completed."],
            "uncertainty_areas": ["Use the initial analyst assessment with caution."],
            "risk_score_concerns": [reason],
            "suggested_improvements": ["Ask a human reviewer to validate the final risk score and citations."],
        }

    def _parse_critic_feedback(self, value: str) -> dict:
        """
        Parse critic feedback when it is valid JSON; otherwise keep the raw text
        in a structured fallback for auditability.
        """
        if not value:
            raise LLMGenerationError("Critic returned empty feedback")

        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            logger.warning("Critic feedback was not valid JSON; preserving raw feedback for audit")
            return {
                "unsupported_claims": [],
                "missing_evidence": [],
                "uncertainty_areas": ["Critic feedback was returned as unstructured text."],
                "risk_score_concerns": [],
                "suggested_improvements": [value.strip()],
            }

        if not isinstance(parsed, dict):
            raise LLMGenerationError("Critic feedback JSON was not an object")

        expected_keys = [
            "unsupported_claims",
            "missing_evidence",
            "uncertainty_areas",
            "risk_score_concerns",
            "suggested_improvements",
        ]

        normalized = {}
        for key in expected_keys:
            item = parsed.get(key, [])
            if isinstance(item, list):
                normalized[key] = [str(value).strip() for value in item if str(value).strip()]
            elif item:
                normalized[key] = [str(item).strip()]
            else:
                normalized[key] = []

        return normalized

    def _format_fallback_report(self, analyst_report: str, warning: str) -> str:
        risk_score = self._extract_risk_score(analyst_report)
        return (
            "## Final Risk Assessment\n\n"
            f"Final Risk Score: {risk_score}\n\n"
            "### Concise Summary\n"
            f"{analyst_report.strip()}\n\n"
            "### Key Evidence\n"
            "- See cited sources in the analyst assessment above.\n\n"
            "### Uncertainty Notes\n"
            f"- {warning}\n\n"
            "### Recommended Human Review Points\n"
            "- Validate source coverage and risk score before operational use."
        )

    def generate_consensus_report(self, query: str, docs: list) -> str:
        """
        AGENTIC CONSENSUS: analyst draft -> critic feedback -> analyst revision.
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
            analyst_report = self._extract_openai_text(analyst_resp)
            if not analyst_report:
                raise LLMGenerationError("OpenAI returned an empty or malformed analyst response")
        except Exception as e:
            logger.exception("Analyst Agent failed: %s", e)
            return (
                "The analyst model could not generate a report right now. "
                "Please try again after refreshing the evidence."
            )

        critic_task = (
            "You are a strict Verification Critic.\n\n"
            "Your role is to verify the analyst's report using ONLY the provided context.\n"
            "Do NOT use outside knowledge.\n"
            "Do NOT hallucinate.\n"
            "If a claim is not clearly supported by the context, mark it unsupported.\n\n"
            "Return JSON only with exactly these keys:\n"
            "{\n"
            '  "unsupported_claims": ["claim and reason"],\n'
            '  "missing_evidence": ["evidence gap"],\n'
            '  "uncertainty_areas": ["uncertain area"],\n'
            '  "risk_score_concerns": ["risk score concern"],\n'
            '  "suggested_improvements": ["specific revision instruction"]\n'
            "}\n\n"
            "IMPORTANT:\n"
            "- Keep each list concise\n"
            "- Use empty arrays if a category has no findings\n"
            "- Do not include markdown outside the JSON\n"
        )

        critic_feedback = None
        critic_warning = None
        try:
            critic_resp = self.anthropic_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
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

            critic_text = self._extract_anthropic_text(critic_resp)
            critic_feedback = self._parse_critic_feedback(critic_text)

        except Exception as e:
            logger.exception("Critic Agent failed: %s", e)
            critic_warning = "Critic review failed; final report falls back to the initial analyst assessment."
            critic_feedback = self._default_critic_feedback(critic_warning)

        revision_task = (
            "You are the Lead Geopolitical Risk Analyst revising your assessment once.\n\n"
            "Use ONLY the provided context and the critic feedback.\n"
            "Remove or qualify unsupported claims.\n"
            "Preserve source citations such as [Source 1].\n"
            "Do not show the raw critic feedback.\n\n"
            "Return a short decision-focused report with exactly these sections:\n\n"
            "## Final Risk Assessment\n\n"
            "Final Risk Score: <number between 1 and 5>\n\n"
            "### Concise Summary\n"
            "<3-5 sentences>\n\n"
            "### Key Evidence\n"
            "- <evidence point with [Source X]>\n"
            "- <evidence point with [Source Y]>\n\n"
            "### Uncertainty Notes\n"
            "- <uncertainty or evidence limitation>\n\n"
            "### Recommended Human Review Points\n"
            "- <specific issue a human should validate>\n\n"
            "Keep the output concise and operational."
        )

        try:
            revision_resp = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": revision_task},
                    {
                        "role": "user",
                        "content": (
                            f"User Query:\n{query}\n\n"
                            f"Context Sources:\n{formatted_context}\n\n"
                            f"Initial Analyst Assessment:\n{analyst_report}\n\n"
                            f"Critic Feedback JSON:\n{json.dumps(critic_feedback, indent=2)}"
                        )
                    },
                ],
            )
            final_output = self._extract_openai_text(revision_resp)
            if not final_output:
                raise LLMGenerationError("OpenAI returned an empty or malformed revision response")
        except Exception as e:
            logger.exception("Analyst revision failed: %s", e)
            revision_warning = "Revision step failed; final report falls back to the initial analyst assessment."
            final_output = self._format_fallback_report(analyst_report, revision_warning)

        self.last_audit = {
            "initial_analyst_assessment": analyst_report,
            "critic_feedback": critic_feedback,
            "critic_warning": critic_warning,
            "final_risk_score": self._extract_risk_score(final_output),
        }
        logger.debug("Actor-critic-revision audit: %s", self.last_audit)

        self.save_to_gold_layer(query, final_output)
        return final_output
