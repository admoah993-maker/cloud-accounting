from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os
import uvicorn

app = FastAPI(
    title="نظام ERP المحاسبي السحابي المتكامل",
    description="إدارة العملاء والمنتجات ونسب العمولات والربط المحاسبي.",
    version="4.6.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# قواعد البيانات المؤقتة
accounts_db = [
    {"id": 1010, "name": "الصندوق / النقدية", "type": "أصول متداولة"},
    {"id": 1020, "name": "حساب البنك الرئيسي", "type": "أصول متداولة"},
    {"id": 1100, "name": "ذمم العملاء (المدينون)", "type": "أصول متداولة"},
    {"id": 1200, "name": "مخزون البضائع", "type": "أصول متداولة"},
    {"id": 2010, "name": "ذمم الموردين (الدائنون)", "type": "خصوم متداولة"},
    {"id": 2200, "name": "ضريبة القيمة المضافة المستحقة (15%)", "type": "خصوم متداولة"},
    {"id": 3010, "name": "رأس المال", "type": "حقوق الملكية"},
    {"id": 4010, "name": "إيرادات المبيعات", "type": "الإيرادات"},
    {"id": 5010, "name": "تكلفة البضاعة المباعة (COGS)", "type": "تكلفة المبيعات"},
    {"id": 5020, "name": "مصروفات عمولات المبيعات", "type": "مصروفات تشغيلية"}
]

branches_db = [
    {"id": 1, "name": "الفرع الرئيسي - الرياض", "city": "الرياض"},
    {"id": 2, "name": "فرع المنطقة الغربية", "city": "جدة"}
]

employees_db = [
    {"id": 101, "name": "عبدالله الشمري", "branch_id": 1, "commission_rate": 5.0, "role": "مبيعات كبار العملاء"},
    {"id": 102, "name": "ريما العتيبي", "branch_id": 2, "commission_rate": 6.5, "role": "مستشار مبيعات"}
]

customers_db = [
    {
        "id": 501, 
        "name": "شركة الحلول المتقدمة المحدودة", 
        "phone": "+966500000000", 
        "branch_id": 1, 
        "tax_number": "310123456700003", 
        "national_address": "الرياض 12211 - حي العليا"
    },
    {
        "id": 502, 
        "name": "مؤسسة الأفق للخدمات اللوجستية", 
        "phone": "+966551112233", 
        "branch_id": 2, 
        "tax_number": "300987654300003", 
        "national_address": "جدة 21432 - حي الشاطئ"
    }
]

products_db = [
    {"id": 1001, "name": "خادم سحابي Enterprise Server X1", "price": 4500.0, "cost": 3000.0, "stock": 25, "sku": "SRV-X1"},
    {"id": 1002, "name": "ترخيص برنامج المحاسبة السنوي", "price": 1200.0, "cost": 200.0, "stock": 100, "sku": "SW-ACC-Y1"},
    {"id": 1003, "name": "جهاز طابعة فواتير حرارية", "price": 850.0, "cost": 550.0, "stock": 40, "sku": "HW-PRN-01"}
]

invoices_db = []
journal_entries_db = []

# Naming Models
class BranchCreate(BaseModel):
    id: int
    name: str
    city: str

class EmployeeCreate(BaseModel):
    id: int
    name: str
    branch_id: int
    commission_rate: float = Field(..., ge=0)
    role: Optional[str] = "موظف مبيعات"

class CustomerCreate(BaseModel):
    id: int
    name: str
    phone: str
    branch_id: int
    tax_number: Optional[str] = ""
    national_address: Optional[str] = ""

class ProductCreate(BaseModel):
    id: int
    sku: str
    name: str
    price: float = Field(..., gt=0)
    cost: float = Field(..., ge=0)
    stock: int = Field(default=0, ge=0)

# Endpoints
@app.get("/")
def root():
    return {"status": "online", "system": "ERP Engine", "version": "4.6.0"}

# الفروع
@app.get("/api/branches")
def get_branches(): return branches_db

@app.post("/api/branches")
def create_branch(item: BranchCreate):
    branches_db.append(item.dict())
    return {"message": "تم إضافة الفرع بنجاح"}

# الموظفين وعمولاتهم
@app.get("/api/employees")
def get_employees(): return employees_db

@app.post("/api/employees")
def create_employee(item: EmployeeCreate):
    employees_db.append(item.dict())
    return {"message": "تم إضافة الموظف وتحديد نسبة العمولة بنجاح"}

# العملاء والبيانات الضريبية
@app.get("/api/customers")
def get_customers(): return customers_db

@app.post("/api/customers")
def create_customer(item: CustomerCreate):
    customers_db.append(item.dict())
    return {"message": "تم إضافة العميل بنجاح"}

# المنتجات والمخزون
@app.get("/api/products")
def get_products(): return products_db

@app.post("/api/products")
def create_product(item: ProductCreate):
    products_db.append(item.dict())
    return {"message": "تم إضافة المنتج بنجاح"}

@app.get("/api/accounts")
def get_accounts(): return accounts_db

@app.get("/api/journal-entries")
def get_journals(): return journal_entries_db

@app.get("/api/invoices")
def get_invoices(): return invoices_db

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
