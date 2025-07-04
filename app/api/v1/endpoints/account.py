# app/api/v1/endpoints/account.py
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.account_service import AccountService
from app.schemas.account import AccountCreate, AccountUpdate, AccountPublicWithOwner
from app.services.transaction_service import TransactionService
from app.schemas.transaction import TransactionPublic

router = APIRouter()


@router.post(
    "/persons/{person_id}/accounts",
    response_model=AccountPublicWithOwner,
    status_code=status.HTTP_201_CREATED,
    summary="为指定用户创建新账户",
    tags=["Persons"],
)
async def create_new_account(
    person_id: int,
    account_in: AccountCreate,
    session: AsyncSession = Depends(get_db),
    service: AccountService = Depends(),
):
    return await service.create_account(
        session, owner_id=person_id, account_in=account_in
    )


@router.get(
    "/accounts/{account_id}",
    response_model=AccountPublicWithOwner,
    summary="获取指定ID的账户",
    tags=["Accounts"],
)
async def get_account_by_id(
    account_id: int,
    session: AsyncSession = Depends(get_db),
    service: AccountService = Depends(),
):
    return await service.get_account_by_id(session, account_id=account_id)


@router.patch(
    "/accounts/{account_id}",
    response_model=AccountPublicWithOwner,
    summary="更新账户信息",
    tags=["Accounts"],
)
async def update_account_info(
    account_id: int,
    account_in: AccountUpdate,
    session: AsyncSession = Depends(get_db),
    service: AccountService = Depends(),
):
    return await service.update_account(
        session, account_id=account_id, account_in=account_in
    )


@router.delete(
    "/accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除账户",
    tags=["Accounts"],
)
async def delete_account_by_id(
    account_id: int,
    session: AsyncSession = Depends(get_db),
    service: AccountService = Depends(),
):
    await service.delete_account(session, account_id=account_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/accounts/{account_id}/transactions",
    response_model=list[TransactionPublic],
    summary="获取指定账户下的所有交易记录",
    tags=["Accounts"],
)
async def get_transactions_for_account(
    account_id: int,
    session: AsyncSession = Depends(get_db),
    service: TransactionService = Depends(),
    skip: int = 0,
    limit: int = 100,
):
    """
    获取指定银行账户下所有交易记录的列表，按交易时间升序排序。
    """
    return await service.get_transactions_for_account(
        session, account_id=account_id, skip=skip, limit=limit
    )
