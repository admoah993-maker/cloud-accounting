from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

app = FastAPI(
    title="نظام المحاسبة السحابي المتكامل",
    description="واجهة برمجية سحابية لإدارة الحسابات، قيود اليومية، والتقارير المالية.",
    version="2.0.0"
)

# تفعيل CORS للتوافق التام مع الواجهات الرسومية (Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# قاعدة بيانات مؤقتة في الذاكرة (In-Memory Database)
accounts_db = [
    {"id": 101, "name": "الصندوق / النقدية", "type": "أصول"},
    {"id": 102, "name": "البنك", "type": "أصول"},
    {"id": 201, "name": "الموردون", "type": "خصوم"},
    {"id": 301, "name": "رأس المال", "type": "حقوق ملكية"},
    {"id": 401, "name": "إيرادات المبيعات", "type": "إيرادات"},
    {"id": 501, "name": "مصروفات الإيجار", "type": "مصروفات"}
]

journal_entries_db = []

# نماذج البيانات (Models)
class AccountCreate(BaseModel):
    id: int
    name: str
    type: str

class JournalLineModel(BaseModel):
    account_id: int
    debit: float = Field(default=0.0, ge=0)
    credit: float = Field(default=0.0, ge=0)

class JournalEntryModel(BaseModel):
    description: str
    lines: List[JournalLineModel]

# المسارات (Endpoints)
@app.get("/", summary="التحقق من حالة النظام السحابي")
def read_root():
    return {
        "status": "online",
        "message": "النظام المحاسبي السحابي يعمل بكفاءة عالية ومن أي مكان!"
    }

@app.get("/api/accounts", summary="عرض دليل الحسابات")
def get_accounts():
    return accounts_db

@app.post("/api/accounts", summary="إضافة حساب جديد")
def create_account(account: AccountCreate):
    for acc in accounts_db:
        if acc["id"] == account.id:
            raise HTTPException(status_code=400, detail="رقم الحساب موجود بالفعل.")
    accounts_db.append(account.dict())
    return {"message": "تم إضافة الحساب بنجاح", "account": account}

@app.post("/api/journal-entries", summary="إصدار وترحيل قيد يومية")
def create_journal_entry(entry: JournalEntryModel):
    total_debit = sum(line.debit for line in entry.lines)
    total_credit = sum(line.credit for line in entry.lines)
    
    if abs(total_debit - total_credit) > 0.001:
        raise HTTPException(
            status_code=400, 
            detail=f"القيد غير متوازن! إجمالي المدين ({total_debit}) لا يساوي إجمالي الدائن ({total_credit})"
        )
    
    entry_data = entry.dict()
    entry_data["id"] = len(journal_entries_db) + 1
    entry_data["created_at"] = datetime.now().isoformat()
    journal_entries_db.append(entry_data)
    
    return {
        "message": "تم ترحيل قيد اليومية بنجاح",
        "entry_id": entry_data["id"],
        "total_amount": total_debit
    }
