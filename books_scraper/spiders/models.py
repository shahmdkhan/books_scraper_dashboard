from datetime import date

from sqlalchemy import (
    Column, Integer, String, Boolean,
    ForeignKey, Date, Text, UniqueConstraint, Float, JSON, Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Interest flag constants — mirror the Django model choices
INTEREST_PENDING        = "pending"
INTEREST_INTERESTED     = "interested"
INTEREST_NOT_INTERESTED = "not_interested"


class Source(Base):
    __tablename__ = "source_table"

    spider_id     = Column(Integer, primary_key=True, autoincrement=True)
    spider_name   = Column(String, unique=True)
    spider_domain = Column(String)

    histories = relationship("History", back_populates="source", cascade="all, delete-orphan")


class History(Base):
    __tablename__ = "history_table"

    history_id      = Column(Integer, primary_key=True, autoincrement=True)
    site_id         = Column(Integer, ForeignKey("source_table.spider_id"))
    isbn            = Column(String)
    available_books = Column(Integer, default=0)
    sold_books      = Column(Integer, default=0)

    source  = relationship("Source", back_populates="histories")
    details = relationship("Detail", back_populates="history", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("site_id", "isbn", name="uq_siteid_isbn"),)


class Detail(Base):
    __tablename__ = "details_table"

    detail_id    = Column(Integer, primary_key=True, autoincrement=True)
    history_id   = Column(Integer, ForeignKey("history_table.history_id"), nullable=False)
    isbn         = Column(String)
    date_scraped = Column(Date, default=date.today)
    first_seen   = Column(Date, default=date.today)
    site_id      = Column(Integer)
    name         = Column(Text)
    price        = Column(Float)
    seller       = Column(Text)
    condition    = Column(Text)
    editorial    = Column(Text)
    images       = Column(JSON)
    url          = Column(Text)
    availability = Column(Boolean, default=True)
    interest = Column(String(20), nullable=False, default=INTEREST_PENDING, server_default=INTEREST_PENDING,)
    contact = Column(Boolean, default=False)

    history = relationship("History", back_populates="details")

    __table_args__ = (
        UniqueConstraint("url", name="uq_detail_url"),
        Index("ix_details_interest", "interest"),
    )