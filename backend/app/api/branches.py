from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.branch import Branch
from app.models.user import User
from app.schemas.branch import BranchCreate, BranchUpdate, BranchResponse
from app.core.exceptions import NotFoundException
from app.core.dependencies import require_auth

router = APIRouter(prefix="/api/branches", tags=["Branches"])


@router.get("/", response_model=list[BranchResponse])
def list_branches(db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return db.query(Branch).filter(Branch.is_active == True).all()


@router.get("/{branch_id}", response_model=BranchResponse)
def get_branch(branch_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise NotFoundException("Filial topilmadi")
    return branch


@router.post("/", response_model=BranchResponse)
def create_branch(data: BranchCreate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    branch = Branch(**data.model_dump())
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


@router.put("/{branch_id}", response_model=BranchResponse)
def update_branch(branch_id: int, data: BranchUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise NotFoundException("Filial topilmadi")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(branch, key, value)
    db.commit()
    db.refresh(branch)
    return branch


@router.delete("/{branch_id}")
def delete_branch(branch_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise NotFoundException("Filial topilmadi")
    branch.is_active = False
    db.commit()
    return {"detail": "O'chirildi"}
