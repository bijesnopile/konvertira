"""Temporary result download route."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from backend.services.storage import api_storage
from backend.services.security import enforce_general_rate
from backend.services.result_downloads import ResultDownloadResponse, download_error

router = APIRouter()


@router.get("/download/{token}")
async def download_result(token: str, request: Request) -> Response:
    try:
        enforce_general_rate(request)
    except HTTPException as exc:
        return download_error(exc)
    return ResultDownloadResponse(api_storage, token,
                                  "File is no longer available. Generate a new cleaned image.")
