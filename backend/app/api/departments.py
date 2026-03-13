from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentWithBranch
from app.core.exceptions import NotFoundException
from app.core.dependencies import require_auth

router = APIRouter(prefix="/api/departments", tags=["Departments"])


@router.get("/", response_model=list[DepartmentWithBranch])
def list_departments(
    branch_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    query = db.query(Department).filter(Department.is_active == True)
    if branch_id:
        query = query.filter(Department.branch_id == branch_id)
    return query.all()


@router.get("/{dept_id}", response_model=DepartmentWithBranch)
def get_department(dept_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise NotFoundException("Bo'lim topilmadi")
    return dept


@router.post("/", response_model=DepartmentWithBranch)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    dept = Department(**data.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.put("/{dept_id}", response_model=DepartmentWithBranch)
def update_department(dept_id: int, data: DepartmentUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise NotFoundException("Bo'lim topilmadi")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(dept, key, value)
    db.commit()
    db.refresh(dept)
    return dept


@router.delete("/{dept_id}")
def delete_department(dept_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise NotFoundException("Bo'lim topilmadi")
    dept.is_active = False
    db.commit()
    return {"detail": "O'chirildi"}
