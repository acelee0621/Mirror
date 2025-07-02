# app/api/v1/endpoints/counterparty.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.services.counterparty_service import CounterpartyService
from app.schemas.counterparty import CounterpartyPublic

router = APIRouter(prefix="/counterparties", tags=["Counterparties"])


@router.get(
    "/", response_model=List[CounterpartyPublic], summary="获取所有交易对手列表"
)
async def get_all_counterparties(
    session: AsyncSession = Depends(get_db),
    service: CounterpartyService = Depends(),
    skip: int = 0,
    limit: int = 100,
):
    """
    获取系统中所有出现过的交易对手方。
    """
    return await service.get_all_counterparties(session, skip=skip, limit=limit)


@router.get(
    "/{counterparty_id}",
    response_model=CounterpartyPublic,
    summary="获取指定ID的交易对手",
)
async def get_counterparty_by_id(
    counterparty_id: int,
    session: AsyncSession = Depends(get_db),
    service: CounterpartyService = Depends(),
):
    """
    根据ID获取单个交易对手的详细信息。
    """
    return await service.get_counterparty_by_id(
        session, counterparty_id=counterparty_id
    )
