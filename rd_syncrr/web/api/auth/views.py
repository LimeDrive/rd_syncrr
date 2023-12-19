from fastapi import APIRouter, Depends, Query

from rd_syncrr.services.security_db import security_db_accsess
from rd_syncrr.settings import settings
from rd_syncrr.utils.security import secret_based_security
from rd_syncrr.web.api.auth.schemas import UsageLog, UsageLogs

router = APIRouter()


@router.get(
    "/new",
    dependencies=[Depends(secret_based_security)],
    include_in_schema=settings.security_hide_docs,
)
def get_new_api_key(
    name: str = Query(
        None,
        description="set API key name",
    ),
    never_expires: bool = Query(
        False,
        description="if set, the created API key will never be considered expired",
    ),
) -> str:
    """
    Returns:
        api_key: a newly generated API key
    """
    return security_db_accsess.create_key(name, never_expires)


@router.get(
    "/revoke",
    dependencies=[Depends(secret_based_security)],
    include_in_schema=settings.security_hide_docs,
)
def revoke_api_key(
    api_key: str = Query(..., alias="api-key", description="the api_key to revoke"),
):
    """
    Revokes the usage of the given API key

    """
    return security_db_accsess.revoke_key(api_key)


@router.get(
    "/renew",
    dependencies=[Depends(secret_based_security)],
    include_in_schema=settings.security_hide_docs,
)
def renew_api_key(
    api_key: str = Query(..., alias="api-key", description="the API key to renew"),
    expiration_date: str = Query(
        None,
        alias="expiration-date",
        description="the new expiration date in ISO format",
    ),
):
    """
    Renews the chosen API key, reactivating it if it was revoked.
    """
    return security_db_accsess.renew_key(api_key, expiration_date)


@router.get(
    "/logs",
    dependencies=[Depends(secret_based_security)],
    response_model=UsageLogs,
    include_in_schema=settings.security_hide_docs,
)
def get_api_key_usage_logs():
    """
    Returns usage information for all API keys
    """
    # TODO Add some sort of filtering on older keys/unused keys?

    return UsageLogs(
        logs=[
            UsageLog(
                api_key=row[0],
                is_active=row[1],
                never_expire=row[2],
                expiration_date=row[3],
                latest_query_date=row[4],
                total_queries=row[5],
                name=row[6],
            )
            for row in security_db_accsess.get_usage_stats()
        ],
    )
