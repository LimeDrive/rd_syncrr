import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from rd_syncrr.utils.security import api_key_security
from rd_syncrr.web.api.sync.schema import Torrent

router = APIRouter()


@router.get(
    "/fetchAll",
    dependencies=[Depends(api_key_security)],
    response_model=list[Torrent],
)
async def get_all_torrents() -> Any:
    """
    Fetches all downloaded torrents from rd.

    Returns:
        dict: The downloaded torrents.

    Raises:
        HTTPException: If the file is not found.
        HTTPException: If the JSON is invalid.
        HTTPException: If an unexpected error occurs.
    """
    try:
        with open(
            "/Users/limehub/Documents/Github/rd_syncrr/rd_syncrr/utils/tasks/all_torrents.json",
        ) as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(  # noqa: B904, TRY200
            status_code=404,
            detail="File not found",
        )
    except json.JSONDecodeError:
        raise HTTPException(  # noqa: B904, TRY200
            status_code=400,
            detail="Invalid JSON",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # noqa: B904, TRY200


@router.get(
    "/fetchLatest",
    dependencies=[Depends(api_key_security)],
    response_model=list[Torrent],
)
async def get_latest_torrents() -> Any:
    """
    Fetches the 25 latest downloaded torrents from rd.

    Returns:
        dict: The latest downloaded torrents.

    Raises:
        HTTPException: If the file is not found.
        HTTPException: If the JSON is invalid.
        HTTPException: If an unexpected error occurs.
    """
    try:
        with open(
            "/Users/limehub/Documents/Github/rd_syncrr/rd_syncrr/utils/tasks/latest_torrents.json",
        ) as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(  # noqa: B904, TRY200
            status_code=404,
            detail="File not found",
        )
    except json.JSONDecodeError:
        raise HTTPException(  # noqa: B904, TRY200
            status_code=400,
            detail="Invalid JSON",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  # noqa: B904, TRY200
