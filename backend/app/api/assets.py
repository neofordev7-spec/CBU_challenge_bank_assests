from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.asset import (
    AssetCreate, AssetUpdate, AssetStatusUpdate,
    AssetDetail, AssetListResponse,
)
from app.services import asset_service
from app.core.dependencies import get_current_user, require_auth

router = APIRouter(prefix="/api/assets", tags=["Assets"])


@router.get("/", response_model=AssetListResponse)
def list_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: int | None = Query(None),
    status: str | None = Query(None),
    department_id: int | None = Query(None),
    branch_id: int | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    items, total, pages = asset_service.get_assets(
        db, page=page, page_size=page_size,
        category_id=category_id, status=status,
        department_id=department_id, branch_id=branch_id,
        search=search, sort_by=sort_by, sort_order=sort_order,
    )
    asset_details = []
    for item in items:
        detail = AssetDetail.model_validate(item)
        detail.current_value = asset_service.calculate_current_value(item, item.category)
        asset_details.append(detail)

    return AssetListResponse(
        items=asset_details, total=total, page=page, page_size=page_size, pages=pages,
    )


@router.get("/{asset_id}", response_model=AssetDetail)
def get_asset(asset_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    asset = asset_service.get_asset(db, asset_id)
    detail = AssetDetail.model_validate(asset)
    detail.current_value = asset_service.calculate_current_value(asset, asset.category)
    return detail


@router.post("/", response_model=AssetDetail)
def create_asset(
    data: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    asset = asset_service.create_asset(db, data.model_dump(), current_user.id)
    detail = AssetDetail.model_validate(asset)
    detail.current_value = asset_service.calculate_current_value(asset, asset.category)
    return detail


@router.put("/{asset_id}", response_model=AssetDetail)
def update_asset(
    asset_id: int,
    data: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    asset = asset_service.update_asset(db, asset_id, data.model_dump(exclude_unset=True), current_user.id)
    detail = AssetDetail.model_validate(asset)
    detail.current_value = asset_service.calculate_current_value(asset, asset.category)
    return detail


@router.patch("/{asset_id}/status", response_model=AssetDetail)
def change_status(
    asset_id: int,
    data: AssetStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    asset = asset_service.change_status(db, asset_id, data.status, data.reason, current_user.id)
    detail = AssetDetail.model_validate(asset)
    detail.current_value = asset_service.calculate_current_value(asset, asset.category)
    return detail


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    asset_service.delete_asset(db, asset_id, current_user.id)
    return {"detail": "O'chirildi"}
