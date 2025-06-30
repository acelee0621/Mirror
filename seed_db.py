import asyncio
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import setup_database_connection, shutdown_database_connection, get_session
from app.models.person import Person
from app.models.account import Account
from typing import Tuple

@asynccontextmanager
async def get_db_session():
    """
    数据库会话上下文管理器，自动处理会话的生命周期
    """
    session = await get_session()
    try:
        yield session
    finally:
        await session.close()

async def create_seed_data(session: AsyncSession) -> Tuple[Person, Account]:
    """
    在数据库中创建初始的 Person 和 Account 数据用于测试。
    
    Args:
        session: 数据库会话
        
    Returns:
        创建的Person和Account对象元组
    """
    print("\n=== 开始创建种子数据 ===")

    # 1. 创建或获取用户 (Person)
    person = await get_or_create_person(session)
    
    # 2. 创建或获取银行账户 (Account)
    account = await get_or_create_account(session, person.id)
    
    print("\n=== 种子数据准备就绪 ===")
    print(f"Person ID: {person.id} | Account ID: {account.id}")
    return person, account

async def get_or_create_person(session: AsyncSession) -> Person:
    """获取或创建Person记录"""
    existing_person = await session.get(Person, 1)
    if existing_person:
        print(f"ℹ️ 用户已存在: {existing_person.full_name} (ID: {existing_person.id})")
        return existing_person
    
    print("🔄 创建新用户...")
    person = Person(full_name="测试用户")
    session.add(person)
    await session.commit()
    await session.refresh(person)
    print(f"✅ 用户创建成功: {person.full_name} (ID: {person.id})")
    return person

async def get_or_create_account(session: AsyncSession, owner_id: int) -> Account:
    """获取或创建Account记录"""
    existing_account = await session.get(Account, 1)
    if existing_account:
        print(f"ℹ️ 账户已存在: {existing_account.account_name} (ID: {existing_account.id})")
        return existing_account
    
    print("🔄 为用户创建新账户...")
    account = Account(
        account_name="我的招行工资卡",
        account_number="622588******1234",
        account_type="储蓄卡",
        institution="招商银行",
        owner_id=owner_id,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    print(f"✅ 账户创建成功: {account.account_name} (ID: {account.id})")
    return account

async def main():
    """
    脚本主入口：初始化数据库，创建数据，然后关闭连接。
    """
    try:
        await setup_database_connection()
        async with get_db_session() as session:
            await create_seed_data(session)
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        raise
    finally:
        await shutdown_database_connection()
        print("\n数据库连接已关闭")

if __name__ == "__main__":
    asyncio.run(main())