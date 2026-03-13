from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.statistics import (
    OverviewStats, CategoryStat, StatusStat,
    DepartmentStat, BranchStat, AgingAsset,
)
from app.services import statistics_service
from app.core.dependencies import require_auth

router = APIRouter(prefix="/api/statistics", tags=["Statistics"])


@router.get("/overview", response_model=OverviewStats)
def get_overview(db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return statistics_service.get_overview(db)


@router.get("/by-category", response_model=list[CategoryStat])
def get_by_category(db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return statistics_service.get_by_category(db)


@router.get("/by-status", response_model=list[StatusStat])
def get_by_status(db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return statistics_service.get_by_status(db)


@router.get("/by-department", response_model=list[DepartmentStat])
def get_by_department(db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return statistics_service.get_by_department(db)


@router.get("/by-branch", response_model=list[BranchStat])
def get_by_branch(db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return statistics_service.get_by_branch(db)


@router.get("/aging", response_model=list[AgingAsset])
def get_aging_assets(db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return statistics_service.get_aging_assets(db)


@router.get("/warranty-expiring")
def get_warranty_expiring(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    return statistics_service.get_warranty_expiring(db, days)
