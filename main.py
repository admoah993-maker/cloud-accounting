from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os
import uvicorn

app = FastAPI(
    title="نظام ERP المحاسبي السحابي الاحترافي",
    description="نظام إدارة مؤسسي شامل مع مفاهيم الفوترة الإلكترونية، إدارة المخزون، والقيود الآلية المزدوجة.",
    version="4.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# قواعد البيانات في الذاكرة (In-Memory Enterprise DB)
accounts_db = [
    {"id": 1010, "name": "الصندوق / النقدية", "type": "أصول متداولة"},
    {"id": 1020, "name": "حساب البنك الرئيسي", "type": "أصول متداولة"},
    {"id": 1100, "name": "ذمم العملاء (المدينون)", "type": "أصول متداولة"},
    {"id": 1200, "name": "مخزون البضائع", "type": "أصول متداولة"},
    {"id": 2010, "name": "ذمم الموردين (الدائنون)", "type": "خصوم متداولة"},
    {"id": 2200, "name": "ضريبة القيمة المضافة المستحقة (15%)", "type": "خصوم متداولة"},
    {"id": 3010, "name": "رأس المال", "type": "حقوق الملكية"},
    {"id": 4010, "name": "إيرادات مبيعات المنتجات", "type": "الإيرادات"},
    {"id": 5010, "name": "تكلفة البضاعة المباعة (COGS)", "type": "تكلفة المبيعات"},
    {"id": 5020, "name": "عمولات مبيعات الموظفين", "type": "مصروفات تشغيلية"}
]

branches_db = [
    {"id": 1, "name": "الفرع الرئيسي - الرياض", "city": "الرياض", "cr_number": "1010000000"},
    {"id": 2, "name": "فرع المنطقة الغربية", "city": "جدة", "cr_number": "4030000000"}
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
        "national_address": "الرياض 12211 - حي العليا - طريق الملك فهد"
    },
    {
        "id": 502, 
        "name": "مؤسسة الأفق للخدمات اللوجستية", 
        "phone": "+966551112233", 
        "branch_id": 2, 
        "tax_number": "300987654300003", 
        "national_address": "جدة 21432 - حي الشاطئ - طريق كورنيش"
    }
]

products_db = [
    {"id": 1001, "name": "خادم سحابي Enterprise Server X1", "price": 4500.0, "cost": 3000.0, "stock": 25, "sku": "SRV-X1"},
    {"id": 1002, "name": "ترخيص برنامج المحاسبة السنوي", "price": 1200.0, "cost": 200.0, "stock": 100, "sku": "SW-ACC-Y1"},
    {"id": 1003, "name": "جهاز طابعة فواتير حرارية ZT", "price": 850.0, "cost": 550.0, "stock": 40, "sku": "HW-PRN-01"}
]

invoices_db = []
journal_entries_db = []

# النماذج الهيكلية (Pydantic Models)
class InvoiceLineItem(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)
    discount: float = Field(default=0.0, ge=0)

class InvoiceCreateRequest(BaseModel):
    customer_id: int
    employee_id: int
    branch_id: int
    payment_method: str  # cash, bank, credit
    vat_rate: float = Field(default=15.0, ge=0)
    items: List[InvoiceLineItem]

# المسارات والـ Endpoints
@app.get("/")
def root():
    return {"status": "online", "system": "Enterprise ERP Engine", "version": "4.5.0"}

@app.get("/api/branches")
def list_branches(): return branches_db

@app.get("/api/employees")
def list_employees(): return employees_db

@app.get("/api/customers")
def list_customers(): return customers_db

@app.get("/api/products")
def list_products(): return products_db

@app.get("/api/accounts")
def list_accounts(): return accounts_db

@app.get("/api/journal-entries")
def list_journals(): return journal_entries_db

@app.get("/api/invoices")
def list_invoices(): return invoices_db

