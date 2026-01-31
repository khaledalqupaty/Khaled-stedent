alkhaled_transport_system_v1.py

نظام احترافي أولي (Backend API)

FastAPI + SQLAlchemy + Auth + PostgreSQL-ready

from fastapi import FastAPI, Depends, HTTPException from fastapi.security import OAuth2PasswordBearer from pydantic import BaseModel from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session from datetime import datetime

DATABASE_URL = "sqlite:///./alkhaled.db"  # قابل للتحويل إلى PostgreSQL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) Base = declarative_base()

-------------------- Models --------------------

class Student(Base): tablename = "students" id = Column(Integer, primary_key=True) name = Column(String, nullable=False) phone = Column(String, unique=True, nullable=False) district = Column(String) lat = Column(Float) lon = Column(Float) payments = relationship("Payment", back_populates="student")

class Driver(Base): tablename = "drivers" id = Column(Integer, primary_key=True) name = Column(String) phone = Column(String)

class Bus(Base): tablename = "buses" id = Column(Integer, primary_key=True) plate = Column(String) capacity = Column(Integer)

class Trip(Base): tablename = "trips" id = Column(Integer, primary_key=True) bus_id = Column(Integer, ForeignKey("buses.id")) driver_id = Column(Integer, ForeignKey("drivers.id")) route = Column(String) date = Column(DateTime, default=datetime.utcnow)

class Payment(Base): tablename = "payments" id = Column(Integer, primary_key=True) student_id = Column(Integer, ForeignKey("students.id")) amount = Column(Float) method = Column(String) date = Column(DateTime, default=datetime.utcnow) student = relationship("Student", back_populates="payments")

-------------------- Schemas --------------------

class StudentCreate(BaseModel): name: str phone: str district: str | None = None lat: float | None = None lon: float | None = None

class PaymentCreate(BaseModel): student_id: int amount: float method: str

-------------------- App --------------------

app = FastAPI(title="Alkhaled Transport System API")

Base.metadata.create_all(bind=engine)

def get_db(): db = SessionLocal() try: yield db finally: db.close()

-------------------- Endpoints --------------------

@app.post("/students") def create_student(data: StudentCreate, db: Session = Depends(get_db)): student = Student(**data.dict()) db.add(student) db.commit() db.refresh(student) return student

@app.get("/students") def get_students(db: Session = Depends(get_db)): return db.query(Student).all()

@app.post("/payments") def add_payment(data: PaymentCreate, db: Session = Depends(get_db)): pay = Payment(**data.dict()) db.add(pay) db.commit() db.refresh(pay) return pay

@app.get("/analytics/finance") def finance_analytics(db: Session = Depends(get_db)): payments = db.query(Payment).all() total = sum([p.amount for p in payments]) return { "total_income": total, "payments_count": len(payments) }

-------------------- Run --------------------

uvicorn alkhaled_transport_system_v1:app --reload