# app/schemas/person.py
from pydantic import Field


# 导入我们之前为Account定义的公开Schema
from app.schemas.base import BaseSchema
from app.schemas.account import AccountPublic


class PersonBase(BaseSchema):
    full_name: str | None = Field(None, max_length=100)
    id_type: str | None = Field(None, max_length=50)
    id_number: str | None = Field(None, max_length=100)


class PersonCreate(PersonBase):
    full_name: str = Field(..., max_length=100)


class PersonUpdate(PersonBase):
    pass


class PersonPublic(BaseSchema):
    """
    用于返回“轻量级”用户信息的模型，比如在列表中。
    不包含关联的账户信息。
    """

    id: int
    full_name: str
    id_type: str | None = None
    id_number: str | None = None


class PersonWithAccounts(PersonPublic):
    """
    用于返回单个用户详细信息的模型。
    它继承了PersonPublic的所有字段，并增加了accounts列表。
    """

    # 关键点：定义一个AccountPublic的列表，并提供一个空列表作为默认值
    accounts: list[AccountPublic] = []
