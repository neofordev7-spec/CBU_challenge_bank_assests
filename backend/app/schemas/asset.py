from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel

from app.schemas.category import CategoryResponse
from app.schemas.employee import EmployeeResponse
from app.schemas.department import DepartmentResponse
from app.schemas.branch import BranchResponse


class AssetBase(BaseModel):
    name: str
    serial_number: str
    category_id: int
    description: str | None = None
    purchase_date: date | None = None
    purchase_price: Decimal | None = None
    warranty_expiry: date | None = None
    notes: str | None = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: str | None = None
    serial_number: str | None = None
    category_id: int | None = None
    description: str | None = None
    purchase_date: date | None = None
    purchase_price: Decimal | None = None
    warranty_expiry: date | None = None
    notes: str | None = None


class AssetStatusUpdate(BaseModel):
    status: str
    reason: str


class AssetResponse(AssetBase):
    id: int
    inventory_number: str
    status: str
    photo_path: str | None = None
    qr_code_path: str | None = None
    current_employee_id: int | None = None
    current_department_id: int | None = None
    current_branch_id: int | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetDetail(AssetResponse):
    category: CategoryResponse | None = None
    current_employee: EmployeeResponse | None = None
    current_department: DepartmentResponse | None = None
    current_branch: BranchResponse | None = None
    current_value: Decimal | None = None


class AssetListResponse(BaseModel):
    items: list[AssetDetail]
    total: int
    page: int
    page_size: int
    pages: int
