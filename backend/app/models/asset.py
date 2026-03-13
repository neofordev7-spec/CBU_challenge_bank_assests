from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.core.enums import AssetStatus


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    inventory_number: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("asset_categories.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=AssetStatus.REGISTERED)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    purchase_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    warranty_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)

    photo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    qr_code_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    current_employee_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("employees.id"), nullable=True)
    current_department_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)
    current_branch_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("branches.id"), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("AssetCategory")
    current_employee = relationship("Employee", foreign_keys=[current_employee_id])
    current_department = relationship("Department", foreign_keys=[current_department_id])
    current_branch = relationship("Branch", foreign_keys=[current_branch_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
    assignments = relationship("AssetAssignment", back_populates="asset")
    audit_logs = relationship("AuditLog", back_populates="asset")
