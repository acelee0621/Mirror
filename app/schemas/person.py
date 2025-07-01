# app/schemas/person.py
from pydantic import ConfigDict, Field

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
    id: int
    full_name: str
    id_type: str | None = None
    id_number: str | None = None
    model_config = ConfigDict(from_attributes=True)


class PersonWithAccounts(PersonPublic):
    """
    用于返回单个用户详细信息的模型。
    """

    # 它引用的是不包含owner的AccountPublic
    accounts: list[AccountPublic] = []
