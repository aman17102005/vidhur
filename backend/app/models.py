from typing import List, Optional

from pydantic import BaseModel, Field

MAX_CONTENT_CHARS = 10_000


class Finding(BaseModel):
    id: str
    severity: str  # "low" | "medium" | "high"
    reason: str
    evidence: Optional[str] = None
    action: str = "verify"


class AnalysisResult(BaseModel):
    verdict: str  # "safe" | "suspicious" | "high_risk"
    findings: List[Finding]
    next_step: str
    report_hint: Optional[str] = None


class AnalyzeRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=MAX_CONTENT_CHARS)
    mode: str = Field("text", pattern="^(text|url|qr|screenshot)$")


class OcrResponse(BaseModel):
    text: str
    result: AnalysisResult


class ExplainRequest(BaseModel):
    provider: str = Field(..., pattern="^(openai|anthropic|gemini|grok)$")
    api_key: str = Field(..., min_length=8, max_length=512)
    model: Optional[str] = Field(None, pattern=r"^[A-Za-z0-9._:\-/]{1,80}$")
    content: str = Field(..., min_length=1, max_length=MAX_CONTENT_CHARS)
    verdict: str
    findings: List[Finding]


class ExplainResponse(BaseModel):
    explanation: str
