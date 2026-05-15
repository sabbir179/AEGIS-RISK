from types import SimpleNamespace

from app.rag.llm_answer import AegisAgenticSystem


def make_agent():
    return AegisAgenticSystem.__new__(AegisAgenticSystem)


def test_extract_risk_score_prefers_final_risk_score():
    agent = make_agent()
    text = "Risk Score: 2\nFinal Risk Score: 4"

    assert agent._extract_risk_score(text) == 4


def test_extract_risk_score_defaults_to_three_for_malformed_text():
    agent = make_agent()

    assert agent._extract_risk_score("Risk Score: incomplete") == 3


def test_prepare_context_dedupes_titles_and_formats_sources():
    agent = make_agent()
    docs = [
        {
            "title": "Oil transit risk",
            "summary": "Summary A",
            "content": "Content A",
            "source": "Source A",
            "url": "https://example.com/a",
            "published_at": "2026-05-15",
        },
        {
            "title": "Oil transit risk",
            "summary": "Summary B",
            "content": "Content B",
            "source": "Source B",
            "url": "https://example.com/b",
            "published_at": "2026-05-15",
        },
    ]

    context = agent._prepare_context(docs)

    assert "[Source 1]" in context
    assert "Source A" in context
    assert "Source B" not in context


def test_extract_openai_and_anthropic_text_handles_structured_responses():
    agent = make_agent()
    openai_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Analyst report"))]
    )
    anthropic_response = SimpleNamespace(
        content=[
            SimpleNamespace(text="Critic report"),
            SimpleNamespace(text="Final Risk Score: 3"),
        ]
    )

    assert agent._extract_openai_text(openai_response) == "Analyst report"
    assert agent._extract_anthropic_text(anthropic_response) == "Critic report\nFinal Risk Score: 3"


def test_generate_consensus_report_returns_safe_message_without_context():
    agent = make_agent()

    assert "No context found" in agent.generate_consensus_report("oil risk", [])


class FakeOpenAIClient:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        output = self.outputs.pop(0)
        if isinstance(output, Exception):
            raise output
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=output))]
        )


class FakeAnthropicClient:
    def __init__(self, output):
        self.output = output
        self.messages = SimpleNamespace(create=self.create)

    def create(self, **kwargs):
        if isinstance(self.output, Exception):
            raise self.output
        return SimpleNamespace(content=[SimpleNamespace(text=self.output)])


def test_parse_critic_feedback_accepts_json_shape():
    agent = make_agent()
    feedback = agent._parse_critic_feedback(
        """
        {
          "unsupported_claims": ["Unsupported tanker claim"],
          "missing_evidence": ["No volume data"],
          "uncertainty_areas": ["Limited source coverage"],
          "risk_score_concerns": ["Score may be high"],
          "suggested_improvements": ["Qualify the conclusion"]
        }
        """
    )

    assert feedback["unsupported_claims"] == ["Unsupported tanker claim"]
    assert feedback["suggested_improvements"] == ["Qualify the conclusion"]


def test_generate_consensus_report_runs_revision_flow():
    agent = make_agent()
    agent.openai_client = FakeOpenAIClient([
        "Initial report with Risk Score: 4 [Source 1]",
        (
            "## Final Risk Assessment\n\n"
            "Final Risk Score: 3\n\n"
            "### Concise Summary\n"
            "Transit risk is elevated but evidence remains limited. [Source 1]\n\n"
            "### Key Evidence\n"
            "- Tanker disruption is cited by the retrieved article. [Source 1]\n\n"
            "### Uncertainty Notes\n"
            "- Market impact is not quantified.\n\n"
            "### Recommended Human Review Points\n"
            "- Validate the latest vessel movement data."
        ),
    ])
    agent.anthropic_client = FakeAnthropicClient(
        """
        {
          "unsupported_claims": [],
          "missing_evidence": ["No market pricing evidence"],
          "uncertainty_areas": ["Limited source coverage"],
          "risk_score_concerns": ["Risk score should be moderated"],
          "suggested_improvements": ["Add uncertainty notes"]
        }
        """
    )
    agent.save_to_gold_layer = lambda query, final_report: None

    output = agent.generate_consensus_report(
        "Assess oil transit risk",
        [{"title": "Oil tanker disruption", "content": "Tanker disruption evidence"}],
    )

    assert "## Final Risk Assessment" in output
    assert "Final Risk Score: 3" in output
    assert "### Uncertainty Notes" in output
    assert "missing_evidence" in agent.last_audit["critic_feedback"]
    assert "Initial report" not in output


def test_generate_consensus_report_falls_back_when_critic_fails():
    agent = make_agent()
    agent.openai_client = FakeOpenAIClient([
        "Initial report with Risk Score: 4 [Source 1]",
        RuntimeError("revision provider unavailable"),
    ])
    agent.anthropic_client = FakeAnthropicClient(RuntimeError("critic unavailable"))
    agent.save_to_gold_layer = lambda query, final_report: None

    output = agent.generate_consensus_report(
        "Assess oil transit risk",
        [{"title": "Oil tanker disruption", "content": "Tanker disruption evidence"}],
    )

    assert "Final Risk Score: 4" in output
    assert "Critic review failed" in output or "Revision step failed" in output
    assert agent.last_audit["critic_warning"].startswith("Critic review failed")
