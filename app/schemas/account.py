# app/schemas/account.py
from pydantic import Field

from app.schemas.base import BaseSchema


# --- 基础模型 ---
class AccountBase(BaseSchema):
    """
    Account 模型的共用基础字段。
    """

    account_name: str | None = Field(None, max_length=100)
    account_number: str | None = Field(None, max_length=100)
    account_type: str | None = Field(None, max_length=50)
    institution: str | None = Field(None, max_length=100)


# --- 创建模型 ---
class AccountCreate(AccountBase):
    """
    创建 Account 时使用的模型。
    """

    account_name: str = Field(..., max_length=100)
    account_number: str = Field(..., max_length=100)


# --- 更新模型 ---
class AccountUpdate(AccountBase):
    """
    更新 Account 时使用的模型。所有字段都是可选的。
    """

    pass


# --- 公开模型（API返回）---
# 为了在返回账户信息时，能一并展示其所有者的基本信息，
# 我们先定义一个嵌套的Person模型。
class PersonInAccountPublic(BaseSchema):
    id: int
    full_name: str


class AccountPublic(AccountBase):
    """
    通过API返回给前端的公开模型。
    """

    id: int
    owner: PersonInAccountPublic  # 嵌套显示所有者信息
