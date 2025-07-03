import streamlit as st
import requests
import pandas as pd
import altair as alt
from navigation import make_sidebar


# --- 配置 ---
API_BASE_URL = "http://127.0.0.1:8000/api/v1"

st.set_page_config(page_title="交易看板 - 明镜 D-Sensor", page_icon="📊", layout="wide")

make_sidebar()  # 一定要在set_page_config之后调用

st.title("📊 交易分析看板")
st.markdown("在这里，您可以查看、筛选和分析您所有账户的交易流水。")

# --- 会话状态初始化 ---
if "selected_person_id" not in st.session_state:
    st.session_state.selected_person_id = None
if "selected_account_id" not in st.session_state:
    st.session_state.selected_account_id = None
if "transactions_df" not in st.session_state:
    st.session_state.transactions_df = pd.DataFrame()
if "loaded_account_id" not in st.session_state:
    st.session_state.loaded_account_id = None


# --- API 调用函数 ---
@st.cache_data(ttl=60)
def get_all_persons():
    try:
        response = requests.get(f"{API_BASE_URL}/persons/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []


@st.cache_data(ttl=60)
def get_person_accounts(person_id: int):
    if not person_id:
        return []
    try:
        response = requests.get(f"{API_BASE_URL}/persons/{person_id}")
        response.raise_for_status()
        return response.json().get("accounts", [])
    except requests.exceptions.RequestException:
        return []


def load_transactions(account_id: int):
    if not account_id:
        st.session_state.transactions_df = pd.DataFrame()
        return
    with st.spinner("正在加载交易数据..."):
        try:
            all_transactions = []
            limit, skip = 100, 0
            while True:
                response = requests.get(
                    f"{API_BASE_URL}/accounts/{account_id}/transactions",
                    params={"skip": skip, "limit": limit},
                )
                response.raise_for_status()
                data = response.json()
                if not data:
                    break
                all_transactions.extend(data)
                skip += limit

            if all_transactions:
                df = pd.DataFrame(all_transactions)
                df["transaction_date"] = pd.to_datetime(
                    df["transaction_date"]
                ).dt.tz_convert("Asia/Shanghai")
                df["account_name"] = df["account"].apply(lambda x: x["account_name"])
                df["counterparty_name"] = df["counterparty"].apply(lambda x: x["name"])
                df.drop(columns=["account", "counterparty"], inplace=True)
                st.session_state.transactions_df = df
            else:
                st.session_state.transactions_df = pd.DataFrame()
        except requests.exceptions.RequestException as e:
            st.error(f"加载交易数据失败: {e}")
            st.session_state.transactions_df = pd.DataFrame()


@st.cache_data
def convert_df_to_csv(df: pd.DataFrame):
    return df.to_csv(index=False).encode("utf-8-sig")


# --- 页面布局与逻辑 ---
persons = get_all_persons()
if not persons:
    st.warning("系统中还没有任何用户。")
else:
    person_df = pd.DataFrame(persons)

    person_index = None
    if st.session_state.selected_person_id is not None:
        matching_person = person_df[
            person_df["id"] == st.session_state.selected_person_id
        ]
        if not matching_person.empty:
            person_index = int(matching_person.index[0])

    selected_person_name = st.selectbox(
        "第一步：选择用户",
        options=person_df["full_name"],
        index=person_index,
        placeholder="请选择一个用户...",
    )

    if selected_person_name:
        st.session_state.selected_person_id = person_df[
            person_df["full_name"] == selected_person_name
        ]["id"].iloc[0]
        accounts = get_person_accounts(st.session_state.selected_person_id)

        if accounts:
            account_df = pd.DataFrame(accounts)

            account_index = None
            if st.session_state.selected_account_id is not None:
                matching_account = account_df[
                    account_df["id"] == st.session_state.selected_account_id
                ]
                if not matching_account.empty:
                    account_index = int(matching_account.index[0])

            selected_account_name = st.selectbox(
                "第二步：选择银行账户",
                options=account_df["account_name"],
                index=account_index,
                placeholder="请选择一个银行账户进行分析...",
                key="selectbox_account",
            )

            if selected_account_name:
                st.session_state.selected_account_id = account_df[
                    account_df["account_name"] == selected_account_name
                ]["id"].iloc[0]
                if (
                    st.session_state.selected_account_id
                    != st.session_state.loaded_account_id
                ):
                    load_transactions(st.session_state.selected_account_id)
                    st.session_state.loaded_account_id = (
                        st.session_state.selected_account_id
                    )
                    st.rerun()
            else:
                st.session_state.transactions_df = pd.DataFrame()
                st.session_state.loaded_account_id = None

# --- 数据展示与筛选 ---
if not st.session_state.transactions_df.empty:
    df = st.session_state.transactions_df.copy()
    type_mapping = {"CREDIT": "收入", "DEBIT": "支出"}
    df["type_cn"] = df["transaction_type"].map(type_mapping)

    st.markdown("---")
    st.subheader("🗓️ 交易概览与筛选")

    with st.expander("点击展开筛选器", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            min_date, max_date = (
                df["transaction_date"].min().date(),
                df["transaction_date"].max().date(),
            )
            date_range = st.date_input(
                "选择日期范围",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
        with col2:
            selected_types_cn = st.multiselect(
                "交易类型",
                options=df["type_cn"].unique(),
                default=df["type_cn"].unique(),
            )
        with col3:
            search_term = st.text_input(
                "摘要或对手方关键字", placeholder="例如：星巴克、工资、快捷支付..."
            )

    # 应用筛选
    if len(date_range) == 2:
        start_date, end_date = date_range
        df = df[
            (df["transaction_date"].dt.date >= start_date)
            & (df["transaction_date"].dt.date <= end_date)
        ]
    if selected_types_cn:
        df = df[df["type_cn"].isin(selected_types_cn)]

    # --- 【核心修改点 1】: 增强关键字搜索 ---
    if search_term:
        # 在多个列中进行搜索，并处理None值
        search_mask = (
            df["description"].str.contains(search_term, case=False, na=False)
            | df["counterparty_name"].str.contains(search_term, case=False, na=False)
            | df["transaction_method"].str.contains(search_term, case=False, na=False)
            | df["location"].str.contains(search_term, case=False, na=False)
            | df["branch_name"].str.contains(search_term, case=False, na=False)
        )
        df = df[search_mask]

    filtered_df = df

    st.markdown("#### 📊 关键指标")
    total_income = filtered_df[filtered_df["transaction_type"] == "CREDIT"][
        "amount"
    ].sum()
    total_expense = filtered_df[filtered_df["transaction_type"] == "DEBIT"][
        "amount"
    ].sum()
    net_flow = total_income + total_expense
    net_outflow = abs(net_flow) if net_flow < 0 else 0.0

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric(label="🔼 总收入", value=f"¥ {total_income:,.2f}")
    kpi2.metric(label="🔽 总支出", value=f"¥ {abs(total_expense):,.2f}")
    kpi3.metric(label="↔️ 净流入", value=f"¥ {net_flow:,.2f}")
    kpi4.metric(label="📉 净流出", value=f"¥ {net_outflow:,.2f}")
    kpi5.metric(label="🔢 总交易笔数", value=f"{len(filtered_df)}")

    st.markdown("#### 📈 可视化分析")
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.write("**支出对手方 Top 5**")
        if not filtered_df[filtered_df["transaction_type"] == "DEBIT"].empty:
            expense_by_counterparty = (
                filtered_df[filtered_df["transaction_type"] == "DEBIT"]
                .groupby("counterparty_name")["amount"]
                .sum()
                .abs()
                .sort_values(ascending=False)
                .head(5)
            )
            bar_chart = (
                alt.Chart(expense_by_counterparty.reset_index())
                .mark_bar()
                .encode(
                    x=alt.X("counterparty_name", sort="-y", title="对手方"),
                    y=alt.Y("amount", title="支出金额 (元)"),
                    tooltip=["counterparty_name", "amount"],
                )
                .configure_axisX(labelAngle=0)
            )
            st.altair_chart(bar_chart, use_container_width=True)
        else:
            st.info("当前筛选范围内无支出数据。")

    with chart_col2:
        st.write("**收入/支出构成**")
        if not filtered_df.empty:
            type_summary = filtered_df.groupby("type_cn")["amount"].sum().abs()
            donut_chart = (
                alt.Chart(type_summary.reset_index())
                .mark_arc(innerRadius=50)
                .encode(
                    theta=alt.Theta(field="amount", type="quantitative"),
                    color=alt.Color(
                        field="type_cn",
                        type="nominal",
                        scale=alt.Scale(
                            domain=["收入", "支出"], range=["#2ca02c", "#d62728"]
                        ),
                        title="类型",
                    ),
                    tooltip=["type_cn", "amount"],
                )
            )
            st.altair_chart(donut_chart, use_container_width=True)
        else:
            st.info("当前筛选范围内无交易数据。")

    st.markdown("#### 📋 交易明细")

    # --- 【核心修改点 2】: 定义要导出和显示的列 ---
    display_columns = [
        "transaction_date",
        "description",
        "counterparty_name",
        "amount",
        "type_cn",
        "balance_after_txn",
        "currency",
        "transaction_method",
        "is_cash",
        "location",
        "branch_name",
        "bank_transaction_id",
        "category",
    ]

    csv = convert_df_to_csv(filtered_df[display_columns])
    st.download_button(
        label="📥 下载筛选结果为 CSV",
        data=csv,
        file_name=f"{selected_account_name}_transactions.csv",
        mime="text/csv",
    )

    # --- 【核心修改点 3】: 更新表格的列和配置 ---
    st.dataframe(
        filtered_df[display_columns],
        column_config={
            "transaction_date": st.column_config.DatetimeColumn(
                "交易时间 (北京)", format="YYYY-MM-DD HH:mm:ss"
            ),
            "description": "交易摘要",
            "counterparty_name": "对手方",
            "amount": st.column_config.NumberColumn("金额", format="¥ %.2f"),
            "type_cn": "类型",
            "balance_after_txn": st.column_config.NumberColumn(
                "交易后余额", format="¥ %.2f"
            ),
            "currency": "币种",
            "transaction_method": "交易渠道",
            "is_cash": "是否现金",
            "location": "交易地点",
            "branch_name": "交易网点",
            "bank_transaction_id": "银行流水号",
            "category": "交易分类",
        },
        use_container_width=True,
        hide_index=True,
        height=600,
    )

elif selected_person_name and st.session_state.get("selectbox_account"):
    st.info("该账户下没有找到任何交易数据。")
