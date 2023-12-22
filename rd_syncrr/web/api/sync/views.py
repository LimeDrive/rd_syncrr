from typing import List  # noqa: UP035

from fastapi import APIRouter, Depends, HTTPException, Query

from rd_syncrr.services.media_db.dao import MediaDAO
from rd_syncrr.tasks import process_torrents_data
from rd_syncrr.utils.security import api_key_security
from rd_syncrr.web.api.sync.schema import TorrentModelDTO

router = APIRouter()


@router.get(
    "/torrents",
    dependencies=[Depends(api_key_security)],
    response_model=List[TorrentModelDTO],
)
async def torrents(
    dao: MediaDAO = Depends(),  # noqa: B008
    offset: int = Query(
        0,
        alias="offset",
        description="the offset to start from",
    ),
    limit: int = Query(
        50,
        alias="limit",
        description="the number of torrents to return",
    ),
) -> List[TorrentModelDTO]:  # type: ignore
    try:
        async with dao:
            return await process_torrents_data(dao, limit=limit, offset=offset)  # type: ignore
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
