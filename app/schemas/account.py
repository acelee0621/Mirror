# app/schemas/account.py
from pydantic import Field
from app.schemas.base import BaseSchema


# --- 基础模型 ---
class AccountBase(BaseSchema):
    account_name: str | None = Field(None, max_length=100)
    account_number: str | None = Field(None, max_length=100)
    account_type: str | None = Field(None, max_length=50)
    institution: str | None = Field(None, max_length=100)


# --- 创建模型 ---
class AccountCreate(AccountBase):
    account_name: str = Field(..., max_length=100)
    account_number: str = Field(..., max_length=100)


# --- 更新模型 ---
class AccountUpdate(AccountBase):
    pass


# --- 公开模型 ---
# 创建一个不包含owner的、轻量级的公开模型
# 它将被用于嵌套在Person的响应中
class AccountPublic(AccountBase):
    """
    用于嵌套在其他模型中的、轻量级的Account公开信息。
    """

    id: int


# 为了在返回账户信息时，能一并展示其所有者的基本信息，
# 我们先定义一个嵌套的Person模型。
class PersonInAccountPublic(BaseSchema):
    id: int
    full_name: str


# 创建一个包含owner的、完整的公开模型
# 它将被用于直接查询单个Account时返回
class AccountPublicWithOwner(AccountPublic):
    """
    用于直接返回单个Account时的完整公开信息，包含所有者。
    """

    owner: PersonInAccountPublic
