"""
Transaction model for Finance App.
Modelo otimizado para análise financeira com LLM.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Date, Boolean, 
    Text, JSON, Index, ForeignKey, Enum as SQLEnum, CheckConstraint
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum

from .database import Base


class TransactionType(enum.Enum):
    """Tipos de transação."""
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"
    PIX = "pix"
    TED = "ted"
    DOC = "doc"
    BOLETO = "boleto"
    CARD = "card"
    CASH = "cash"


class TransactionStatus(enum.Enum):
    """Status da transação."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PROCESSING = "processing"


class Transaction(Base):
    """
    Modelo de transação financeira.
    
    Otimizado para análise com LLM e detecção de padrões.
    """
    __tablename__ = "transactions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic transaction info
    date = Column(Date, nullable=False, index=True)
    datetime = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text, nullable=False)
    
    # Transaction classification
    transaction_type = Column(SQLEnum(TransactionType), nullable=False, index=True)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.COMPLETED, index=True)
    
    # Account information
    account_id = Column(String(50), nullable=True, index=True)
    account_name = Column(String(200), nullable=True)
    
    # Counterpart information
    counterpart_name = Column(String(200), nullable=True)
    counterpart_document = Column(String(20), nullable=True)
    counterpart_bank = Column(String(10), nullable=True)
    
    # Location and channel
    location = Column(String(200), nullable=True)
    channel = Column(String(50), nullable=True)  # app, atm, branch, online
    
    # Categorization (manual and automatic)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    subcategory = Column(String(100), nullable=True)
    tags = Column(JSONB, nullable=True)  # Array of tags
    
    # LLM Analysis
    llm_category = Column(String(100), nullable=True)  # AI suggested category
    llm_confidence = Column(Numeric(3, 2), nullable=True)  # Confidence score 0-1
    llm_analysis = Column(JSONB, nullable=True)  # Full LLM analysis
    
    # Recurring transaction detection
    is_recurring = Column(Boolean, default=False, index=True)
    recurring_pattern = Column(String(50), nullable=True)  # monthly, weekly, etc.
    recurring_group_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Import information
    import_source = Column(String(50), nullable=True)  # csv, ofx, api
    import_batch_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    external_id = Column(String(100), nullable=True, index=True)  # Bank's transaction ID
    
    # Metadata
    raw_data = Column(JSONB, nullable=True)  # Original import data
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("Category", back_populates="transactions")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('amount != 0', name='amount_not_zero'),
        Index('idx_date_amount', 'date', 'amount'),
        Index('idx_description_search', 'description'),
        Index('idx_recurring_group', 'recurring_group_id', 'date'),
        Index('idx_import_batch', 'import_batch_id'),
        Index('idx_llm_category', 'llm_category', 'llm_confidence'),
    )
    
    @validates('amount')
    def validate_amount(self, key, amount):
        """Validate transaction amount."""
        if amount == 0:
            raise ValueError("Transaction amount cannot be zero")
        return amount
    
    @validates('description')
    def validate_description(self, key, description):
        """Validate and clean description."""
        if not description or not description.strip():
            raise ValueError("Description cannot be empty")
        return description.strip()
    
    @property
    def is_debit(self) -> bool:
        """Check if transaction is a debit (negative amount)."""
        return self.amount < 0
    
    @property
    def is_credit(self) -> bool:
        """Check if transaction is a credit (positive amount)."""
        return self.amount > 0
    
    @property
    def absolute_amount(self) -> Decimal:
        """Get absolute value of amount."""
        return abs(self.amount)
    
    @property
    def formatted_amount(self) -> str:
        """Get formatted amount in Brazilian currency."""
        return f"R$ {self.amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary."""
        return {
            'id': str(self.id),
            'date': self.date.isoformat() if self.date else None,
            'datetime': self.datetime.isoformat() if self.datetime else None,
            'amount': float(self.amount),
            'description': self.description,
            'transaction_type': self.transaction_type.value if self.transaction_type else None,
            'status': self.status.value if self.status else None,
            'account_id': self.account_id,
            'account_name': self.account_name,
            'counterpart_name': self.counterpart_name,
            'counterpart_document': self.counterpart_document,
            'counterpart_bank': self.counterpart_bank,
            'location': self.location,
            'channel': self.channel,
            'category_id': self.category_id,
            'subcategory': self.subcategory,
            'tags': self.tags,
            'llm_category': self.llm_category,
            'llm_confidence': float(self.llm_confidence) if self.llm_confidence else None,
            'llm_analysis': self.llm_analysis,
            'is_recurring': self.is_recurring,
            'recurring_pattern': self.recurring_pattern,
            'recurring_group_id': str(self.recurring_group_id) if self.recurring_group_id else None,
            'import_source': self.import_source,
            'import_batch_id': str(self.import_batch_id) if self.import_batch_id else None,
            'external_id': self.external_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def get_llm_context(self) -> str:
        """Get transaction context for LLM analysis."""
        context_parts = [
            f"Transação: {self.description}",
            f"Valor: {self.formatted_amount}",
            f"Data: {self.date.strftime('%d/%m/%Y') if self.date else 'N/A'}",
            f"Tipo: {self.transaction_type.value if self.transaction_type else 'N/A'}",
        ]
        
        if self.counterpart_name:
            context_parts.append(f"Destinatário: {self.counterpart_name}")
        
        if self.location:
            context_parts.append(f"Local: {self.location}")
        
        if self.channel:
            context_parts.append(f"Canal: {self.channel}")
        
        return " | ".join(context_parts)
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, date={self.date}, amount={self.amount}, description='{self.description[:50]}...')>"


class ImportBatch(Base):
    """
    Modelo para controle de importação de dados.
    """
    __tablename__ = "import_batches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # csv, ofx, api
    total_records = Column(Integer, nullable=False, default=0)
    processed_records = Column(Integer, nullable=False, default=0)
    successful_records = Column(Integer, nullable=False, default=0)
    failed_records = Column(Integer, nullable=False, default=0)
    
    status = Column(String(20), nullable=False, default="processing")  # processing, completed, failed
    error_log = Column(JSONB, nullable=True)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Metadata
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True)
    import_settings = Column(JSONB, nullable=True)
    
    def __repr__(self):
        return f"<ImportBatch(id={self.id}, filename='{self.filename}', status='{self.status}')>"

