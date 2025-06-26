from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession

class BaseRepository(ABC):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @abstractmethod
    async def create(self, obj_in): ...
    @abstractmethod  
    async def get(self, id: int): ...
    @abstractmethod
    async def update(self, id: int, obj_in): ...
    @abstractmethod
    async def delete(self, id: int): ...