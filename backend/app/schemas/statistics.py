from decimal import Decimal
from pydantic import BaseModel


class OverviewStats(BaseModel):
    total_assets: int
    registered: int
    assigned: int
    in_repair: int
    lost: int
    written_off: int
    total_value: Decimal
    expiring_warranty_count: int


class CategoryStat(BaseModel):
    category_id: int
    category_name: str
    count: int


class StatusStat(BaseModel):
    status: str
    count: int


class DepartmentStat(BaseModel):
    department_id: int
    department_name: str
    count: int


class BranchStat(BaseModel):
    branch_id: int
    branch_name: str
    count: int


class AgingAsset(BaseModel):
    id: int
    name: str
    inventory_number: str
    category_name: str
    purchase_date: str | None
    warranty_expiry: str | None
    age_months: int | None
    useful_life_months: int | None
    status: str
