from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeWithDepartment
from app.core.exceptions import NotFoundException
from app.core.dependencies import require_auth

router = APIRouter(prefix="/api/employees", tags=["Employees"])


@router.get("/", response_model=list[EmployeeWithDepartment])
def list_employees(
    department_id: int | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    query = db.query(Employee).filter(Employee.is_active == True)
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    if search:
        query = query.filter(Employee.full_name.ilike(f"%{search}%"))
    return query.all()


@router.get("/{emp_id}", response_model=EmployeeWithDepartment)
def get_employee(emp_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise NotFoundException("Xodim topilmadi")
    return emp


@router.post("/", response_model=EmployeeWithDepartment)
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    emp = Employee(**data.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@router.put("/{emp_id}", response_model=EmployeeWithDepartment)
def update_employee(emp_id: int, data: EmployeeUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise NotFoundException("Xodim topilmadi")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(emp, key, value)
    db.commit()
    db.refresh(emp)
    return emp


@router.delete("/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise NotFoundException("Xodim topilmadi")
    emp.is_active = False
    db.commit()
    return {"detail": "O'chirildi"}
