from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.asset import Asset
from app.models.assignment import AssetAssignment
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.schemas.asset import AssetDetail
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.dependencies import require_auth
from app.services import asset_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login yoki parol noto'g'ri",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Foydalanuvchi bloklangan")

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/register", response_model=UserResponse)
def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu username allaqachon mavjud")

    user = User(
        username=data.username,
        full_name=data.full_name,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(require_auth)):
    return UserResponse.model_validate(current_user)


@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    users = db.query(User).all()
    return [UserResponse.model_validate(u) for u in users]


@router.get("/my-assets")
def my_assets(db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    """USER roli uchun — o'ziga biriktirilgan aktivlar"""
    if not current_user.employee_id:
        return {"current_assets": [], "history": []}

    # Hozir biriktirilgan aktivlar
    current_assets = (
        db.query(Asset)
        .filter(Asset.current_employee_id == current_user.employee_id)
        .all()
    )
    current_list = []
    for a in current_assets:
        detail = AssetDetail.model_validate(a)
        detail.current_value = asset_service.calculate_current_value(a, a.category)
        current_list.append(detail)

    # Biriktirish tarixi (barcha — hozirgi va qaytarilganlar)
    history = (
        db.query(AssetAssignment)
        .filter(AssetAssignment.employee_id == current_user.employee_id)
        .order_by(AssetAssignment.assigned_at.desc())
        .all()
    )
    history_list = []
    for h in history:
        history_list.append({
            "id": h.id,
            "asset_id": h.asset_id,
            "asset_name": h.asset.name if h.asset else None,
            "asset_inventory_number": h.asset.inventory_number if h.asset else None,
            "asset_status": h.asset.status if h.asset else None,
            "assigned_at": h.assigned_at.isoformat() if h.assigned_at else None,
            "returned_at": h.returned_at.isoformat() if h.returned_at else None,
            "return_reason": h.return_reason,
            "department_name": h.department.name if h.department else None,
        })

    return {"current_assets": current_list, "history": history_list}
