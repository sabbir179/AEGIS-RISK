from graphviz import Digraph

dot = Digraph(format='png')
dot.attr(rankdir='LR')

dot.node('A', 'News Sources')
dot.node('B', 'Ingestion\n(Fetcher, Dedupe, Parser)')
dot.node('C', 'Preprocessing')
dot.node('D', 'Retrieval / Context')
dot.node('E', 'Prompt Engineering')
dot.node('F', 'LLM Inference')
dot.node('G', 'Output Structuring')
dot.node('H', 'Risk Scoring')
dot.node('I', 'Database')
dot.node('J', 'Analytics & Aggregation')
dot.node('K', 'Dashboard (Streamlit)')
dot.node('L', 'Vector DB (Chroma)')
dot.node('M', 'Feedback Layer')
dot.node('N', 'Re-analysis Trigger')
dot.node('O', 'Alerts & Watchpoints')

dot.edges([
    ('A','B'), ('B','C'), ('C','D'), ('D','E'),
    ('E','F'), ('F','G'), ('G','H'), ('H','I'),
    ('I','J'), ('J','K')
])

dot.edge('I','L')
dot.edge('L','D')

dot.edge('K','M')
dot.edge('M','N')
dot.edge('N','D')

dot.edge('H','O')
dot.edge('O','K')

dot.render('aegis_risk_architecture_agentic', view=True)