"""
Modelli Phase 5 — Studio Task Management.

REGOLA: usa sempre `from sqlalchemy import Uuid` (NON dialects.postgresql.UUID)
         per compatibilità SQLite nei test.
"""
import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, DateTime, Date, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StudioTask(Base):
    """Task di studio (scadenze fiscali, attività clienti, etc.)."""

    __tablename__ = "studio_tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    studio_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    client_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    fiscal_year_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    titolo: Mapped[str] = mapped_column(String(255), nullable=False)
    descrizione: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    # scadenza_iva | versamento_ritenute | chiusura_bilancio | generico
    priorita: Mapped[str] = mapped_column(String(10), nullable=False, default="normale")
    # bassa | normale | alta | urgente
    stato: Mapped[str] = mapped_column(String(10), nullable=False, default="aperto")
    # aperto | completato | annullato
    data_scadenza: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    assegnato_a: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    completato_il: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
