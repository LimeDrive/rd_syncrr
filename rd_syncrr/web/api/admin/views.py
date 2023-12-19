"""Trigger views."""

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from rd_syncrr.utils.security import secret_based_security
from rd_syncrr.utils.tasks import process_torrents
from rd_syncrr.utils.tasks.torrents_action import check_hash_availability
from rd_syncrr.web.api.admin.schemas import TestedHash, UpdateResponse

router = APIRouter()


@router.post(
    "/refresh/hashlist",
    dependencies=[Depends(secret_based_security)],
    response_model=UpdateResponse,
    status_code=202,
)
async def update_torrents_list_info() -> UpdateResponse:
    """Trigger an update of torrents list from your RD account."""
    try:
        await process_torrents()
        message = UpdateResponse(message="torrents list update triggered")
        return message  # noqa: TRY300
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # noqa: B904, TRY200


@router.post(
    "/refresh/sync",
    dependencies=[Depends(secret_based_security)],
    status_code=202,
)
async def refresh_instance_sync() -> dict[str, str]:
    """Trigger an update of torrents list from your synced RD account."""
    return {"hello": "world"}


@router.post(
    "/test/cached/{hash}",
    dependencies=[Depends(secret_based_security)],
    response_model=dict[int, TestedHash],
)
async def test_hash_in_rd_cache(
    hash: str,  # noqa: A002
) -> dict[str, Any] | Literal[True]:
    """Test hash to check if the files are cached in RD."""
    try:
        aviability = await check_hash_availability(hash)
        if aviability:
            return aviability
        else:
            raise HTTPException(  # noqa: TRY301
                status_code=404,
                detail="Torrent not available",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # noqa: B904, TRY200


@router.post(
    "/add/magnet",
    dependencies=[Depends(secret_based_security)],
    status_code=202,
)
async def add_magnet_to_rd(
    magnet: str = Query(..., description="The magnet link to add to RD."),
) -> dict[str, str]:
    """Add a magnet to RD."""
    return {"hello": "world"}


# add_torrents_to_rd
