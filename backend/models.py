from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True, index=True)
    username    = Column(String, unique=True, nullable=False, index=True)
    full_name   = Column(String, nullable=False)
    hashed_pw   = Column(String, nullable=False)
    role        = Column(String, default="viewer")   # admin | viewer
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)


class Property(Base):
    __tablename__ = "properties"

    id      = Column(String, primary_key=True)   # P001
    name    = Column(String, nullable=False)
    city    = Column(String)
    address = Column(String)
    type    = Column(String)                     # residential|commercial|mixed

    units   = relationship("Unit", back_populates="property")


class Unit(Base):
    __tablename__ = "units"

    id          = Column(String, primary_key=True)   # U001
    property_id = Column(String, ForeignKey("properties.id"), nullable=False)
    number      = Column(String, nullable=False)
    floor       = Column(Integer, default=0)
    type        = Column(String)
    area_m2     = Column(Float)
    deleted     = Column(Boolean, default=False)

    property    = relationship("Property", back_populates="units")
    contracts   = relationship("Contract", back_populates="unit")


class Tenant(Base):
    __tablename__ = "tenants"

    id          = Column(String, primary_key=True)   # T001
    name        = Column(String, nullable=False)
    phone       = Column(String)
    email       = Column(String)
    id_number   = Column(String)
    deleted     = Column(Boolean, default=False)

    contracts   = relationship("Contract", back_populates="tenant")


class Contract(Base):
    __tablename__ = "contracts"

    id               = Column(String, primary_key=True)   # C001
    unit_id          = Column(String, ForeignKey("units.id"), nullable=False)
    tenant_id        = Column(String, ForeignKey("tenants.id"), nullable=False)
    ejar_number      = Column(String)
    start_date       = Column(String, nullable=False)
    end_date         = Column(String, nullable=False)
    annual_rent      = Column(Float, nullable=False)
    installments     = Column(Integer, default=12)
    installment_day  = Column(Integer, default=1)
    status           = Column(String, default="active")   # active|expired|terminated
    archived         = Column(Boolean, default=False)
    archived_at      = Column(String)
    deleted          = Column(Boolean, default=False)

    unit             = relationship("Unit", back_populates="contracts")
    tenant           = relationship("Tenant", back_populates="contracts")
    payments         = relationship("Payment", back_populates="contract")
    followup_logs    = relationship("FollowupLog", back_populates="contract")


class Payment(Base):
    __tablename__ = "payments"

    id             = Column(String, primary_key=True)   # PAY001
    contract_id    = Column(String, ForeignKey("contracts.id"), nullable=False)
    due_date       = Column(String, nullable=False)
    amount_due     = Column(Float, nullable=False)
    amount_paid    = Column(Float, default=0)
    paid_date      = Column(String)
    status         = Column(String, default="pending")   # pending|paid|partial|overdue
    receipt_number = Column(String)
    deleted        = Column(Boolean, default=False)
    deleted_at     = Column(String)

    contract       = relationship("Contract", back_populates="payments")
    receipt_tokens = relationship("ReceiptToken", back_populates="payment")


class ReceiptToken(Base):
    __tablename__ = "receipt_tokens"

    token       = Column(String, primary_key=True)
    payment_id  = Column(String, ForeignKey("payments.id"), nullable=False)
    expiry      = Column(String, nullable=False)

    payment     = relationship("Payment", back_populates="receipt_tokens")


class FollowupLog(Base):
    __tablename__ = "followup_logs"

    id          = Column(String, primary_key=True)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    payment_id  = Column(String)
    action      = Column(String)
    note        = Column(Text)
    ts          = Column(String)

    contract    = relationship("Contract", back_populates="followup_logs")


class AppSetting(Base):
    __tablename__ = "app_settings"

    key   = Column(String, primary_key=True)
    value = Column(Text)
