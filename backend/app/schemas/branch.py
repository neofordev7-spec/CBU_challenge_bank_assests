from datetime import datetime
from pydantic import BaseModel


class BranchBase(BaseModel):
    name: str
    code: str
    address: str | None = None


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    address: str | None = None
    is_active: bool | None = None


class BranchResponse(BranchBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
