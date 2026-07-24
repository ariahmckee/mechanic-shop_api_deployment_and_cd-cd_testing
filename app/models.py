from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import date
from typing import List

# Create a base class for our models
class Base(DeclarativeBase):
    pass

# Instantiate your SQLAlchemy database
db = SQLAlchemy(model_class = Base)


class Customer(Base):
    __tablename__ = 'customers'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(db.String(20), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(db.String(100), nullable=False)
    
    tickets: Mapped[List['Ticket']] = db.relationship(back_populates='customer', cascade="all, delete")

ticket_mechanic = db.Table(
    'ticket_mechanic',
    Base.metadata,
    db.Column('ticket_id', db.ForeignKey('tickets.id')),
    db.Column('mechanic_id', db.ForeignKey('mechanics.id'))
)

class Ticket(Base):
    __tablename__ = 'tickets'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    vin: Mapped[str] = mapped_column(db.String(255),nullable=False)
    ticket_date: Mapped[date] = mapped_column(db.Date)
    ticket_desc: Mapped[str]= mapped_column(db.String(255),nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('customers.id'), nullable=False)
    
    customer: Mapped['Customer'] = db.relationship(back_populates='tickets')   
    mechanics: Mapped[List['Mechanic']] = db.relationship(secondary=ticket_mechanic, back_populates='tickets')
    inventory_items: Mapped[List['TicketInventory']] = db.relationship(back_populates='ticket', cascade="all, delete-orphan")
    
class Mechanic(Base):
    __tablename__ = 'mechanics'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(db.String(20), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(db.String(100), nullable=False)
    salary: Mapped[float]
    
    tickets: Mapped[List['Ticket']] = db.relationship(secondary=ticket_mechanic, back_populates='mechanics')

class Inventory(Base):
    __tablename__ = 'inventory'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    
    ticket_items: Mapped[List['TicketInventory']] = db.relationship(back_populates='inventory', cascade="all, delete-orphan")

class TicketInventory(Base):
    __tablename__ = 'ticket_inventory'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(db.ForeignKey('tickets.id'), nullable=False)
    inventory_id: Mapped[int] = mapped_column(db.ForeignKey('inventory.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False, default=1)
    
    ticket: Mapped['Ticket'] = db.relationship(back_populates='inventory_items')
    inventory: Mapped['Inventory'] = db.relationship(back_populates='ticket_items')
