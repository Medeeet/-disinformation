from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    text: str = ""
    url: str = ""


class RuleScores(BaseModel):
    clickbait: float = 0.0
    linguistic: float = 0.0
    source_credibility: float = 0.0
    structural: float = 0.0
    fact_check: float | None = None


class AnalyzeResponse(BaseModel):
    analysis_id: str
    overall_score: float
    verdict: str
    verdict_label: str
    verdict_description: str
    ml_score: float | None = None
    rule_scores: RuleScores
    flagged_patterns: list[str] = []
    input_text: str = ""


class SourceRequest(BaseModel):
    domain: str
    credibility_score: float
    category: str = ""
    notes: str = ""
