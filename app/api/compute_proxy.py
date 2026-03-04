"""
Compute Proxy API Endpoints
Lightweight compute endpoints for interactive visualization workflows.
"""

import logging
from typing import List, Dict, Any, Union

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.fragment_matcher import match_fragments
from app.services.modification_matcher import match_modifications

logger = logging.getLogger(__name__)
router = APIRouter()


class SpectrumPeak(BaseModel):
    mz: float
    intensity: float


class FragmentMatchRequest(BaseModel):
    sequence: str = Field(..., min_length=1)
    spectrumData: List[SpectrumPeak]
    ppmTolerance: float = Field(default=20.0, gt=0)


class FragmentMatchResponse(BaseModel):
    annotations: List[Dict[str, Any]]


class ModificationSearchRequest(BaseModel):
    selectedPeaks: List[SpectrumPeak]
    modificationDb: Union[str, List[Dict[str, Any]]]
    ppmTolerance: float = Field(default=20.0, gt=0)


class ModificationSearchResponse(BaseModel):
    matches: List[Dict[str, Any]]


@router.post("/fragment-match", response_model=FragmentMatchResponse)
async def fragment_match(request: FragmentMatchRequest) -> FragmentMatchResponse:
    try:
        annotations = match_fragments(
            sequence=request.sequence,
            spectrum_data=[peak.model_dump() for peak in request.spectrumData],
            ppm_tolerance=request.ppmTolerance,
        )
        return FragmentMatchResponse(annotations=annotations)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Fragment match failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fragment match failed",
        ) from exc


@router.post("/modification-search", response_model=ModificationSearchResponse)
async def modification_search(request: ModificationSearchRequest) -> ModificationSearchResponse:
    try:
        matches = match_modifications(
            selected_peaks=[peak.model_dump() for peak in request.selectedPeaks],
            modification_db=request.modificationDb,
            ppm_tolerance=request.ppmTolerance,
        )
        return ModificationSearchResponse(matches=matches)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Modification search failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Modification search failed",
        ) from exc
