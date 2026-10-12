from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os
import uvicorn

app = FastAPI(
    title="نظام المحاسبة السحابي المتكامل - ERP",
    description="إدارة الحسابات، المنتجات، العملاء، الفروع، الموظفين، وعمولات المبيعات.",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# قواعد البيانات المؤقتة (In-Memory Database)
accounts_db = [
    {"id": 101, "name": "الصندوق / النقدية", "type": "أصول"},
    {"id": 102, "name": "البنك", "type": "أصول"},
    {"id": 201, "name": "الموردون", "type": "خصوم"},
    {"id": 301, "name": "رأس المال", "type": "حقوق ملكية"},
    {"id": 401, "name": "إيرادات المبيعات", "type": "إيرادات"},
    {"id": 501, "name": "مصروفات الإيجار", "type": "مصروفات"}
]

branches_db = [
    {"id": 1, "name": "الفرع الرئيسي", "city": "الرياض"},
    {"id": 2, "name": "فرع جدة", "city": "جدة"}
]

employees_db = [
    {"id": 1, "name": "أحمد محمد", "branch_id": 1, "commission_rate": 5.0},
    {"id": 2, "name": "سارة خالد", "branch_id": 2, "commission_rate": 7.5}
]

customers_db = [
    {"id": 1, "name": "شركة النور التجارية", "phone": "0500000000", "branch_id": 1},
    {"id": 2, "name": "مؤسسة التقنية الحديثة", "phone": "0511111111", "branch_id": 2}
]

products_db = [
    {"id": 1, "name": "منتج أ", "price": 150.0, "cost": 100.0, "stock": 50},
    {"id": 2, "name": "منتج ب", "price": 300.0, "cost": 200.0, "stock": 20}
]

journal_entries_db = []

# النماذج (Models)
class BranchCreate(BaseModel):
    id: int
    name: str
    city: str

class EmployeeCreate(BaseModel):
    id: int
    name: str
    branch_id: int
    commission_rate: float = Field(default=0.0, ge=0)

class CustomerCreate(BaseModel):
    id: int
    name: str
    phone: str
    branch_id: int

class ProductCreate(BaseModel):
    id: int
    name: str
    price: float = Field(..., gt=0)
    cost: float = Field(..., ge=0)
    stock: int = Field(default=0, ge=0)

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

# مسارات الفروع
@app.get("/api/branches", summary="عرض الفروع")
def get_branches():
    return branches_db

@app.post("/api/branches", summary="إضافة فرع جديد")
def create_branch(branch: BranchCreate):
    branches_db.append(branch.dict())
    return {"message": "تم إضافة الفرع بنجاح", "branch": branch}

# مسارات الموظفين وعمولات المبيعات
@app.get("/api/employees", summary="عرض الموظفين ونسب العمولات")
def get_employees():
    return employees_db

@app.post("/api/employees", summary="إضافة موظف جديد وتحديد عمولته")
def create_employee(emp: EmployeeCreate):
    employees_db.append(emp.dict())
    return {"message": "تم إضافة الموظف وتحديد نسبة العمولة بنجاح", "employee": emp}

# مسارات العملاء
@app.get("/api/customers", summary="عرض العملاء")
def get_customers():
    return customers_db

@app.post("/api/customers", summary="إضافة عميل جديد")
def create_customer(cust: CustomerCreate):
    customers_db.append(cust.dict())
    return {"message": "تم إضافة العميل بنجاح", "customer": cust}

# مسارات المنتجات والمخزون
@app.get("/api/products", summary="عرض المنتجات")
def get_products():
    return products_db

@app.post("/api/products", summary="إضافة منتج جديد")
def create_product(prod: ProductCreate):
    products_db.append(prod.dict())
    return {"message": "تم إضافة المنتج بنجاح", "product": prod}

# المسارات الأساسية للحسابات والقيود
@app.get("/")
def read_root():
    return {"status": "online", "message": "نظام ERP المحاسبي يعمل بكفاءة!"}

@app.get("/api/accounts")
def get_accounts():
    return accounts_db

@app.post("/api/accounts")
def create_account(account: AccountCreate):
    accounts_db.append(account.dict())
    return {"message": "تم إضافة الحساب بنجاح", "account": account}

@app.post("/api/journal-entries")
def create_journal_entry(entry: JournalEntryModel):
    total_debit = sum(line.debit for line in entry.lines)
    total_credit = sum(line.credit for line in entry.lines)
    if abs(total_debit - total_credit) > 0.001:
        raise HTTPException(status_code=400, detail="القيد غير متوازن (المدين لا يساوي الدائن)")
    
    entry_data = entry.dict()
    entry_data["id"] = len(journal_entries_db) + 1
    entry_data["created_at"] = datetime.now().isoformat()
    journal_entries_db.append(entry_data)
    return {"message": "تم ترحيل القيد بنجاح", "entry_id": entry_data["id"]}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
