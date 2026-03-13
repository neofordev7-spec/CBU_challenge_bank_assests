from datetime import datetime
from pydantic import BaseModel

from app.schemas.branch import BranchResponse


class DepartmentBase(BaseModel):
    name: str
    code: str
    branch_id: int


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    branch_id: int | None = None
    is_active: bool | None = None


class DepartmentResponse(DepartmentBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DepartmentWithBranch(DepartmentResponse):
    branch: BranchResponse | None = None
