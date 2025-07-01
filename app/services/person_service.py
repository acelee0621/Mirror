# app/services/person_service.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.person import person_repository
from app.schemas.person import PersonCreate, PersonUpdate
from app.models.person import Person
from app.core.exceptions import NotFoundException, AlreadyExistsException


class PersonService:
    def __init__(self):
        self.repository = person_repository

    async def get_all_persons(
        self, session: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list[Person]:
        """获取所有Person记录（不包含账户详情，保持轻量）"""
        return await self.repository.get_multi(session, skip=skip, limit=limit)

    async def get_person_by_id(self, session: AsyncSession, person_id: int) -> Person:
        """通过ID获取一个Person，并包含其所有账户信息"""
        person = await self.repository.get_with_accounts(session, person_id=person_id)
        if not person:
            raise NotFoundException(detail=f"ID为 {person_id} 的用户不存在。")
        return person

    async def create_person(
        self, session: AsyncSession, *, person_in: PersonCreate
    ) -> Person:
        """创建一个新的Person"""
        existing_person = await self.repository.get_by_full_name(
            session, full_name=person_in.full_name
        )
        if existing_person:
            raise AlreadyExistsException(
                detail=f"用户 '{person_in.full_name}' 已存在。"
            )

        return await self.repository.create(session, obj_in=person_in)

    async def update_person(
        self, session: AsyncSession, *, person_id: int, person_in: PersonUpdate
    ) -> Person:
        """更新一个Person"""
        db_person = await self.get_person_by_id(session, person_id)
        updated_person = await self.repository.update(
            session, db_obj=db_person, obj_in=person_in
        )
        return await self.get_person_by_id(session, person_id=updated_person.id)

    async def delete_person(self, session: AsyncSession, *, person_id: int) -> None:
        """删除一个Person"""
        await self.get_person_by_id(session, person_id)
        await self.repository.delete(session, id=person_id)


# 创建服务层的单例
person_service = PersonService()
