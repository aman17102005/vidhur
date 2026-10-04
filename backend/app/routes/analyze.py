from fastapi import APIRouter, HTTPException

from ..models import AnalysisResult, AnalyzeRequest
from ..rules.engine import analyze
from ..rules.extract import extract_entities

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResult)
def analyze_route(req: AnalyzeRequest) -> AnalysisResult:
    if req.mode == "url" and not extract_entities(req.content).urls:
        raise HTTPException(422, "That does not look like a web link. Paste the full link, for example https://example.com/page")
    return analyze(req.content)
