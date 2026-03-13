from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentReturn, AssignmentResponse
from app.services import assignment_service
from app.core.dependencies import require_auth

router = APIRouter(prefix="/api/assignments", tags=["Assignments"])


@router.post("/", response_model=AssignmentResponse)
def assign_asset(
    data: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    assignment = assignment_service.assign_asset(
        db, data.asset_id, data.employee_id, data.department_id, data.branch_id,
        data.notes, current_user.id,
    )
    return AssignmentResponse.model_validate(assignment)


@router.post("/{assignment_id}/return", response_model=AssignmentResponse)
def return_asset(
    assignment_id: int,
    data: AssignmentReturn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    assignment = assignment_service.return_asset(
        db, assignment_id, data.return_reason, current_user.id,
    )
    return AssignmentResponse.model_validate(assignment)


@router.get("/asset/{asset_id}", response_model=list[AssignmentResponse])
def get_asset_assignments(asset_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return [
        AssignmentResponse.model_validate(a)
        for a in assignment_service.get_asset_assignments(db, asset_id)
    ]


@router.get("/employee/{employee_id}", response_model=list[AssignmentResponse])
def get_employee_assignments(employee_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_auth)):
    return [
        AssignmentResponse.model_validate(a)
        for a in assignment_service.get_employee_assignments(db, employee_id)
    ]
