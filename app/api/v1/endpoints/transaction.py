# app/api/v1/endpoints/transaction.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.transaction_service import TransactionService
from app.schemas.transaction import TransactionPublic

router = APIRouter(tags=["Transactions"])


@router.get(
    "/accounts/{account_id}/transactions",
    response_model=list[TransactionPublic],
    summary="获取指定账户下的所有交易记录",
)
async def get_transactions_for_account(
    account_id: int,
    session: AsyncSession = Depends(get_db),
    service: TransactionService = Depends(),
    skip: int = 0,
    limit: int = 100,
):
    """
    获取指定银行账户下所有交易记录的列表，按交易日期降序排列。
    """
    return await service.get_transactions_for_account(
        session, account_id=account_id, skip=skip, limit=limit
    )


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionPublic,
    summary="获取单笔交易详情",
)
async def get_transaction_by_id(
    transaction_id: int,
    session: AsyncSession = Depends(get_db),
    service: TransactionService = Depends(),
):
    """
    根据ID获取单笔交易的详细信息，包含账户和对手方信息。
    """
    return await service.get_transaction_by_id(session, transaction_id=transaction_id)
