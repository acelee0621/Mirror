# app_streamlit/pages/7_Group_Analysis.py

import os
import streamlit as st
import requests
import pandas as pd
import altair as alt
from navigation import make_sidebar

# --- 配置 ---
API_BASE_URL = os.getenv("STREAMLIT_API_BASE_URL", "http://127.0.0.1:8000/api/v1")

# --- 页面配置 ---
st.set_page_config(
    page_title="共同对手方分析 - 明镜 D-Sensor", page_icon="🔗", layout="wide"
)
make_sidebar()
st.title("🔗 共同对手方分析")
st.markdown(
    "选择多个用户，系统将自动找出同时与他们存在资金往来的**共同对手方**，揭示隐藏的关联网络。"
)

# --- 会话状态初始化 ---
if "group_summary_df" not in st.session_state:
    st.session_state.group_summary_df = pd.DataFrame()
if "group_detail_df" not in st.session_state:
    st.session_state.group_detail_df = pd.DataFrame()


# --- API 调用函数 ---
@st.cache_data(ttl=60)
def get_all_persons():
    try:
        response = requests.get(f"{API_BASE_URL}/persons/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []


def load_group_analysis_data(person_ids: list[int], person_df: pd.DataFrame):
    if not person_ids or len(person_ids) < 2:
        st.warning("请至少选择两位用户以进行共同对手方分析。")
        st.session_state.group_summary_df = pd.DataFrame()
        st.session_state.group_detail_df = pd.DataFrame()
        return

    with st.spinner("正在执行联合分析，寻找共同对手方..."):
        try:
            # 1. 获取共同对手方的聚合分析数据
            summary_response = requests.post(
                f"{API_BASE_URL}/analysis/group/counterparties",
                json={"person_ids": person_ids},
            )
            summary_response.raise_for_status()
            summary_data = summary_response.json()
            st.session_state.group_summary_df = pd.DataFrame(summary_data)

            # 2. 获取所有相关人员的交易明细数据
            detail_response = requests.post(
                f"{API_BASE_URL}/analysis/group/transactions",
                json={"person_ids": person_ids},
            )
            detail_response.raise_for_status()
            detail_data = detail_response.json()
            if detail_data:
                detail_df = pd.DataFrame(detail_data)
                # 预处理明细数据
                detail_df["transaction_date"] = pd.to_datetime(
                    detail_df["transaction_date"]
                ).dt.tz_convert("Asia/Shanghai")

                # --- 【核心修复点】: 同时提取 account_name 和 owner_name ---
                detail_df["counterparty_name"] = detail_df["counterparty"].apply(
                    lambda x: x["name"]
                )

                # 从嵌套的 account 字典中提取账户名
                detail_df["account_name"] = detail_df["account"].apply(
                    lambda x: x["account_name"]
                )

                # 创建一个从 person_id 到 full_name 的映射字典
                person_id_to_name = person_df.set_index("id")["full_name"]
                # 正确地从嵌套的 owner 字典中访问 id，然后映射为所有者名称
                detail_df["owner_name"] = (
                    detail_df["account"]
                    .apply(lambda x: x["owner"]["id"])
                    .map(person_id_to_name)
                )

                st.session_state.group_detail_df = detail_df
            else:
                st.session_state.group_detail_df = pd.DataFrame()

        except requests.exceptions.RequestException as e:
            st.error(f"联合分析失败: {e}")
            st.session_state.group_summary_df = pd.DataFrame()
            st.session_state.group_detail_df = pd.DataFrame()


# --- 页面布局与逻辑 ---
persons = get_all_persons()
if not persons:
    st.warning("系统中还没有任何用户。")
else:
    person_df = pd.DataFrame(persons)
    st.markdown("#### 选择要进行联合分析的用户组")
    selected_person_names = st.multiselect(
        "选择用户 (至少两位)",
        options=person_df["full_name"].tolist(),
        placeholder="请选择用户...",
    )

    if st.button("🚀 开始分析共同对手方", disabled=len(selected_person_names) < 2):
        selected_person_ids = person_df[
            person_df["full_name"].isin(selected_person_names)
        ]["id"].tolist()
        load_group_analysis_data(selected_person_ids, person_df)

    # --- 结果展示 ---
    if not st.session_state.group_summary_df.empty:
        summary_df = st.session_state.group_summary_df.copy()
        detail_df = st.session_state.group_detail_df.copy()

        st.markdown("---")
        st.markdown("### **共同对手方分析结果**")

        # 指标卡片
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric(label="🔗 共同对手方总数", value=len(summary_df))
        kpi2.metric(
            label="💰 涉及总流水", value=f"¥ {summary_df['total_flow'].sum():,.2f}"
        )
        if not summary_df.empty:
            top_flow_contact = summary_df.loc[summary_df["total_flow"].idxmax()]
            kpi3.metric(
                label="🔗 最大资金往来共同对手", value=str(top_flow_contact["name"])
            )
            top_freq_contact = summary_df.loc[summary_df["transaction_count"].idxmax()]
            kpi4.metric(
                label="📞 最频繁交易共同对手", value=str(top_freq_contact["name"])
            )

        # 图表
        st.markdown("#### Top 10 共同对手方资金往来 (按总流水)")
        top_10 = summary_df.nlargest(10, "total_flow", keep="all")
        chart = (
            alt.Chart(top_10)
            .mark_bar()
            .encode(
                x=alt.X("net_flow:Q", title="净流量 (元)"),
                y=alt.Y(
                    "name:N",
                    sort=alt.EncodingSortField(
                        field="total_flow", op="sum", order="descending"
                    ),
                    title="对手方",
                ),
                color=alt.condition(
                    alt.datum.net_flow > 0, alt.value("#2E8B57"), alt.value("#D26466")
                ),
                tooltip=[
                    "name",
                    "total_income",
                    "total_expense",
                    "net_flow",
                    "transaction_count",
                    "total_flow",
                ],
            )
            .properties(height=400)
        )
        st.altair_chart(chart, use_container_width=True)

        # 详细的下钻分析
        st.markdown("#### 共同对手方交易明细")
        sorted_summary_df = summary_df.sort_values("total_flow", ascending=False)
        for _, opponent in sorted_summary_df.iterrows():
            opponent_name = opponent["name"]
            with st.expander(
                f"**{opponent_name}** (总流水: ¥ {opponent['total_flow']:,.2f} | 交易次数: {opponent['transaction_count']})"
            ):
                opponent_transactions = detail_df[
                    detail_df["counterparty_name"] == opponent_name
                ].copy()
                if not opponent_transactions.empty:
                    # 按用户名进行分组展示
                    for (
                        owner_name,
                        transactions_by_owner,
                    ) in opponent_transactions.groupby("owner_name"):
                        st.markdown(f"**关联人: {owner_name}**")
                        type_mapping = {"CREDIT": "收入", "DEBIT": "支出"}
                        transactions_by_owner["type_cn"] = transactions_by_owner[
                            "transaction_type"
                        ].map(type_mapping)

                        st.dataframe(
                            transactions_by_owner[
                                [
                                    "transaction_date",
                                    "description",
                                    "amount",
                                    "type_cn",
                                    "account_name",
                                ]
                            ],
                            column_config={
                                "transaction_date": st.column_config.DatetimeColumn(
                                    "交易时间 (北京)", format="YYYY-MM-DD HH:mm:ss"
                                ),
                                "account_name": "所属账户",
                                "description": "摘要",
                                "amount": st.column_config.NumberColumn(
                                    "金额", format="¥ %.2f"
                                ),
                                "type_cn": "类型",
                            },
                            use_container_width=True,
                            hide_index=True,
                        )
                else:
                    st.info("在加载的交易明细中未找到与此对手方的具体交易记录。")

    elif (
        "group_summary_df" in st.session_state
        and st.session_state.group_summary_df is not None
    ):
        st.info("分析完毕，在所选用户中未发现任何共同的对手方。")
