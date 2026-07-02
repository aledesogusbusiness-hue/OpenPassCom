import uuid
from datetime import datetime, date

from sqlalchemy import String, Boolean, DateTime, Date, Integer, UniqueConstraint, CheckConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, AuditMixin


class ClientEntity(AuditMixin, Base):
    __tablename__ = "client_entities"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ragione_sociale: Mapped[str] = mapped_column(String(255), nullable=False)
    codice_fiscale: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    partita_iva: Mapped[str | None] = mapped_column(String(11), nullable=True, unique=True, index=True)
    fiscal_regime: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ordinario"
    )  # ordinario | semplificato | forfettario
    periodicita_iva: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # mensile | trimestrale | None per forfettario
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    note: Mapped[str | None] = mapped_column(String(2000), nullable=True)


class FiscalYear(Base):
    __tablename__ = "fiscal_years"

    __table_args__ = (
        UniqueConstraint("client_entity_id", "anno", name="uq_fiscal_year_client_anno"),
        CheckConstraint("data_fine > data_inizio", name="ck_fiscal_year_date_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    client_entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    anno: Mapped[int] = mapped_column(Integer, nullable=False)
    data_inizio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fine: Mapped[date] = mapped_column(Date, nullable=False)
    stato: Mapped[str] = mapped_column(String(10), nullable=False, default="aperto")  # aperto | chiuso
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
