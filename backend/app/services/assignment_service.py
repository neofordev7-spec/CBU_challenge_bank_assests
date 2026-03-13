from datetime import datetime

from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.assignment import AssetAssignment
from app.models.employee import Employee
from app.models.department import Department
from app.models.branch import Branch
from app.core.enums import AssetStatus, ALLOWED_TRANSITIONS
from app.core.exceptions import NotFoundException, BadRequestException
from app.services import audit_service


def assign_asset(
    db: Session,
    asset_id: int,
    employee_id: int | None = None,
    department_id: int | None = None,
    branch_id: int | None = None,
    notes: str | None = None,
    user_id: int | None = None,
) -> AssetAssignment:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise NotFoundException("Aktiv topilmadi")

    if AssetStatus.ASSIGNED not in ALLOWED_TRANSITIONS.get(asset.status, []):
        raise BadRequestException(
            f"'{asset.status}' statusidagi aktivni biriktirish mumkin emas"
        )

    active_assignment = (
        db.query(AssetAssignment)
        .filter(AssetAssignment.asset_id == asset_id, AssetAssignment.returned_at.is_(None))
        .first()
    )
    if active_assignment:
        raise BadRequestException("Bu aktiv allaqachon biriktirilgan. Avval qaytaring.")

    if not employee_id and not department_id and not branch_id:
        raise BadRequestException("Xodim yoki bo'lim/filial ko'rsatilishi kerak")

    # Xodim orqali biriktirish
    if employee_id:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise NotFoundException("Xodim topilmadi")
        department = employee.department
        branch = department.branch if department else None

        assignment = AssetAssignment(
            asset_id=asset_id,
            employee_id=employee_id,
            department_id=department.id if department else 0,
            branch_id=branch.id if branch else 0,
            assigned_by=user_id,
            notes=notes,
        )
        db.add(assignment)

        asset.status = AssetStatus.ASSIGNED
        asset.current_employee_id = employee_id
        asset.current_department_id = department.id if department else None
        asset.current_branch_id = branch.id if branch else None
        asset.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(assignment)

        audit_service.log_action(
            db,
            action="ASSIGNED",
            entity_type="assignment",
            entity_id=assignment.id,
            asset_id=asset_id,
            new_value={
                "employee": employee.full_name,
                "department": department.name if department else None,
            },
            description=f"Aktiv '{asset.name}' xodim '{employee.full_name}' ga biriktirildi",
            performed_by=user_id,
        )

    # Bo'lim/filialga to'g'ridan-to'g'ri biriktirish
    else:
        department = None
        branch = None
        if department_id:
            department = db.query(Department).filter(Department.id == department_id).first()
            if not department:
                raise NotFoundException("Bo'lim topilmadi")
        if branch_id:
            branch = db.query(Branch).filter(Branch.id == branch_id).first()
            if not branch:
                raise NotFoundException("Filial topilmadi")
        # Agar faqat department berilsa, branch ni department dan olish
        if department and not branch and department.branch:
            branch = department.branch

        assignment = AssetAssignment(
            asset_id=asset_id,
            employee_id=None,
            department_id=department.id if department else 0,
            branch_id=branch.id if branch else 0,
            assigned_by=user_id,
            notes=notes,
        )
        db.add(assignment)

        asset.status = AssetStatus.ASSIGNED
        asset.current_employee_id = None
        asset.current_department_id = department.id if department else None
        asset.current_branch_id = branch.id if branch else None
        asset.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(assignment)

        target_name = department.name if department else (branch.name if branch else "")
        audit_service.log_action(
            db,
            action="ASSIGNED",
            entity_type="assignment",
            entity_id=assignment.id,
            asset_id=asset_id,
            new_value={
                "department": department.name if department else None,
                "branch": branch.name if branch else None,
            },
            description=f"Aktiv '{asset.name}' bo'lim/filial '{target_name}' ga biriktirildi",
            performed_by=user_id,
        )

    return assignment


def return_asset(
    db: Session,
    assignment_id: int,
    return_reason: str | None = None,
    user_id: int | None = None,
) -> AssetAssignment:
    assignment = db.query(AssetAssignment).filter(AssetAssignment.id == assignment_id).first()
    if not assignment:
        raise NotFoundException("Biriktirish topilmadi")
    if assignment.returned_at is not None:
        raise BadRequestException("Bu biriktirish allaqachon qaytarilgan")

    assignment.returned_at = datetime.utcnow()
    assignment.return_reason = return_reason

    asset = db.query(Asset).filter(Asset.id == assignment.asset_id).first()
    if asset:
        asset.status = AssetStatus.REGISTERED
        asset.current_employee_id = None
        asset.current_department_id = None
        asset.current_branch_id = None
        asset.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(assignment)

    employee = assignment.employee
    audit_service.log_action(
        db,
        action="RETURNED",
        entity_type="assignment",
        entity_id=assignment.id,
        asset_id=assignment.asset_id,
        old_value={"employee": employee.full_name if employee else None},
        new_value={"return_reason": return_reason},
        description=f"Aktiv '{asset.name if asset else ''}' xodim '{employee.full_name if employee else ''}' dan qaytarildi",
        performed_by=user_id,
    )

    return assignment


def get_asset_assignments(db: Session, asset_id: int) -> list[AssetAssignment]:
    return (
        db.query(AssetAssignment)
        .filter(AssetAssignment.asset_id == asset_id)
        .order_by(AssetAssignment.assigned_at.desc())
        .all()
    )


def get_employee_assignments(db: Session, employee_id: int) -> list[AssetAssignment]:
    return (
        db.query(AssetAssignment)
        .filter(AssetAssignment.employee_id == employee_id)
        .order_by(AssetAssignment.assigned_at.desc())
        .all()
    )
