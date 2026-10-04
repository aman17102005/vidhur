from fastapi import APIRouter, HTTPException

from ..ai.base import SYSTEM_PROMPT, AIProviderError, build_user_prompt
from ..ai.registry import get_provider
from ..models import ExplainRequest, ExplainResponse

router = APIRouter()


@router.post("/explain", response_model=ExplainResponse)
async def explain_route(req: ExplainRequest) -> ExplainResponse:
    provider = get_provider(req.provider)
    api_key = req.api_key.strip()
    try:
        text = await provider.explain(
            api_key=api_key,
            model=req.model or provider.default_model,
            system=SYSTEM_PROMPT,
            user=build_user_prompt(req.content, req.verdict, req.findings),
        )
    except AIProviderError as e:
        raise HTTPException(502, str(e))
    finally:
        # The key lives only in this request's local variables; drop references right away.
        api_key = None  # noqa: F841
        req.api_key = ""
    if not text:
        raise HTTPException(502, "The AI provider returned an empty answer.")
    return ExplainResponse(explanation=text)
