from datetime import datetime, date
from decimal import Decimal
import math

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.asset import Asset
from app.models.category import AssetCategory
from app.core.enums import AssetStatus, ALLOWED_TRANSITIONS
from app.core.exceptions import NotFoundException, BadRequestException
from app.services import audit_service
from app.services.qrcode_service import generate_qr


def generate_inventory_number(db: Session, category_code: str) -> str:
    year = datetime.utcnow().year
    prefix = f"BNK-{category_code}-{year}-"
    last_asset = (
        db.query(Asset)
        .filter(Asset.inventory_number.like(f"{prefix}%"))
        .order_by(Asset.id.desc())
        .first()
    )
    if last_asset:
        last_num = int(last_asset.inventory_number.split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    return f"{prefix}{next_num:04d}"


def calculate_current_value(asset: Asset, category: AssetCategory | None = None) -> Decimal | None:
    if not asset.purchase_price or not asset.purchase_date:
        return None
    useful_life = 60  # default 5 years
    if category and category.useful_life_months:
        useful_life = category.useful_life_months
    months_elapsed = (date.today().year - asset.purchase_date.year) * 12 + (
        date.today().month - asset.purchase_date.month
    )
    if months_elapsed <= 0:
        return asset.purchase_price
    if months_elapsed >= useful_life:
        return Decimal("0.00")
    depreciation = float(asset.purchase_price) / useful_life * months_elapsed
    current = float(asset.purchase_price) - depreciation
    return Decimal(str(max(0, round(current, 2))))


def get_assets(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    category_id: int | None = None,
    status: str | None = None,
    department_id: int | None = None,
    branch_id: int | None = None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    query = db.query(Asset)

    if category_id:
        query = query.filter(Asset.category_id == category_id)
    if status:
        query = query.filter(Asset.status == status)
    if department_id:
        query = query.filter(Asset.current_department_id == department_id)
    if branch_id:
        query = query.filter(Asset.current_branch_id == branch_id)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Asset.name.ilike(search_term),
                Asset.serial_number.ilike(search_term),
                Asset.inventory_number.ilike(search_term),
            )
        )

    total = query.count()

    sort_col = getattr(Asset, sort_by, Asset.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    pages = math.ceil(total / page_size) if page_size > 0 else 0

    return items, total, pages


def get_asset(db: Session, asset_id: int) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise NotFoundException("Aktiv topilmadi")
    return asset


def get_asset_by_inventory(db: Session, inventory_number: str) -> Asset:
    asset = db.query(Asset).filter(Asset.inventory_number == inventory_number).first()
    if not asset:
        raise NotFoundException("Aktiv topilmadi")
    return asset


def create_asset(db: Session, data: dict, user_id: int | None = None) -> Asset:
    category = db.query(AssetCategory).filter(AssetCategory.id == data["category_id"]).first()
    if not category:
        raise BadRequestException("Kategoriya topilmadi")

    # Serial number uniqueness tekshiruvi
    serial = data.get("serial_number")
    if serial:
        existing = db.query(Asset).filter(Asset.serial_number == serial).first()
        if existing:
            raise BadRequestException(
                f"Bu seriya raqami allaqachon mavjud: {serial} "
                f"(Aktiv: {existing.name}, Inventar: {existing.inventory_number})"
            )

    inventory_number = generate_inventory_number(db, category.code)

    asset = Asset(
        **data,
        inventory_number=inventory_number,
        status=AssetStatus.REGISTERED,
        created_by=user_id,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # QR kod avtomatik generatsiya
    try:
        qr_filename = generate_qr(inventory_number)
        asset.qr_code_path = qr_filename
        db.commit()
        db.refresh(asset)
    except Exception:
        pass  # QR xatosi aktiv yaratishni to'xtatmasin

    audit_service.log_action(
        db,
        action="CREATED",
        entity_type="asset",
        entity_id=asset.id,
        asset_id=asset.id,
        new_value={"name": asset.name, "serial_number": asset.serial_number, "inventory_number": inventory_number},
        description=f"Aktiv '{asset.name}' (SN: {asset.serial_number}) ro'yxatga olindi",
        performed_by=user_id,
    )

    return asset


def update_asset(db: Session, asset_id: int, data: dict, user_id: int | None = None) -> Asset:
    asset = get_asset(db, asset_id)
    old_values = {}
    new_values = {}

    for key, value in data.items():
        if value is not None and hasattr(asset, key):
            old_val = getattr(asset, key)
            if old_val != value:
                old_values[key] = str(old_val) if old_val is not None else None
                new_values[key] = str(value)
                setattr(asset, key, value)

    if new_values:
        asset.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(asset)

        audit_service.log_action(
            db,
            action="UPDATED",
            entity_type="asset",
            entity_id=asset.id,
            asset_id=asset.id,
            old_value=old_values,
            new_value=new_values,
            description=f"Aktiv '{asset.name}' tahrirlandi",
            performed_by=user_id,
        )

    return asset


def change_status(db: Session, asset_id: int, new_status: str, reason: str | None = None, user_id: int | None = None) -> Asset:
    asset = get_asset(db, asset_id)
    old_status = asset.status

    allowed = ALLOWED_TRANSITIONS.get(old_status, [])
    if new_status not in allowed:
        raise BadRequestException(
            f"'{old_status}' statusidan '{new_status}' ga o'tish mumkin emas. "
            f"Ruxsat etilgan: {', '.join(allowed) if allowed else 'hech qaysi'}"
        )

    asset.status = new_status
    asset.updated_at = datetime.utcnow()

    if new_status in [AssetStatus.REGISTERED, AssetStatus.WRITTEN_OFF, AssetStatus.LOST, AssetStatus.IN_REPAIR]:
        asset.current_employee_id = None
        asset.current_department_id = None
        asset.current_branch_id = None

    db.commit()
    db.refresh(asset)

    audit_service.log_action(
        db,
        action="STATUS_CHANGED",
        entity_type="asset",
        entity_id=asset.id,
        asset_id=asset.id,
        old_value={"status": old_status},
        new_value={"status": new_status, "reason": reason},
        description=f"Status o'zgardi: {old_status} → {new_status}" + (f" (Sabab: {reason})" if reason else ""),
        performed_by=user_id,
    )

    return asset


def delete_asset(db: Session, asset_id: int, user_id: int | None = None):
    asset = get_asset(db, asset_id)

    if asset.status == AssetStatus.WRITTEN_OFF:
        raise BadRequestException("Aktiv allaqachon hisobdan chiqarilgan")

    if asset.status == AssetStatus.ASSIGNED:
        raise BadRequestException("Biriktirilgan aktivni o'chirish mumkin emas. Avval qaytaring.")

    old_status = asset.status
    asset.status = AssetStatus.WRITTEN_OFF
    asset.current_employee_id = None
    asset.current_department_id = None
    asset.current_branch_id = None
    asset.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(asset)

    audit_service.log_action(
        db,
        action="WRITTEN_OFF",
        entity_type="asset",
        entity_id=asset.id,
        asset_id=asset.id,
        old_value={"status": old_status},
        new_value={"status": AssetStatus.WRITTEN_OFF},
        description=f"Aktiv '{asset.name}' hisobdan chiqarildi",
        performed_by=user_id,
    )
