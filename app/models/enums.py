# app/models/enums.py
import enum

class CounterpartyType(str, enum.Enum):
    PERSON = "PERSON"          # 个人
    MERCHANT = "MERCHANT"      # 普通商户/公司
    PAYMENT_PLATFORM = "PAYMENT_PLATFORM"  # 支付平台 (如支付宝, 财付通)
    BANK = "BANK"              # 银行机构 (如同行转账, 利息)
    UNKNOWN = "UNKNOWN"        # 未知