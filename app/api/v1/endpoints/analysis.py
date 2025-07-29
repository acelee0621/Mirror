# app/api/v1/endpoints/analysis.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.analysis_service import analysis_service, AnalysisService
from app.schemas.analysis import (
    UturnAnalysisRequest,
    UturnAnalysisResponse,
    UturnEvent,
    GroupAnalysisRequest,
)
from app.schemas.transaction import TransactionPublicWithOwner
from app.schemas.counterparty import CounterpartyAnalysisSummary

router = APIRouter(prefix="/analysis", tags=["🔬 Analysis"])


@router.post(
    "/persons/{person_id}/u-turn",
    response_model=UturnAnalysisResponse,
    summary="运行“快进快出”资金分析",
)
async def run_u_turn_analysis(
    person_id: int,
    request: UturnAnalysisRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    对指定用户的交易数据进行“快进快出”（U-Turn）模式检测。

    - **amount_threshold**: 定义什么是大额交易。
    - **time_window_hours**: 从大额收入发生后，在多长时间内寻找匹配的支出。
    - **amount_tolerance**: 金额匹配的容忍度，例如0.1代表总支出在收入金额的90%-110%范围内即可。
    """
    # 1. 调用服务层，获取包含完整ORM对象的事件列表
    orm_events = await analysis_service.detect_u_turn_transactions(
        session=session,
        person_id=person_id,
        amount_threshold=request.amount_threshold,
        time_window_hours=request.time_window_hours,
        amount_tolerance=request.amount_tolerance,
    )

    # 2. 遍历服务层返回的每一个事件字典
    validated_events: list[UturnEvent] = []
    for event in orm_events:
        # 3. 使用从事件字典中获取的数据，显式地创建一个 UturnEvent 对象
        #    Pydantic 会在这里自动将 Transaction ORM 对象转换为 TransactionPublic Schema
        validated_event = UturnEvent(
            inflow=event["inflow"],
            outflows=event["outflows"],
            total_outflow=event["total_outflow"],
            time_diff_hours=event["time_diff_hours"],
        )
        validated_events.append(validated_event)

    # 4. 将经过验证和转换的 Pydantic 对象列表传递给最终的响应模型
    return UturnAnalysisResponse(found_events=validated_events)


@router.post(
    "/group/transactions",
    response_model=list[TransactionPublicWithOwner],
    summary="执行多人联合交易流水分析",
)
async def run_group_transaction_analysis(
    request: GroupAnalysisRequest,
    session: AsyncSession = Depends(get_db),
    service: AnalysisService = Depends(),
):
    """
    接收一个用户ID列表，返回这些用户合并后的、按时间排序的完整交易流水。
    """
    return await service.perform_group_transaction_analysis(
        session, person_ids=request.person_ids
    )


@router.post(
    "/group/counterparties",
    response_model=list[CounterpartyAnalysisSummary],
    summary="执行多人联合对手方分析",
)
async def run_group_counterparty_analysis(
    request: GroupAnalysisRequest,
    session: AsyncSession = Depends(get_db),
    service: AnalysisService = Depends(),
):
    """
    接收一个用户ID列表，返回这些用户合并后的、按名称聚合的对手方网络分析。
    """
    return await service.perform_group_counterparty_analysis(
        session, person_ids=request.person_ids
    )
