from datetime import datetime
from pydantic import BaseModel

from app.schemas.employee import EmployeeResponse
from app.schemas.department import DepartmentResponse
from app.schemas.branch import BranchResponse


class AssignmentCreate(BaseModel):
    asset_id: int
    employee_id: int | None = None
    department_id: int | None = None
    branch_id: int | None = None
    notes: str | None = None


class AssignmentReturn(BaseModel):
    return_reason: str | None = None


class AssignmentResponse(BaseModel):
    id: int
    asset_id: int
    employee_id: int | None = None
    department_id: int
    branch_id: int
    assigned_at: datetime
    returned_at: datetime | None = None
    return_reason: str | None = None
    notes: str | None = None
    employee: EmployeeResponse | None = None
    department: DepartmentResponse | None = None
    branch: BranchResponse | None = None

    class Config:
        from_attributes = True
