# app/services/rule_based_analysis.py
import pandas as pd
from datetime import timedelta
from typing import Any


def find_u_turn_transactions(
    transactions_df: pd.DataFrame,
    amount_threshold: float = 10000.0,
    time_window_hours: int = 72,
    amount_tolerance: float = 0.10,
) -> list[dict[str, Any]]:
    """
    在交易数据中识别“快进快出”（U-Turn）模式。

    """
    df = transactions_df.sort_values("transaction_date").copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["amount", "id"])  # 确保 id 列存在且不为空

    large_inflows = df[
        (df["transaction_type"] == "CREDIT") & (df["amount"] >= amount_threshold)
    ]
    large_outflows = df[
        (df["transaction_type"] == "DEBIT")
        & (df["amount"].abs() >= amount_threshold * (1 - amount_tolerance))
    ]

    found_events = []
    used_outflow_indices = set()

    for _, inflow_row in large_inflows.iterrows():
        inflow_time = inflow_row["transaction_date"]
        inflow_amount = inflow_row["amount"]

        window_end = inflow_time + timedelta(hours=time_window_hours)

        candidate_outflows = large_outflows[
            (large_outflows["transaction_date"] > inflow_time)
            & (large_outflows["transaction_date"] <= window_end)
            & (~large_outflows.index.isin(used_outflow_indices))
        ]

        if candidate_outflows.empty:
            continue

        candidate_outflows = candidate_outflows.sort_values("amount", ascending=True)

        matched_outflows_rows = []
        current_outflow_sum = 0.0

        for _, outflow_row in candidate_outflows.iterrows():
            matched_outflows_rows.append(outflow_row)
            current_outflow_sum += abs(outflow_row["amount"])

            lower_bound = inflow_amount * (1 - amount_tolerance)
            upper_bound = inflow_amount * (1 + amount_tolerance)

            if lower_bound <= current_outflow_sum <= upper_bound:
                event = {
                    "inflow_id": inflow_row["id"],
                    "outflow_ids": [o["id"] for o in matched_outflows_rows],
                    "total_outflow": current_outflow_sum,
                    "time_diff_hours": (
                        matched_outflows_rows[-1]["transaction_date"] - inflow_time
                    )
                    / timedelta(hours=1),
                }
                found_events.append(event)

                for o in matched_outflows_rows:
                    used_outflow_indices.add(o.name)

                break

    return found_events
