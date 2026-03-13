from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.asset import Asset
from app.models.category import AssetCategory
from app.models.department import Department
from app.models.branch import Branch
from app.core.enums import AssetStatus


def get_overview(db: Session) -> dict:
    total = db.query(func.count(Asset.id)).scalar() or 0

    status_counts = {}
    for s in AssetStatus:
        count = db.query(func.count(Asset.id)).filter(Asset.status == s.value).scalar() or 0
        status_counts[s.value.lower()] = count

    total_value = db.query(func.sum(Asset.purchase_price)).scalar() or Decimal("0")

    expiring_date = date.today() + timedelta(days=30)
    expiring = (
        db.query(func.count(Asset.id))
        .filter(
            Asset.warranty_expiry.isnot(None),
            Asset.warranty_expiry <= expiring_date,
            Asset.warranty_expiry >= date.today(),
            Asset.status != AssetStatus.WRITTEN_OFF,
        )
        .scalar()
        or 0
    )

    return {
        "total_assets": total,
        "registered": status_counts.get("registered", 0),
        "assigned": status_counts.get("assigned", 0),
        "in_repair": status_counts.get("in_repair", 0),
        "lost": status_counts.get("lost", 0),
        "written_off": status_counts.get("written_off", 0),
        "total_value": total_value,
        "expiring_warranty_count": expiring,
    }


def get_by_category(db: Session) -> list[dict]:
    results = (
        db.query(
            AssetCategory.id,
            AssetCategory.name,
            func.count(Asset.id).label("count"),
        )
        .join(Asset, Asset.category_id == AssetCategory.id)
        .group_by(AssetCategory.id, AssetCategory.name)
        .all()
    )
    return [{"category_id": r[0], "category_name": r[1], "count": r[2]} for r in results]


def get_by_status(db: Session) -> list[dict]:
    results = (
        db.query(Asset.status, func.count(Asset.id).label("count"))
        .group_by(Asset.status)
        .all()
    )
    return [{"status": r[0], "count": r[1]} for r in results]


def get_by_department(db: Session) -> list[dict]:
    results = (
        db.query(
            Department.id,
            Department.name,
            func.count(Asset.id).label("count"),
        )
        .join(Asset, Asset.current_department_id == Department.id)
        .group_by(Department.id, Department.name)
        .all()
    )
    return [{"department_id": r[0], "department_name": r[1], "count": r[2]} for r in results]


def get_by_branch(db: Session) -> list[dict]:
    results = (
        db.query(
            Branch.id,
            Branch.name,
            func.count(Asset.id).label("count"),
        )
        .join(Asset, Asset.current_branch_id == Branch.id)
        .group_by(Branch.id, Branch.name)
        .all()
    )
    return [{"branch_id": r[0], "branch_name": r[1], "count": r[2]} for r in results]


def get_aging_assets(db: Session) -> list[dict]:
    assets = (
        db.query(Asset)
        .join(AssetCategory, Asset.category_id == AssetCategory.id)
        .filter(
            Asset.purchase_date.isnot(None),
            Asset.status != AssetStatus.WRITTEN_OFF,
        )
        .all()
    )
    result = []
    for a in assets:
        age_months = (date.today().year - a.purchase_date.year) * 12 + (date.today().month - a.purchase_date.month)
        useful_life = a.category.useful_life_months if (a.category and a.category.useful_life_months) else 60
        if age_months >= useful_life:
            result.append({
                "id": a.id,
                "name": a.name,
                "inventory_number": a.inventory_number,
                "category_name": a.category.name if a.category else "",
                "purchase_date": str(a.purchase_date) if a.purchase_date else None,
                "warranty_expiry": str(a.warranty_expiry) if a.warranty_expiry else None,
                "age_months": age_months,
                "useful_life_months": useful_life,
                "status": a.status,
            })
    return result


def get_warranty_expiring(db: Session, days: int = 30) -> list[dict]:
    expiring_date = date.today() + timedelta(days=days)
    assets = (
        db.query(Asset)
        .filter(
            Asset.warranty_expiry.isnot(None),
            Asset.warranty_expiry <= expiring_date,
            Asset.warranty_expiry >= date.today(),
            Asset.status != AssetStatus.WRITTEN_OFF,
        )
        .all()
    )
    return [
        {
            "id": a.id,
            "name": a.name,
            "inventory_number": a.inventory_number,
            "warranty_expiry": str(a.warranty_expiry),
            "status": a.status,
            "days_remaining": (a.warranty_expiry - date.today()).days,
        }
        for a in assets
    ]
