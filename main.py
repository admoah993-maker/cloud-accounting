from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os
import uvicorn

app = FastAPI(
    title="نظام ERP المحاسبي السحابي - الشامل والتقارير",
    description="إدارة الشجرة المحاسبية، الفواتير، المشتريات، تقارير الضريبة، وعمولات الموظفين والعملاء.",
    version="6.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. الشجرة المحاسبية الكاملة (Chart of Accounts)
accounts_db = [
    # الأصول
    {"id": 1000, "name": "الأصول المتداولة", "type": "أصول"},
    {"id": 1010, "name": "الصندوق / النقدية", "type": "أصول"},
    {"id": 1020, "name": "البنوك", "type": "أصول"},
    {"id": 1100, "name": "ذمم العملاء (المدينون)", "type": "أصول"},
    {"id": 1200, "name": "مخزون البضائع", "type": "أصول"},
    {"id": 1300, "name": "مصروفات مدفوعة مقدماً", "type": "أصول"},
    {"id": 1500, "name": "الأصول الثابتة", "type": "أصول"},
    {"id": 1510, "name": "السيارات ووسائط النقل", "type": "أصول"},
    {"id": 1520, "name": "الأثاث والمكتبيات", "type": "أصول"},
    {"id": 1530, "name": "الأجهزة والمعدات التقنية", "type": "أصول"},

    # الخصوم والالتزامات
    {"id": 2000, "name": "الخصوم المتداولة", "type": "خصوم"},
    {"id": 2010, "name": "ذمم الموردين (الدائنون)", "type": "خصوم"},
    {"id": 2200, "name": "ضريبة القيمة المضافة المستحقة (مبيعات)", "type": "خصوم"},
    {"id": 2210, "name": "ضريبة القيمة المضافة القابلة للاسترداد (مشتريات)", "type": "أصول متداولة"},
    {"id": 2300, "name": "رواتب وأجور مستحقة الدفع", "type": "خصوم"},
    {"id": 2500, "name": "الخصوم طويلة الأجل", "type": "خصوم"},
    {"id": 2510, "name": "القروض البنكية طويلة الأجل", "type": "خصوم"},

    # حقوق الملكية
    {"id": 3000, "name": "حقوق الملكية", "type": "حقوق ملكية"},
    {"id": 3010, "name": "رأس المال الأساسي", "type": "حقوق ملكية"},
    {"id": 3020, "name": "الأرباح المبقاة", "type": "حقوق ملكية"},
    {"id": 3030, "name": "مسحوبات شخصية", "type": "حقوق ملكية"},

    # الإيرادات
    {"id": 4000, "name": "الإيرادات", "type": "إيرادات"},
    {"id": 4010, "name": "إيرادات مبيعات المنتجات والخدمات", "type": "إيرادات"},
    {"id": 4020, "name": "إيرادات أخرى متنوعة", "type": "إيرادات"},

    # المصروفات وتكلفة البضاعة
    {"id": 5000, "name": "تكلفة البضاعة المباعة", "type": "مصروفات"},
    {"id": 5010, "name": "تكلفة البضاعة المباعة (COGS)", "type": "مصروفات"},
    {"id": 5100, "name": "المصروفات التشغيلية والإدارية", "type": "مصروفات"},
    {"id": 5110, "name": "مصروف الإيجار", "type": "مصروفات"},
    {"id": 5120, "name": "مصروف الرواتب والأجور", "type": "مصروفات"},
    {"id": 5130, "name": "مصروف الكهرباء والمياه", "type": "مصروفات"},
    {"id": 5140, "name": "مصروف عمولات المبيعات", "type": "مصروفات"},
    {"id": 5150, "name": "مصروف الدعاية والإعلان", "type": "مصروفات"}
]

# 2. الفروع
branches_db = [
    {"id": 1, "name": "الفرع الرئيسي - الرياض", "city": "الرياض"},
    {"id": 2, "name": "فرع جدة", "city": "جدة"}
]

# 3. الموظفين وعمولاتهم
employees_db = [
    {"id": 101, "name": "عبدالله الشمري", "branch_id": 1, "commission_rate": 5.0},
    {"id": 102, "name": "ريما العتيبي", "branch_id": 2, "commission_rate": 6.5}
]

# 4. العملاء (بالرقم الضريبي والعنوان الوطني)
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

# 5. المنتجات والمخزون
products_db = [
    {"id": 1001, "sku": "SRV-X1", "name": "خادم سحابي Enterprise Server X1", "price": 4500.0, "cost": 3000.0, "stock": 25},
    {"id": 1002, "sku": "SW-ACC-Y1", "name": "ترخيص برنامج المحاسبة السنوي", "price": 1200.0, "cost": 200.0, "stock": 100}
]

invoices_db = []
purchases_db = []
journal_entries_db = []

# النماذج (Pydantic Models)
class AccountCreate(BaseModel):
    id: int
    name: str
    type: str

class BranchCreate(BaseModel):
    id: int
    name: str
    city: str

class EmployeeCreate(BaseModel):
    id: int
    name: str
    branch_id: int
    commission_rate: float = Field(..., ge=0)

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

class InvoiceLineItem(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class InvoiceCreateRequest(BaseModel):
    customer_id: int
    employee_id: int
    branch_id: int
    payment_method: str  # cash, bank, credit
    vat_rate: float = Field(default=15.0, ge=0)
    items: List[InvoiceLineItem]

class PurchaseCreateRequest(BaseModel):
    supplier_name: str
    product_id: int
    quantity: int = Field(..., gt=0)
    unit_cost: float = Field(..., gt=0)
    vat_rate: float = Field(default=15.0, ge=0)

# المسارات الأساسية والمرجعية
@app.get("/")
def root():
    return {"status": "online", "message": "نظام ERP المحاسبي الشامل مع التقارير والضرائب يعمل بكفاءة عالية!"}

@app.get("/api/accounts")
def get_accounts(): return accounts_db

@app.post("/api/accounts")
def create_account(acc: AccountCreate):
    accounts_db.append(acc.dict())
    return {"message": "تم إضافة الحساب إلى الشجرة بنجاح"}

@app.get("/api/branches")
def get_branches(): return branches_db

@app.post("/api/branches")
def create_branch(branch: BranchCreate):
    branches_db.append(branch.dict())
    return {"message": "تم إضافة الفرع بنجاح"}

@app.get("/api/employees")
def get_employees(): return employees_db

@app.post("/api/employees")
def create_employee(emp: EmployeeCreate):
    employees_db.append(emp.dict())
    return {"message": "تم إضافة الموظف ونسبة العمولة بنجاح"}

@app.get("/api/customers")
def get_customers(): return customers_db

@app.post("/api/customers")
def create_customer(cust: CustomerCreate):
    customers_db.append(cust.dict())
    return {"message": "تم إضافة العميل بنجاح"}

@app.get("/api/products")
def get_products(): return products_db

@app.post("/api/products")
def create_product(prod: ProductCreate):
    products_db.append(prod.dict())
    return {"message": "تم إضافة المنتج بنجاح"}

@app.get("/api/journal-entries")
def get_journals(): return journal_entries_db

@app.get("/api/invoices")
def get_invoices(): return invoices_db

@app.get("/api/purchases")
def get_purchases(): return purchases_db

# تسجيل مشتريات وضريبة مشتريات
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
    return {"message": "تم تسجل المشتريات واحتساب الضريبة وتحديث المخزون بنجاح", "purchase": purchase_record}

# محرك الفوترة والترحيل التلقائي للمبيعات
@app.post("/api/invoices")
def create_invoice(req: InvoiceCreateRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="الفاتورة فارغة ولا تحتوي على منتجات.")

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
        if not product:
            raise HTTPException(status_code=400, detail=f"المنتج رقم #{item.product_id} غير موجود.")
        if product["stock"] < item.quantity:
            raise HTTPException(status_code=400, detail=f"الكمية غير كافية للمنتج {product['name']}. المتاح: {product['stock']}")

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

    payment_map = {
        "cash": (1010, "الصندوق / النقدية"),
        "bank": (1020, "البنوك"),
        "credit": (1100, "ذمم العملاء")
    }
    debit_acc_id, debit_acc_name = payment_map.get(req.payment_method, (1010, "الصندوق"))

    inv_id = len(invoices_db) + 1
    sales_journal = {
        "id": len(journal_entries_db) + 1,
        "ref": f"INV-REF-{inv_id}",
        "description": f"إثبات فاتورة مبيعات رقم #{inv_id} للعميل ({customer['name']})",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lines": [
            {"account_id": debit_acc_id, "account_name": debit_acc_name, "debit": grand_total, "credit": 0.0},
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
        "commission_earned": commission_earned,
        "sales_journal_id": sales_journal["id"],
        "cogs_journal_id": cogs_journal["id"]
    }
    invoices_db.append(invoice_record)

    return {
        "status": "success",
        "message": "تم إصدار الفاتورة وتحديث المخزون وترحيل القيود بنجاح!",
        "invoice": invoice_record
    }

# 📊 مسارات التقارير الضريبية، أداء الموظفين، وحسابات العملاء
@app.get("/api/reports/summary")
def get_financial_reports():
    total_sales_subtotal = sum(i["subtotal"] for i in invoices_db)
    total_sales_vat = sum(i["vat_amount"] for i in invoices_db)
    total_cogs = sum(i["total_cost"] for i in invoices_db)
    
    total_purchase_vat = sum(p["vat_amount"] for p in purchases_db)
    net_vat_due = total_sales_vat - total_purchase_vat
    gross_profit = total_sales_subtotal - total_cogs

    employee_performance = {}
    for emp in employees_db:
        emp_invoices = [i for i in invoices_db if i["employee"]["id"] == emp["id"]]
        emp_sales = sum(i["subtotal"] for i in emp_invoices)
        emp_commission = sum(i["commission_earned"] for i in emp_invoices)
        employee_performance[emp["name"]] = {
            "total_sales": emp_sales,
            "invoices_count": len(emp_invoices),
            "commission_earned": emp_commission,
            "rate": emp["commission_rate"]
        }

    customer_statement = {}
    for cust in customers_db:
        cust_invoices = [i for i in invoices_db if i["customer"]["id"] == cust["id"]]
        cust_total_purchases = sum(i["grand_total"] for i in cust_invoices)
        customer_statement[cust["name"]] = {
            "tax_number": cust["tax_number"],
            "national_address": cust["national_address"],
            "total_invoices": len(cust_invoices),
            "total_spent": cust_total_purchases
        }

    return {
        "vat_report": {
            "output_vat_sales": total_sales_vat,
            "input_vat_purchases": total_purchase_vat,
            "net_vat_payable": net_vat_due
        },
        "profit_report": {
            "total_sales": total_sales_subtotal,
            "total_cost_cogs": total_cogs,
            "gross_profit": gross_profit
        },
        "employees_report": employee_performance,
        "customers_report": customer_statement
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
