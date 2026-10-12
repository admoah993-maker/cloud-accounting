import os
from typing import List
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

# إعداد قاعدة البيانات (يدعم السحاب عبر PostgreSQL أو محلياً عبر SQLite)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./cloud_accounting.db")

# تعديل توافقية رابط قاعدة البيانات لـ SQLAlchemy إذا لزم الأمر
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- تعريف جداول قاعدة البيانات (ORM Models) ---
class DBAccount(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String)
    account_type = Column(String) # أصول، خصوم، إيرادات، مصروفات، حقوق ملكية

class DBJournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String)
    description = Column(String)
    lines = relationship("DBJournalLine", back_populates="entry", cascade="all, delete-orphan")

class DBJournalLine(Base):
    __tablename__ = "journal_lines"
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id"))
    account_code = Column(String)
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    
    entry = relationship("DBJournalEntry", back_populates="lines")

# إنشاء الجداول تلقائياً عند البدء
Base.metadata.create_all(bind=engine)

# Dependency لجلب قاعدة البيانات
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- نماذج التحقق (Pydantic Models) ---
class AccountCreate(BaseModel):
    code: str
    name: str
    account_type: str

class JournalLineModel(BaseModel):
    account_code: str
    debit: float = Field(0.0, ge=0)
    credit: float = Field(0.0, ge=0)

class JournalEntryModel(BaseModel):
    date: str
    description: str
    lines: List[JournalLineModel]

# --- تطبيق FastAPI ---
app = FastAPI(
    title="نظام المحاسبة السحابي المتكامل",
    description="واجهة برمجية سحابية لإدارة الحسابات، قيود اليومية، والتقارير المالية.",
    version="2.0.0"
)

@app.get("/", summary="التحقق من حالة النظام السحابي")
def read_root():
    return {"status": "online", "message": "النظام المحاسبي السحابي يعمل بكفاءة عالية ومن أي مكان!"}

# 1. إضافة حساب جديد لدليل الحسابات
@app.post("/api/accounts", summary="إضافة حساب جديد")
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    existing = db.query(DBAccount).filter(DBAccount.code == account.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="رقم الحساب موجود مسبقاً.")
    
    db_account = DBAccount(code=account.code, name=account.name, account_type=account.account_type)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return {"message": "تم إضافة الحساب بنجاح", "account": db_account.code}

# 2. عرض دليل الحسابات
@app.get("/api/accounts", summary="عرض دليل الحسابات")
def get_accounts(db: Session = Depends(get_db)):
    return db.query(DBAccount).all()

# 3. ترحيل قيد يومية (مع التحقق من التوازن المالي المدين = الدائن)
@app.post("/api/journal-entries", summary="إصدار وترحيل قيد يومية")
def post_journal_entry(entry: JournalEntryModel, db: Session = Depends(get_db)):
    total_debit = sum(line.debit for line in entry.lines)
    total_credit = sum(line.credit for line in entry.lines)

    # القاعدة الذهبية للمحاسبة
    if round(total_debit, 2) != round(total_credit, 2):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "قيد غير متزن محاسبياً",
                "total_debit": total_debit,
                "total_credit": total_credit,
                "message": "إجمالي المدين يجب أن يساوي إجمالي الدائن تماماً."
            }
        )

    # حفظ القيد في قاعدة البيانات السحابية
    db_entry = DBJournalEntry(date=entry.date, description=entry.description)
    for line in entry.lines:
        db_line = DBJournalLine(
            account_code=line.account_code,
            debit=line.debit,
            credit=line.credit
        )
        db_entry.lines.append(db_line)
    
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    return {
        "status": "success",
        "message": f"تم ترحيل القيد برقم مرجعي [{db_entry.id}] بنجاح.",
        "total_amount": total_debit
    }

# تشغيل الخادم السحابي بالمنفذ المخصص تلقائياً
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