@app.post("/api/invoices")
def create_enterprise_invoice(req: InvoiceCreateRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="لا يمكن إصدار فاتورة بدون عناصر.")

    customer = next((c for c in customers_db if c["id"] == req.customer_id), None)
    employee = next((e for e in employees_db if e["id"] == req.employee_id), None)
    branch = next((b for b in branches_db if b["id"] == req.branch_id), None)

    if not customer or not employee or not branch:
        raise HTTPException(status_code=400, detail="العميل أو الموظف أو الفرع المحدد غير موجود.")

    subtotal = 0.0
    total_cost = 0.0
    processed_items = []

    for item in req.items:
        product = next((p for p in products_db if p["id"] == item.product_id), None)
        if not product:
            raise HTTPException(status_code=400, detail=f"المنتج #{item.product_id} غير مسجل.")
        if product["stock"] < item.quantity:
            raise HTTPException(status_code=400, detail=f"المخزون غير كافٍ للمنتج '{product['name']}'. المتاح: {product['stock']}")

        # تحديث المخزون وحساب التكاليف والخصم
        product["stock"] -= item.quantity
        line_price = (product["price"] * item.quantity) - item.discount
        line_cost = product["cost"] * item.quantity

        subtotal += line_price
        total_cost += line_cost

        processed_items.append({
            "product_id": product["id"],
            "sku": product["sku"],
            "name": product["name"],
            "unit_price": product["price"],
            "quantity": item.quantity,
            "discount": item.discount,
            "net_total": line_price
        })

    vat_amount = subtotal * (req.vat_rate / 100.0)
    grand_total = subtotal + vat_amount
    commission_earned = subtotal * (employee["commission_rate"] / 100.0)

    # تحديد الحساب المدين
    payment_map = {
        "cash": (1010, "نقداً - الصندوق"),
        "bank": (1020, "مدفوعات شبكة / تحويل بنكي"),
        "credit": (1100, "آجل - حساب العميل")
    }
    debit_acc_id, pay_label = payment_map.get(req.payment_method, (1010, "نقداً"))

    # 1. القيد المحاسبي المزدوج الرئيسي للمبيعات
    inv_id = len(invoices_db) + 1
    journal_entry = {
        "id": len(journal_entries_db) + 1,
        "ref": f"INV-REF-{inv_id}",
        "description": f"إثبات فاتورة مبيعات #{inv_id} للعميل ({customer['name']}) - طريقة الدفع: {pay_label}",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lines": [
            {"account_id": debit_acc_id, "account_name": pay_label, "debit": grand_total, "credit": 0.0},
            {"account_id": 4010, "account_name": "إيرادات المبيعات", "debit": 0.0, "credit": subtotal},
            {"account_id": 2200, "account_name": "ضريبة القيمة المضافة (15%)", "debit": 0.0, "credit": vat_amount}
        ]
    }
    journal_entries_db.append(journal_entry)

    # 2. قيد إثبات تكلفة البضاعة المباعة (COGS Entry)
    cogs_entry = {
        "id": len(journal_entries_db) + 1,
        "ref": f"COGS-REF-{inv_id}",
        "description": f"إثبات تكلفة البضاعة المباعة للفاتورة #{inv_id}",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lines": [
            {"account_id": 5010, "account_name": "تكلفة البضاعة المباعة", "debit": total_cost, "credit": 0.0},
            {"account_id": 1200, "account_name": "مخزون البضائع", "debit": 0.0, "credit": total_cost}
        ]
    }
    journal_entries_db.append(cogs_entry)

    # 3. حفظ الفاتورة الإلكترونية الشاملة
    invoice_record = {
        "id": inv_id,
        "invoice_number": f"INV-{datetime.now().strftime('%Y%m%d')}-{inv_id:04d}",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer": customer,
        "employee": employee,
        "branch": branch,
        "payment_method": req.payment_method,
        "payment_label": pay_label,
        "items": processed_items,
        "subtotal": subtotal,
        "vat_amount": vat_amount,
        "grand_total": grand_total,
        "commission_earned": commission_earned,
        "journal_entry_id": journal_entry["id"],
        "cogs_entry_id": cogs_entry["id"]
    }
    invoices_db.append(invoice_record)

    return {
        "status": "success",
        "message": "تم إصدَار الفاتورة الإلكترونية وترحيل القيود المحاسبية وتعديل رصيد المخزون بنجاح.",
        "invoice": invoice_record
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
