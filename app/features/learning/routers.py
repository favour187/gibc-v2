"""Competition-specific module: learning.

Placeholder status router. The real product logic will be added here in the
dedicated build phase for this competition, keeping all competition-specific
code separate from the generic foundation.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/status")
def feature_status() -> dict:
    return {
        "feature": "learning",
        "status": "planned",
        "note": "Adaptive learning engine: mastery model, personalized paths, AI explanations & practice, progress analytics. Track 03 (Open).",
    }
