# app/tasks/utils/parser_service.py
from pathlib import Path

import pandas as pd
import numpy as np
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import CounterpartyType
from app.repository.counterparty import counterparty_repository
from app.repository.transaction import transaction_repository


class ParserService:
    """
    封装了从文件解析、清洗数据到存入数据库的完整业务逻辑。
    这个版本经过优化，可以处理来自四大行（工、建、农、中）的不同流水格式。
    """

    def __init__(self):
        # 核心：构建兼容四大行的统一列名映射
        self.COLUMN_MAPPING = {
            # 标准化目标字段 -> 可能的原始列名列表
            # 注意：日期和时间相关的列将进行特殊处理，这里仅作参考
            "transaction_date_str": ["交易时间", "交易日期"],
            "transaction_time_str": ["交易时间"],
            "amount_in": ["收入金额", "收入金额(元)"],
            "amount_out": ["支出金额", "支出金额(元)"],
            "amount_single": ["交易金额"],
            "transaction_type_flag": ["借贷标志", "借贷"],
            "currency": ["币种"],
            "balance_after_txn": ["交易余额", "账户余额"],
            "description": ["交易摘要", "摘要", "交易说明", "交易附言"],
            "bank_transaction_id": ["交易流水号", "凭证号"],
            "counterparty_name": [
                "交易对方名称",
                "对方户名",
                "对方名称",
                "对方账户名称",
            ],
            "counterparty_account_number": ["交易对方账号", "对方账号", "对方账户账号"],
            "merchant_name": ["商户名称"],
            "transaction_method": ["交易类型", "交易渠道", "交易方式"],
            "is_cash_flag": ["现金标志"],
            "location": ["交易发生地"],
            "branch_name": ["交易网点名称", "交易机构"],
        }

        # 对手类型关键词
        self.MERCHANT_KEYWORDS = [
            "公司",
            "机构",
            "科技",
            "网络",
            "支付",
            "技术",
            "银行",
            "物业",
            "管理",
            "财付通",
            "支付宝",
            "银联",
            "唯品会",
            "钱袋宝",
            "微众",
            "抖音",
            "电商",
            "商户",
            "平台",
            "快递",
            "服饰",
            "股份",
            "商业",
            "便购",
            "餐饮",
        ]

    def _read_file_to_dataframe(self, file_path: str) -> pd.DataFrame:
        """
        读取一个Excel或CSV文件，转换为 Pandas.DataFrame
        """
        path = Path(file_path)
        logger.info(f"开始读取文件: {path}")
        if path.suffix in [".xlsx", ".xls"]:
            return pd.read_excel(path, header=0, dtype=str)
        elif path.suffix == ".csv":
            return pd.read_csv(path, header=0, dtype=str)
        else:
            raise ValueError(f"不支持的文件类型: {path.suffix}")

    def _normalize_counterparty_name(self, name: str | None) -> str:
        """
        标准化交易对手方的名称 (当前为直通模式，保留原始名称以便测试)
        """
        # 1. 保留入口处的安全检查，增加对纯空格字符串的判断
        if not name or not isinstance(name, str) or not name.strip():
            return "未知对手"

        # 2. 暂时不进行任何替换或标准化操作，直接返回原始名称
        return name

    def _classify_counterparty(self, name: str) -> CounterpartyType:
        """根据名称中的关键词，使用启发式规则对对手方进行分类 (草鸡版)"""
        # 将名称转为小写并去除空格，以提高匹配成功率
        normalized_name = name.lower().strip()

        if not normalized_name or normalized_name == "未知对手":
            return CounterpartyType.UNKNOWN

        # 1. 优先根据关键词判断
        for keyword in self.MERCHANT_KEYWORDS:
            if keyword.lower() in normalized_name:
                if any(p in normalized_name for p in ["支付", "财付通", "支付宝"]):
                    return CounterpartyType.PAYMENT_PLATFORM
                if "银行" in normalized_name or "银联" in normalized_name:
                    return CounterpartyType.BANK
                return CounterpartyType.MERCHANT

        # 2. 长度启发式规则
        if len(normalized_name) > 7:
            return CounterpartyType.MERCHANT

        # 3. 默认是个人
        return CounterpartyType.PERSON

    def _determine_is_cash(self, row: pd.Series) -> bool:
        """
        用于判断单笔交易是否为现金交易。
        它会检查多个列来寻找线索，并能正确处理None值。
        """

        # 规则1：检查“现金标志”列
        cash_flag = row.get("is_cash_flag")  # 直接获取值，可能是字符串或None
        if isinstance(cash_flag, str) and cash_flag.strip() == "现金交易":
            logger.trace(
                f"Row {row.name}: 通过'现金标志'列找到现金交易 ('{cash_flag}')"
            )
            return True

        # 规则2：检查“交易摘要”列
        description = row.get("description")
        if isinstance(description, str) and (
            "现金存入" in description or "现金支取" in description
        ):
            logger.trace(
                f"Row {row.name}: 通过'交易摘要'列找到现金交易 ('{description}')"
            )
            return True

        # 规则3：检查“交易类型/渠道”列
        method = row.get("transaction_method")
        if isinstance(method, str) and ("现金存款" in method or "现金取款" in method):
            logger.trace(f"Row {row.name}: 通过'交易方式'列找到现金交易 ('{method}')")
            return True

        # 如果以上所有规则都不满足，则默认为非现金交易
        return False

    def _clean_and_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗和转换从 Excel/CSV 文件中解析得到的数据，以便后续入库。
        【V3版核心重构】
        """
        logger.info("开始清洗和转换数据...")

        # 创建一个新的干净的DataFrame，用于存放标准化后的数据
        cleaned_df = pd.DataFrame(index=df.index)

        # 步骤 1: 智能处理日期和时间列的歧义
        if "交易日期" in df.columns and "交易时间" in df.columns:
            logger.info("检测到'交易日期'和'交易时间'分离模式 (例如 中行)。")
            cleaned_df["transaction_date_str"] = df["交易日期"]
            cleaned_df["transaction_time_str"] = df["交易时间"]
        else:
            logger.info(
                "未检测到日期、时间分离列，将尝试寻找单个日期时间列 (例如 工行)。"
            )
            # 在工行模式下，“交易时间”就是我们需要的完整日期时间字符串
            date_col_source = next(
                (
                    col
                    for col in self.COLUMN_MAPPING["transaction_date_str"]
                    if col in df.columns
                ),
                None,
            )
            if date_col_source:
                cleaned_df["transaction_date_str"] = df[date_col_source]
            else:
                cleaned_df["transaction_date_str"] = None
            cleaned_df["transaction_time_str"] = None  # 确保此模式下时间列为空

        # 步骤 2: 复制其余明确的列
        for std_name, raw_names_list in self.COLUMN_MAPPING.items():
            # 跳过已特殊处理的日期/时间列
            if std_name in ["transaction_date_str", "transaction_time_str"]:
                continue

            source_col_name = next(
                (raw_name for raw_name in raw_names_list if raw_name in df.columns),
                None,
            )
            if source_col_name:
                cleaned_df[std_name] = df[source_col_name]
            else:
                cleaned_df[std_name] = None

        logger.info("列名标准化和数据复制完成。")

        # 步骤 3: 解析日期时间
        if pd.notna(cleaned_df["transaction_date_str"]).any():
            # 模式一：日期+时间分离 (中行)
            if pd.notna(cleaned_df["transaction_time_str"]).any():
                logger.info("正在使用“日期+时间分离”模式解析时间...")
                time_str = pd.to_datetime(
                    cleaned_df["transaction_time_str"], errors="coerce"
                ).dt.strftime("%H:%M:%S")
                full_datetime_str = cleaned_df["transaction_date_str"] + " " + time_str
                cleaned_df["transaction_date"] = pd.to_datetime(
                    full_datetime_str, errors="coerce"
                )
            # 模式二：日期时间合一 (工行、交行等)
            else:
                logger.info("正在使用“日期时间合一”模式解析时间（兼容多种格式）...")
                # --- 对日期字符串进行预处理 ---
                # 1. 移除所有可能的冒号、空格，并去除首尾空白
                date_series = (
                    cleaned_df["transaction_date_str"]
                    .str.replace(":", "", regex=False)
                    .str.replace(" ", "", regex=False)
                    .str.strip()
                )
                # 2. 对齐长度：对于缺少秒的格式 (如 YYYYMMDDHHMM)，在末尾补 '00'，使其统一为14位
                date_series_padded = date_series.str.ljust(14, "0")
                # 3. 现在所有格式都统一了，再使用严格格式进行解析
                cleaned_df["transaction_date"] = pd.to_datetime(
                    date_series_padded,
                    format="%Y%m%d%H%M%S",
                    errors="coerce",
                )
        else:
            logger.warning(
                "在文件中未找到可识别的交易日期列，'transaction_date' 将为空。"
            )
            cleaned_df["transaction_date"] = pd.NaT

        cleaned_df["transaction_date"] = (
            cleaned_df["transaction_date"]
            .dt.tz_localize("Asia/Shanghai", ambiguous="infer")
            .dt.tz_convert("UTC")
        )

        # 步骤 4: 健壮的金额模式检测
        temp_in = pd.to_numeric(cleaned_df["amount_in"], errors="coerce").fillna(0)
        temp_out = pd.to_numeric(cleaned_df["amount_out"], errors="coerce").fillna(0)
        temp_single = pd.to_numeric(
            cleaned_df["amount_single"], errors="coerce"
        ).fillna(0)

        is_separate_mode = (temp_in != 0).any() or (temp_out != 0).any()
        is_single_mode = (temp_single != 0).any() and pd.notna(
            cleaned_df["transaction_type_flag"]
        ).any()

        if is_separate_mode:
            logger.info("检测到“收支分离列”模式 (基于有效数据)。")
            cleaned_df["amount"] = temp_in - temp_out
            cleaned_df["transaction_type"] = cleaned_df["amount"].apply(
                lambda x: "CREDIT" if x >= 0 else "DEBIT"
            )
        elif is_single_mode:
            logger.info("检测到“单金额列 + 借贷标志”模式 (基于有效数据)。")
            cleaned_df["amount"] = temp_single
            cleaned_df["transaction_type"] = cleaned_df["transaction_type_flag"].apply(
                lambda x: "CREDIT" if str(x) in ["进", "贷", "Credit"] else "DEBIT"
            )
            cleaned_df["amount"] = cleaned_df.apply(
                lambda row: abs(row["amount"])
                if row["transaction_type"] == "CREDIT"
                else -abs(row["amount"]),
                axis=1,
            )
        else:
            logger.warning("无法识别有效的金额记录模式！将创建空金额列。")
            cleaned_df["amount"] = 0.0
            cleaned_df["transaction_type"] = "UNKNOWN"

        # 步骤 5: 其余字段清洗
        cleaned_df["currency"] = cleaned_df["currency"].fillna("CNY")
        cleaned_df["balance_after_txn"] = pd.to_numeric(
            cleaned_df["balance_after_txn"], errors="coerce"
        )
        logger.info("正在通过多列分析来判断现金交易...")
        cleaned_df["is_cash"] = cleaned_df.apply(self._determine_is_cash, axis=1)
        cleaned_df["counterparty_name"] = cleaned_df["counterparty_name"].fillna(
            cleaned_df.get("merchant_name")
        )
        cleaned_df["description"] = cleaned_df["description"].fillna("无摘要信息")

        # 过滤掉没有有效交易日期的行
        original_rows = len(cleaned_df)
        cleaned_df.dropna(subset=["transaction_date"], inplace=True)
        if original_rows > len(cleaned_df):
            logger.warning(
                f"过滤掉了 {original_rows - len(cleaned_df)} 行无效数据（缺少有效交易日期）。"
            )

        # 将Pandas的空值统一替换为Python的None
        cleaned_df = cleaned_df.replace(
            {np.nan: None, pd.NaT: None, "nan": None, "": None}
        )

        logger.success("数据清洗和转换完成。")
        return cleaned_df

    async def process_and_save_transactions(
        self, session: AsyncSession, file_path: str, account_id: int
    ):
        try:
            raw_df = self._read_file_to_dataframe(file_path)
            cleaned_df = self._clean_and_transform(raw_df)

            if cleaned_df.empty:
                logger.warning("清洗后没有有效的交易数据可供处理。")
                return {"processed_rows": 0}

            transactions_to_create = []
            for _, row in cleaned_df.iterrows():
                normalized_name = self._normalize_counterparty_name(
                    row.get("counterparty_name")
                )

                counterparty_type = self._classify_counterparty(normalized_name)

                counterparty = await counterparty_repository.get_or_create(
                    session,
                    name=normalized_name,
                    account_number=row.get("counterparty_account_number"),
                    counterparty_type=counterparty_type.value,
                )

                transaction_data = {
                    "transaction_date": row.get("transaction_date"),
                    "amount": row.get("amount"),
                    "currency": row.get("currency", "CNY"),
                    "transaction_type": row.get("transaction_type"),
                    "balance_after_txn": row.get("balance_after_txn"),
                    "description": row.get("description"),
                    "transaction_method": row.get("transaction_method"),
                    "bank_transaction_id": row.get("bank_transaction_id"),
                    "is_cash": row.get("is_cash", False),
                    "location": row.get("location"),
                    "branch_name": row.get("branch_name"),
                    "category": None,
                    "account_id": account_id,
                    "counterparty_id": counterparty.id,
                }
                transactions_to_create.append(transaction_data)

            if transactions_to_create:
                logger.info(f"准备批量插入 {len(transactions_to_create)} 条交易数据...")
                await transaction_repository.bulk_create(
                    session, transactions_data=transactions_to_create
                )
                logger.success("交易数据批量插入成功！")
            else:
                logger.warning("没有可供插入的交易数据。")

            return {"processed_rows": len(cleaned_df)}
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时发生严重错误: {e}", exc_info=True)
            raise


parser_service = ParserService()
