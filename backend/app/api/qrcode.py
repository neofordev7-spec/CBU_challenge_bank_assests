from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services import qrcode_service, asset_service
from app.schemas.asset import AssetDetail
from app.core.dependencies import require_auth

router = APIRouter(prefix="/api", tags=["QR Code"])


@router.get("/assets/{asset_id}/qrcode")
def get_asset_qrcode(asset_id: int, db: Session = Depends(get_db)):
    asset = asset_service.get_asset(db, asset_id)
    qr_bytes = qrcode_service.get_qr_bytes(asset.inventory_number)
    return Response(content=qr_bytes, media_type="image/png")


@router.post("/assets/{asset_id}/qrcode")
def generate_asset_qrcode(asset_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    asset = asset_service.get_asset(db, asset_id)
    filename = qrcode_service.generate_qr(asset.inventory_number)
    asset.qr_code_path = filename
    db.commit()
    return {"filename": filename, "inventory_number": asset.inventory_number}


@router.get("/qr/lookup/{inventory_number}", response_model=AssetDetail)
def qr_lookup(inventory_number: str, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    asset = asset_service.get_asset_by_inventory(db, inventory_number)
    detail = AssetDetail.model_validate(asset)
    detail.current_value = asset_service.calculate_current_value(asset, asset.category)
    return detail
