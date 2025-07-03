# app/schemas/
from pydantic import BaseModel, ConfigDict


# ===================================================================
# 通用配置和基础类
# ===================================================================


class BaseSchema(BaseModel):
    # 配置Pydantic模型以兼容ORM对象
    model_config = ConfigDict(from_attributes=True)