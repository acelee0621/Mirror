# app/repository/person.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repository.base import BaseRepository
from app.models.person import Person
from app.schemas.person import PersonCreate, PersonUpdate


class PersonRepository(BaseRepository[Person, PersonCreate, PersonUpdate]):
    """
    Person 模型的仓库层。
    """

    async def get_by_full_name(
        self, session: AsyncSession, *, full_name: str
    ) -> Person | None:
        statement = select(self.model).where(self.model.full_name == full_name)
        result = await session.scalars(statement)
        return result.one_or_none()

    async def get_with_accounts(
        self, session: AsyncSession, *, person_id: int
    ) -> Person | None:
        """
        根据ID获取一个Person，并预先加载其所有关联的Account。
        """
        statement = (
            select(self.model)
            .where(self.model.id == person_id)
            .options(selectinload(self.model.accounts))
        )
        result = await session.scalars(statement)
        return result.one_or_none()


# 创建仓库的单例
person_repository = PersonRepository(Person)
