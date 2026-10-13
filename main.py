from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os
import uvicorn

app = FastAPI(
    title="نظام ERP المحاسبي السحابي - الشامل",
    description="إدارة الشجرة المحاسبية، الصلاحيات، القيود اليومية، المبيعات، المشتريات، والتقارير الضريبية.",
    version="7.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. قاعدة بيانات المستخدمين والصلاحيات
users_db = [
    {"username": "admin", "password": "123", "name": "مدير النظام", "role": "admin"},
    {"username": "accountant", "password": "123", "name": "المحاسب الرئيسي", "role": "accountant"},
    {"username": "sales", "password": "123", "name": "عبدالله الشمري", "role": "sales"}
]

# 2. الشجرة المحاسبية الكاملة
accounts_db = [
    {"id": 1010, "name": "الصندوق / النقدية", "type": "أصول"},
    {"id": 1020, "name": "البنوك", "type": "أصول"},
    {"id": 1100, "name": "ذمم العملاء (المدينون)", "type": "أصول"},
    {"id": 1200, "name": "مخزون البضائع", "type": "أصول"},
    {"id": 2010, "name": "ذمم الموردين (الدائنون)", "type": "خصوم"},
    {"id": 2200, "name": "ضريبة القيمة المضافة المستحقة (مبيعات)", "type": "خصوم"},
    {"id": 2210, "name": "ضريبة القيمة المضافة القابلة للاسترداد (مشتريات)", "type": "أصول"},
    {"id": 3010, "name": "رأس المال الأساسي", "type": "حقوق ملكية"},
    {"id": 4010, "name": "إيرادات مبيعات المنتجات والخدمات", "type": "إيرادات"},
    {"id": 5010, "name": "تكلفة البضاعة المباعة (COGS)", "type": "مصروفات"},
    {"id": 5140, "name": "مصروف عمولات المبيعات", "type": "مصروفات"}
]

branches_db = [
    {"id": 1, "name": "الفرع الرئيسي - الرياض", "city": "الرياض"},
    {"id": 2, "name": "فرع جدة", "city": "جدة"}
]

employees_db = [
    {"id": 101, "name": "عبدالله الشمري", "username": "sales", "role": "sales", "branch_id": 1, "commission_rate": 5.0},
    {"id": 102, "name": "المحاسب الرئيسي", "username": "accountant", "role": "accountant", "branch_id": 1, "commission_rate": 0.0}
]

customers_db = [
    {
        "id": 501, 
        "name": "شركة الحلول المتقدمة المحدودة", 
        "phone": "+966500000000", 
        "branch_id": 1, 
        "tax_number": "310123456700003", 
        "national_address": "الرياض - حي العليا"
    }
]

products_db = [
    {"id": 1001, "sku": "SRV-X1", "name": "خادم سحابي Enterprise Server X1", "price": 4500.0, "cost": 3000.0, "stock": 25},
    {"id": 1002, "sku": "SW-ACC-Y1", "name": "ترخيص برنامج المحاسبة السنوي", "price": 1200.0, "cost": 200.0, "stock": 100}
]

invoices_db = []
purchases_db = []
journal_entries_db = []

# نماذج الإدخال
class LoginRequest(BaseModel):
    username: str
    password: str

class InvoiceLineItem(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class InvoiceCreateRequest(BaseModel):
    customer_id: int
    employee_id: int
    branch_id: int
    payment_method: str
    vat_rate: float = Field(default=15.0, ge=0)
    items: List[InvoiceLineItem]

class PurchaseCreateRequest(BaseModel):
    supplier_name: str
    product_id: int
    quantity: int = Field(..., gt=0)
    unit_cost: float = Field(..., gt=0)
    vat_rate: float = Field(default=15.0, ge=0)

@app.get("/")
def root():
    return {"status": "online", "message": "نظام ERP المحاسبي الشامل مع نظام الصلاحيات والقيود المزدوجة يعمل بنجاح!"}

@app.post("/api/login")
def login(req: LoginRequest):
    user = next((u for u in users_db if u["username"] == req.username and u["password"] == req.password), None)
    if not user:
        raise HTTPException(status_code=401, detail="اسم المستخدم أو كلمة المرور غير صحيحة")
    return {"message": "تم تسجيل الدخول بنجاح", "user": {"name": user["name"], "username": user["username"], "role": user["role"]}}

@app.get("/api/accounts")
def get_accounts(): return accounts_db

@app.get("/api/branches")
def get_branches(): return branches_db

@app.get("/api/employees")
def get_employees(): return employees_db

@app.get("/api/customers")
def get_customers(): return customers_db

@app.get("/api/products")
def get_products(): return products_db

@app.get("/api/journal-entries")
def get_journals(): return journal_entries_db

@app.get("/api/invoices")
def get_invoices(): return invoices_db

@app.get("/api/purchases")
def get_purchases(): return purchases_db

# تسجيل مشتريات وتوليد القيد المحاسبي
@app.post("/api/purchases")
def create_purchase(req: PurchaseCreateRequest):
    product = next((p for p in products_db if p["id"] == req.product_id), None)
    if not product:
        raise HTTPException(status_code=400, detail="المنتج غير موجود")
    
    subtotal = req.quantity * req.unit_cost
    vat_amount = subtotal * (req.vat_rate / 100.0)
    grand_total = subtotal + vat_amount

    product["stock"] += req.quantity
    product["cost"] = req.unit_cost

    pur_id = len(purchases_db) + 1
    purchase_record = {
        "id": pur_id,
        "supplier_name": req.supplier_name,
        "product_name": product["name"],
        "quantity": req.quantity,
        "subtotal": subtotal,
        "vat_amount": vat_amount,
        "grand_total": grand_total,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    purchases_db.append(purchase_record)

    journal_entry = {
        "id": len(journal_entries_db) + 1,
        "ref": f"PUR-REF-{pur_id}",
        "description": f"إثبات فاتورة مشتريات من المورد ({req.supplier_name})",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lines": [
            {"account_id": 1200, "account_name": "مخزون البضائع", "debit": subtotal, "credit": 0.0},
            {"account_id": 2210, "account_name": "ضريبة القيمة المضافة القابلة للاسترداد (مشتريات)", "debit": vat_amount, "credit": 0.0},
            {"account_id": 1010, "account_name": "الصندوق / النقدية", "debit": 0.0, "credit": grand_total}
        ]
    }
    journal_entries_db.append(journal_entry)

    return {"message": "تم تسجل المشتريات وتوليد القيد المحاسبي وتحديث المخزون بنجاح", "purchase": purchase_record}

# إصدار فاتورة مبيعات وتوليد القيود المحاسبية التلقائية
@app.post("/api/invoices")
def create_invoice(req: InvoiceCreateRequest):
    customer = next((c for c in customers_db if c["id"] == req.customer_id), None)
    employee = next((e for e in employees_db if e["id"] == req.employee_id), None)
    branch = next((b for b in branches_db if b["id"] == req.branch_id), None)

    if not customer or not employee or not branch:
        raise HTTPException(status_code=400, detail="العميل أو الموظف أو الفرع غير موجود.")

    subtotal = 0.0
    total_cost = 0.0
    processed_items = []

    for item in req.items:
        product = next((p for p in products_db if p["id"] == item.product_id), None)
        if not product or product["stock"] < item.quantity:
            raise HTTPException(status_code=400, detail="المنتج غير متوفر أو الكمية بالمخزن غير كافية.")

        product["stock"] -= item.quantity
        line_price = product["price"] * item.quantity
        line_cost = product["cost"] * item.quantity
        subtotal += line_price
        total_cost += line_cost

        processed_items.append({
            "product_id": product["id"],
            "sku": product["sku"],
            "name": product["name"],
            "unit_price": product["price"],
            "quantity": item.quantity,
            "net_total": line_price
        })

    vat_amount = subtotal * (req.vat_rate / 100.0)
    grand_total = subtotal + vat_amount
    commission_earned = subtotal * (employee["commission_rate"] / 100.0)

    inv_id = len(invoices_db) + 1
    
    sales_journal = {
        "id": len(journal_entries_db) + 1,
        "ref": f"INV-REF-{inv_id}",
        "description": f"إثبات فاتورة مبيعات رقم #{inv_id} للعميل ({customer['name']})",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lines": [
            {"account_id": 1010, "account_name": "الصندوق / النقدية", "debit": grand_total, "credit": 0.0},
            {"account_id": 4010, "account_name": "إيرادات مبيعات المنتجات والخدمات", "debit": 0.0, "credit": subtotal},
            {"account_id": 2200, "account_name": "ضريبة القيمة المضافة المستحقة (مبيعات)", "debit": 0.0, "credit": vat_amount}
        ]
    }
    journal_entries_db.append(sales_journal)

    cogs_journal = {
        "id": len(journal_entries_db) + 1,
        "ref": f"COGS-REF-{inv_id}",
        "description": f"إثبات تكلفة البضاعة المباعة للفاتورة #{inv_id}",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lines": [
            {"account_id": 5010, "account_name": "تكلفة البضاعة المباعة (COGS)", "debit": total_cost, "credit": 0.0},
            {"account_id": 1200, "account_name": "مخزون البضائع", "debit": 0.0, "credit": total_cost}
        ]
    }
    journal_entries_db.append(cogs_journal)

    invoice_record = {
        "id": inv_id,
        "invoice_number": f"INV-{datetime.now().strftime('%Y%m%d')}-{inv_id:04d}",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer": customer,
        "employee": employee,
        "branch": branch,
        "payment_method": req.payment_method,
        "items": processed_items,
        "subtotal": subtotal,
        "vat_amount": vat_amount,
        "grand_total": grand_total,
        "total_cost": total_cost,
        "commission_earned": commission_earned
    }
    invoices_db.append(invoice_record)

    return {"message": "تم إصدار الفاتورة وتوليد القيود المحاسبية بنجاح", "invoice": invoice_record}

@app.get("/api/reports/summary")
def get_financial_reports():
    total_sales_subtotal = sum(i["subtotal"] for i in invoices_db)
    total_sales_vat = sum(i["vat_amount"] for i in invoices_db)
    total_cogs = sum(i["total_cost"] for i in invoices_db)
    total_purchase_vat = sum(p["vat_amount"] for p in purchases_db)

    return {
        "vat_report": {
            "output_vat_sales": total_sales_vat,
            "input_vat_purchases": total_purchase_vat,
            "net_vat_payable": total_sales_vat - total_purchase_vat
        },
        "profit_report": {
            "total_sales": total_sales_subtotal,
            "total_cost_cogs": total_cogs,
            "gross_profit": total_sales_subtotal - total_cogs
        }
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
