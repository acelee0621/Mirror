# app/api/v1/endpoints/person.py
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.person_service import PersonService
from app.services.transaction_service import TransactionService
from app.schemas.transaction import TransactionPublic
from app.services.counterparty_service import CounterpartyService
from app.schemas.counterparty import CounterpartySummary, CounterpartyAnalysisSummary
from app.schemas.person import (
    PersonCreate,
    PersonUpdate,
    PersonPublic,
    PersonWithAccounts,
)

router = APIRouter(prefix="/persons", tags=["Persons"])


@router.post(
    "/",
    response_model=PersonPublic,
    status_code=status.HTTP_201_CREATED,
    summary="创建新用户",
)
async def create_new_person(
    person_in: PersonCreate,
    session: AsyncSession = Depends(get_db),
    service: PersonService = Depends(),
):
    return await service.create_person(session, person_in=person_in)


@router.get("/", response_model=list[PersonPublic], summary="获取用户列表")
async def get_all_persons(
    session: AsyncSession = Depends(get_db),
    service: PersonService = Depends(),
    skip: int = 0,
    limit: int = 100,
):
    return await service.get_all_persons(session, skip=skip, limit=limit)


@router.get(
    "/{person_id}",
    response_model=PersonWithAccounts,
    summary="获取指定ID的用户（包含其所有账户）",
)
async def get_person_by_id(
    person_id: int,
    session: AsyncSession = Depends(get_db),
    service: PersonService = Depends(),
):
    return await service.get_person_by_id(session, person_id=person_id)


@router.patch("/{person_id}", response_model=PersonWithAccounts, summary="更新用户信息")
async def update_person_info(
    person_id: int,
    person_in: PersonUpdate,
    session: AsyncSession = Depends(get_db),
    service: PersonService = Depends(),
):
    return await service.update_person(
        session, person_id=person_id, person_in=person_in
    )


@router.delete(
    "/{person_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除用户"
)
async def delete_person_by_id(
    person_id: int,
    session: AsyncSession = Depends(get_db),
    service: PersonService = Depends(),
):
    await service.delete_person(session, person_id=person_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{person_id}/transactions",
    response_model=list[TransactionPublic],
    summary="获取一个用户所有账户的全部交易记录",
)
async def get_transactions_for_person(
    person_id: int,
    session: AsyncSession = Depends(get_db),
    service: TransactionService = Depends(),
    skip: int = 0,
    limit: int = 100,
):
    """
    获取一个用户所有账户下的全部交易记录，按交易时间升序排序。
    """
    return await service.get_transactions_for_person(
        session, person_id=person_id, skip=skip, limit=limit
    )


@router.get(
    "/{person_id}/counterparties/summary",
    response_model=list[CounterpartySummary],
    summary="获取一个用户所有对手方的资金往来汇总",
)
async def get_counterparty_summary_for_person(
    person_id: int,
    session: AsyncSession = Depends(get_db),
    service: CounterpartyService = Depends(),
):
    """
    获取一个用户与他所有对手方的资金往来汇总统计，
    包含总收入、总支出、净流量和交易次数，按总交易绝对值降序排序。
    """
    return await service.get_summary_by_person_id(session, person_id=person_id)


@router.get(
    "/{person_id}/counterparties/analysis_summary",
    response_model=list[CounterpartyAnalysisSummary],
    summary="获取按名称聚合的对手方分析汇总",
    tags=["Persons"],
)
async def get_counterparty_analysis_for_person(
    person_id: int,
    session: AsyncSession = Depends(get_db),
    service: CounterpartyService = Depends(),
):
    return await service.get_analysis_summary_by_person_id(session, person_id=person_id)
