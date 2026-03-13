from typing import TypedDict, List, Any


class AnalysisState(TypedDict, total=False):
    # --- Input ---
    ticker: str
    analysis_date: str

    # --- Fetched raw data ---
    company_name: str
    current_price: float
    info: dict
    price_history: List[dict]
    financials: dict
    news: List[dict]
    analyst_recommendations: Any

    # --- Agent outputs ---
    market_intelligence: dict   # Agent 1
    macro_analysis: dict        # Agent 2
    fundamental_analysis: dict  # Agent 3
    technical_analysis: dict    # Agent 4
    sentiment_analysis: dict    # Agent 5
    risk_assessment: dict       # Agent 6
    final_recommendation: dict  # Agent 7 (Chief Investment Analyst)

    # --- Report ---
    report_markdown: str
    report_path: str

    # --- Meta ---
    errors: List[str]
