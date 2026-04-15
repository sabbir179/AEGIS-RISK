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
        Extracts the numeric risk score (1-5) from the AI's final response.
        """
        # Finds the last digit mentioned after 'Risk Score' (case insensitive)
        matches = re.findall(r"(?:Final\s*)?Risk Score:?\s*(\d)", text, re.IGNORECASE)
        if matches:
            score = int(matches[-1])
            return max(1, min(5, score))
        return 3 # Default to moderate risk if extraction fails

    def save_to_gold_layer(self, query: str, final_report: str):
        """
        MEDALLION GOLD LAYER: Persists verified consensus for graphing.
        """
        risk_score = self._extract_risk_score(final_report)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gold_risk_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
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
        except Exception as e:
            print(f"❌ Gold Layer Persistence Error: {e}")

    def generate_consensus_report(self, query: str, docs: list) -> str:
        """
        AGENTIC CONSENSUS: Lead Analyst (OpenAI) vs. Verification Critic (Anthropic).
        """
        # --- ROBUST DATA VALIDATION ---
        # This prevents the 'NoneType is not iterable' error from your screenshot
        if not docs or docs is None:
            return "⚠️ No context found. Please run Bronze/Silver ingestion first."

        try:
            # Safely handle different ChromaDB return formats
            if isinstance(docs, list) and len(docs) > 0 and isinstance(docs[0], list):
                context_list = docs[0]
            else:
                context_list = docs
            
            # Clean and join the top 5 articles
            context = "\n\n".join([str(d) for d in context_list if d][:5])
            
            if not context.strip():
                return "⚠️ Context found but it was empty. No data to analyze."

        except Exception as e:
            return f"⚠️ Error processing Silver-layer context: {str(e)}"

        # --- PHASE 1: LEAD ANALYST (GPT-4o) ---
        analyst_task = (
            "You are a Lead Geopolitical Analyst. Provide a detailed risk report. "
            "You MUST include a section: 'Risk Score: X' (1-5)."
        )
        
        try:
            analyst_resp = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": analyst_task},
                    {"role": "user", "content": f"Context: {context}\nQuery: {query}"}
                ]
            )
            analyst_report = analyst_resp.choices[0].message.content
        except Exception as e:
            return f"❌ Analyst Agent (OpenAI) failed: {str(e)}"

        # --- PHASE 2: VERIFICATION CRITIC (Claude 4-6 Sonnet) ---
        critic_task = (
            "You are a Verification Critic. Review the Analyst's report for errors. "
            "End your verification with 'Final Risk Score: X' (1-5)."
        )

        try:
            critic_resp = self.anthropic_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1500,
                system=critic_task,
                messages=[{"role": "user", "content": f"Report: {analyst_report}\nContext: {context}"}]
            )
            final_critique = critic_resp.content[0].text
        except Exception as e:
            return f"❌ Critic Agent (Anthropic) failed: {str(e)}"

        # --- SYNTHESIS & STORAGE ---
        final_output = (
            f"## 🏛️ AGENTIC CONSENSUS REPORT\n\n"
            f"### LEAD ANALYST ASSESSMENT\n{analyst_report}\n\n"
            f"--- \n"
            f"### CRITIC VERIFICATION\n{final_critique}"
        )

        self.save_to_gold_layer(query, final_output)
        return final_output