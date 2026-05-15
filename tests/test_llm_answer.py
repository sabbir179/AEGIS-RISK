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
