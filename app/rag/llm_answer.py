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
        """Helper to find the 1-5 score in the LLM text."""
        match = re.search(r"Risk Score:?\s*(\d)", text)
        if match:
            score = int(match.group(1))
            return max(1, min(5, score)) # Ensure it's between 1 and 5
        return 0

    def save_to_gold_layer(self, query: str, final_report: str):
        """
        MEDALLION GOLD LAYER: Structured Research Data.
        This table allows you to create the graphs for your IEEE paper.
        """
        risk_score = self._extract_risk_score(final_report)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gold_risk_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                topic TEXT,
                risk_score INTEGER,
                full_report TEXT,
                consensus_reached BOOLEAN
            )
        ''')

        cursor.execute(
            "INSERT INTO gold_risk_index (timestamp, topic, risk_score, full_report, consensus_reached) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), query, risk_score, final_report, True)
        )
        
        conn.commit()
        conn.close()

    def generate_consensus_report(self, query: str, docs: list[str]) -> str:
        """
        AGENTIC CONSENSUS: Lead Analyst (OpenAI) vs. Critic (Anthropic).
        """
        if not docs:
            return "No Silver-layer context found to analyze."

        context = "\n\n".join(docs[:5])

        # PHASE 1: LEAD ANALYST (OpenAI)
        analyst_task = (
            "You are a Lead Geopolitical Analyst. Based on the context, provide a detailed report. "
            "You MUST include a section: 'Risk Score: X' where X is 1-5."
        )
        
        analyst_resp = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": analyst_task},
                {"role": "user", "content": f"Context: {context}\nQuery: {query}"}
            ]
        )
        analyst_report = analyst_resp.choices[0].message.content

        # PHASE 2: VERIFICATION CRITIC (Anthropic) - The 'Verifiable AI' step
        critic_task = (
            "You are a Verification Critic. Review the Analyst's report for bias or errors. "
            "If you agree, finalize the report. If not, suggest corrections. "
            "End your response with 'Final Risk Score: X'."
        )

        critic_resp = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1500,
            system=critic_task,
            messages=[{"role": "user", "content": f"Report to verify: {analyst_report}\nOriginal Context: {context}"}]
        )
        final_critique = critic_resp.content[0].text

        # SYNTHESIS
        final_output = (
            f"## 🏛️ AGENTIC CONSENSUS REPORT\n\n"
            f"### LEAD ANALYST ASSESSMENT\n{analyst_report}\n\n"
            f"--- \n"
            f"### CRITIC VERIFICATION\n{final_critique}"
        )

        # SAVE TO GOLD LAYER
        self.save_to_gold_layer(query, final_output)

        return final_output

# Compatibility function for your FastAPI routes
def generate_ai_answer(query: str, docs: list[str]) -> str:
    agent_system = AegisAgenticSystem()
    return agent_system.generate_consensus_report(query, docs)