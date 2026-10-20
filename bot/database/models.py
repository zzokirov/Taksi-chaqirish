"""
Farg'ona Viloyati Taksi Bot — Database Models.
8 ta jadval: users, drivers, payments, orders, districts, driver_groups, settings, admin_logs
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey, Integer,
    Numeric, String, Text, func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base model."""
    pass


class User(Base):
    """Foydalanuvchilar jadvali."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    role = Column(String(20), default="customer")  # customer, driver, admin
    created_at = Column(DateTime, default=func.now())

    # Relationships
    driver = relationship("Driver", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="customer", foreign_keys="Order.customer_id")


class Driver(Base):
    """Haydovchilar jadvali."""
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    car_model = Column(String(100), nullable=False)
    car_number = Column(String(20), nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False)
    status = Column(String(20), default="PENDING")  # PENDING, APPROVED, REJECTED, BLOCKED
    online_status = Column(String(20), default="OFFLINE")  # ONLINE, OFFLINE
    payment_status = Column(String(20), default="NONE")  # NONE, PENDING, APPROVED, REJECTED, EXPIRED
    created_at = Column(DateTime, default=func.now())
    approved_at = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    approved_by = Column(BigInteger, nullable=True)

    # Relationships
    user = relationship("User", back_populates="driver")
    district = relationship("District", back_populates="drivers")
    payments = relationship("Payment", back_populates="driver", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="driver", foreign_keys="Order.driver_id")


class SupportMessage(Base):
    """Yordam so'rovlari jadvali."""
    __tablename__ = "support_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_type = Column(String(20), default="text") # text, photo, voice, video
    text_content = Column(Text, nullable=True)
    file_id = Column(String(255), nullable=True)
    status = Column(String(20), default="NEW") # NEW, READ
    created_at = Column(DateTime, default=func.now())
    
    user = relationship("User", lazy="joined")


class Payment(Base):
    """To'lovlar jadvali."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    card_number = Column(String(30), nullable=True)
    receipt_file_id = Column(String(255), nullable=True)
    receipt_type = Column(String(10), nullable=True)  # jpg, png, pdf
    status = Column(String(20), default="PENDING")  # PENDING, APPROVED, REJECTED
    created_at = Column(DateTime, default=func.now())
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(BigInteger, nullable=True)

    # Relationships
    driver = relationship("Driver", back_populates="payments")


class Order(Base):
    """Buyurtmalar jadvali."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False)
    from_address = Column(String(500), nullable=False)
    to_address = Column(String(500), nullable=False)
    passengers = Column(Integer, default=1)
    price = Column(String(50), nullable=True)
    status = Column(String(30), default="NEW")
    # Statuslar: NEW, SEARCHING_DRIVER, DRIVER_ACCEPTED, DRIVER_ON_WAY,
    #            DRIVER_ARRIVED, TRIP_STARTED, COMPLETED, CANCELLED
    created_at = Column(DateTime, default=func.now())
    accepted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancel_reason = Column(Text, nullable=True)
    group_chat_id = Column(BigInteger, nullable=True)
    group_message_id = Column(BigInteger, nullable=True)

    # Relationships
    customer = relationship("User", back_populates="orders", foreign_keys=[customer_id])
    driver = relationship("Driver", back_populates="orders", foreign_keys=[driver_id])
    district = relationship("District", back_populates="orders")


class District(Base):
    """Tumanlar/shaharlar jadvali."""
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    status = Column(String(20), default="ACTIVE")  # ACTIVE, INACTIVE
    created_at = Column(DateTime, default=func.now())

    # Relationships
    drivers = relationship("Driver", back_populates="district")
    orders = relationship("Order", back_populates="district")
    groups = relationship("DriverGroup", back_populates="district")


class DriverGroup(Base):
    """Haydovchilar guruhlari jadvali."""
    __tablename__ = "driver_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False)
    group_name = Column(String(200), nullable=False)
    telegram_group_id = Column(BigInteger, nullable=True)
    invite_link = Column(String(500), nullable=True)
    status = Column(String(20), default="ACTIVE")  # ACTIVE, INACTIVE
    created_at = Column(DateTime, default=func.now())

    # Relationships
    district = relationship("District", back_populates="groups")


class Setting(Base):
    """Sozlamalar jadvali."""
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)


class AdminLog(Base):
    """Admin log jadvali."""
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(BigInteger, nullable=False)
    action = Column(String(200), nullable=False)
    target_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now())
