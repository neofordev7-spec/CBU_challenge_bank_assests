from datetime import datetime
from pydantic import BaseModel

from app.schemas.department import DepartmentWithBranch


class EmployeeBase(BaseModel):
    full_name: str
    employee_code: str
    position: str | None = None
    department_id: int
    phone: str | None = None
    email: str | None = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    employee_code: str | None = None
    position: str | None = None
    department_id: int | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool | None = None


class EmployeeResponse(EmployeeBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeWithDepartment(EmployeeResponse):
    department: DepartmentWithBranch | None = None
