from flask import Flask, render_template_string, request, jsonify
import os
import json

app = Flask(__name__)

DB_FILE = "erp_database.json"

# واجهة HTML والـ JavaScript المتكاملة داخل السيرفر
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام ERP المحاسبي السحابي - العنوان الوطني وقوالب الفواتير</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style> 
        body { font-family: 'Cairo', sans-serif; } 
        @media print {
            body * { visibility: hidden; }
            #printableInvoice, #printableInvoice * { visibility: visible; }
            #printableInvoice { position: absolute; left: 0; top: 0; width: 100%; }
            .no-print { display: none !important; }
        }
        .template-card { transition: all 0.25s ease-in-out; }
        .template-card:hover { transform: translateY(-4px); }
        .template-selected {
            border-color: #4f46e5 !important;
            background-color: #f5f3ff !important;
            box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.15) !important;
        }
    </style>
</head>
<body class="bg-slate-100 text-slate-800 min-h-screen flex flex-col">

    <!-- 1. شاشة تسجيل الدخول -->
    <div id="loginSection" class="fixed inset-0 bg-slate-900 bg-opacity-95 z-50 flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl border border-slate-200">
            <div class="text-center mb-6">
                <div class="inline-block bg-indigo-600 text-white p-4 rounded-2xl shadow-lg mb-3 text-2xl">🔐</div>
                <h2 class="text-2xl font-extrabold text-slate-900">تسجيل الدخول للنظام السحابي</h2>
                <p class="text-xs text-slate-500 mt-1">أدخل بيانات الحساب للوصول إلى لوحة التحكم بحسب صلاحياتك</p>
            </div>

            <form onsubmit="handleLogin(event)" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">اسم المستخدم</label>
                    <input type="text" id="loginUsername" required placeholder="أدخل اسم المستخدم" class="w-full border border-slate-300 p-3 rounded-xl text-sm focus:outline-none focus:border-indigo-600">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">كلمة المرور</label>
                    <input type="password" id="loginPassword" required placeholder="••••••••" class="w-full border border-slate-300 p-3 rounded-xl text-sm focus:outline-none focus:border-indigo-600">
                </div>
                <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 rounded-xl text-sm shadow-lg transition">دخول النظام 🚀</button>
            </form>

            <div class="mt-6 pt-4 border-t text-xs text-slate-500">
                <p class="font-bold text-slate-700 mb-2">💡 الحسابات الافتراضية للتجربة:</p>
                <div class="space-y-1 bg-slate-50 p-3 rounded-xl border text-slate-600 font-mono">
                    <div>👑 <b>مدير النظام:</b> admin / 123</div>
                    <div>🧮 <b>محاسب:</b> accountant / 123</div>
                    <div>🛒 <b>مسؤول مبيعات:</b> sales / 123</div>
                </div>
            </div>
        </div>
    </div>

    <!-- 2. الواجهة الرئيسية للبرنامج -->
    <div id="mainApp" class="hidden min-h-screen flex flex-col">
        
        <header class="bg-slate-900 text-white shadow-xl p-4 flex flex-wrap justify-between items-center no-print">
            <div class="flex items-center space-x-3 space-x-reverse">
                <span class="text-2xl">⚡</span>
                <div>
                    <h1 id="headerCompanyName" class="text-lg font-bold">نظام ERP السحابي المطور</h1>
                    <p id="headerCompanyDetails" class="text-xs text-indigo-300">إدارة الفواتير، العنوان الوطني، ومعرض القوالب</p>
                </div>
            </div>
            
            <div class="flex items-center space-x-4 space-x-reverse mt-2 sm:mt-0">
                <div class="bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-700 text-xs">
                    <span class="text-slate-400">المستخدم:</span>
                    <span id="currentUserDisplay" class="font-bold text-indigo-300 mr-1"></span>
                    <span id="currentRoleDisplay" class="bg-indigo-600 text-white px-2 py-0.5 rounded text-[10px] font-bold mr-1"></span>
                </div>
                <button onclick="handleLogout()" class="bg-rose-600 hover:bg-rose-700 text-white px-3 py-1.5 rounded-xl text-xs font-bold transition shadow">تسجيل الخروج 🚪</button>
            </div>
        </header>

        <nav class="bg-white border-b shadow-sm sticky top-0 z-20 no-print">
            <div class="container mx-auto px-4 flex overflow-x-auto space-x-2 space-x-reverse py-2">
                <button id="nav-reports" onclick="switchTab('reports', this)" class="tab-btn px-4 py-2 rounded-xl font-bold text-sm text-indigo-600 bg-indigo-50">📈 التقارير والضرائب</button>
                <button id="nav-journals" onclick="switchTab('journals', this)" class="tab-btn px-4 py-2 rounded-xl font-bold text-sm text-slate-600 hover:bg-slate-100">📖 دفتر القيود اليومية</button>
                <button id="nav-invoices" onclick="switchTab('invoices', this)" class="tab-btn px-4 py-2 rounded-xl font-bold text-sm text-slate-600 hover:bg-slate-100">🧾 المبيعات بالفواتير</button>
                <button id="nav-purchases" onclick="switchTab('purchases', this)" class="tab-btn px-4 py-2 rounded-xl font-bold text-sm text-slate-600 hover:bg-slate-100">📥 المشتريات</button>
                <button id="nav-customers" onclick="switchTab('customers', this)" class="tab-btn px-4 py-2 rounded-xl font-bold text-sm text-slate-600 hover:bg-slate-100">👥 العملاء والعنوان الوطني</button>
                <button id="nav-employees" onclick="switchTab('employees', this)" class="tab-btn px-4 py-2 rounded-xl font-bold text-sm text-slate-600 hover:bg-slate-100">👔 الموظفون وعمولاتهم</button>
                <button id="nav-products" onclick="switchTab('products', this)" class="tab-btn px-4 py-2 rounded-xl font-bold text-sm text-slate-600 hover:bg-slate-100">📦 المنتجات والمخزون</button>
                <button id="nav-settings" onclick="switchTab('settings', this)" class="tab-btn px-4 py-2 rounded-xl font-bold text-sm text-slate-600 hover:bg-slate-100">🎨 معرض وقوالب الفواتير</button>
            </div>
        </nav>

        <main class="container mx-auto px-4 py-6 flex-grow no-print">
            
            <!-- 1. التقارير -->
            <section id="sec-reports" class="app-section space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="bg-white p-6 rounded-2xl shadow-sm border">
                        <h3 class="font-bold text-indigo-900 mb-3">📋 إقرار ضريبة القيمة المضافة</h3>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between"><span>ضريبة المبيعات:</span><span id="vatSales" class="font-bold text-indigo-600">0.00 ر.س</span></div>
                            <div class="flex justify-between"><span>ضريبة المشتريات:</span><span id="vatPurchases" class="font-bold text-amber-600">0.00 ر.س</span></div>
                            <hr class="my-2">
                            <div class="flex justify-between font-bold text-base text-emerald-700"><span>الصافي المستحق للدولة:</span><span id="vatNet">0.00 ر.س</span></div>
                        </div>
                    </div>

                    <div class="bg-white p-6 rounded-2xl shadow-sm border">
                        <h3 class="font-bold text-indigo-900 mb-3">💰 تقرير مجمل الأرباح</h3>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between"><span>إجمالي الإيرادات:</span><span id="repSales" class="font-bold text-indigo-600">0.00 ر.س</span></div>
                            <div class="flex justify-between"><span>تكلفة المبيعات (COGS):</span><span id="repCogs" class="font-bold text-rose-600">0.00 ر.س</span></div>
                            <hr class="my-2">
                            <div class="flex justify-between font-bold text-base text-indigo-700"><span>مجمل الربح التجاري:</span><span id="repProfit">0.00 ر.س</span></div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- 2. القيود اليومية -->
            <section id="sec-journals" class="app-section hidden space-y-6">
                <div class="bg-white p-6 rounded-2xl shadow-sm border">
                    <h3 class="font-bold text-lg text-slate-900 mb-4">📖 سجل القيود اليومية المرحلة (القيود المزدوجة)</h3>
                    <div id="journalsContainer" class="space-y-4"></div>
                </div>
            </section>

            <!-- 3. المبيعات وإصدار الفواتير -->
            <section id="sec-invoices" class="app-section hidden space-y-6">
                <div class="bg-white p-6 rounded-2xl shadow-sm border space-y-4">
                    <h3 class="font-bold text-lg text-slate-900">🧾 إصدار فاتورة مبيعات جديدة</h3>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label class="block text-xs font-bold text-slate-600 mb-1">العميل</label>
                            <select id="invCustomerId" class="w-full border p-2.5 rounded-xl text-sm bg-white"></select>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-600 mb-1">الموظف المسؤول</label>
                            <select id="invEmployeeId" class="w-full border p-2.5 rounded-xl text-sm bg-white"></select>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-600 mb-1">المنتج</label>
                            <select id="invProductId" class="w-full border p-2.5 rounded-xl text-sm bg-white"></select>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label class="block text-xs font-bold text-slate-600 mb-1">الكمية</label>
                            <input type="number" id="invQuantity" value="1" min="1" class="w-full border p-2.5 rounded-xl text-sm">
                        </div>
                    </div>

                    <div>
                        <label class="block text-xs font-bold text-slate-700 mb-2">اختر تصميم الفاتورة لهذه العملية:</label>
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-3" id="quickTemplatePicker">
                            
                            <div id="qCard-modern" class="border rounded-xl p-3 bg-slate-50 border-slate-200 flex flex-col justify-between space-y-2">
                                <div onclick="selectQuickTemplate('modern')" class="cursor-pointer text-center text-xs font-bold">
                                    🏙️ النمط العصري
                                </div>
                                <button type="button" onclick="previewSampleTemplate('modern')" class="bg-indigo-100 hover:bg-indigo-200 text-indigo-800 text-[10px] font-bold py-1 rounded-lg transition">👁️ معاينة القالب</button>
                            </div>

                            <div id="qCard-classic" class="border rounded-xl p-3 bg-slate-50 border-slate-200 flex flex-col justify-between space-y-2">
                                <div onclick="selectQuickTemplate('classic')" class="cursor-pointer text-center text-xs font-bold">
                                    📜 النمط الكلاسيكي
                                </div>
                                <button type="button" onclick="previewSampleTemplate('classic')" class="bg-slate-200 hover:bg-slate-300 text-slate-800 text-[10px] font-bold py-1 rounded-lg transition">👁️ معاينة القالب</button>
                            </div>

                            <div id="qCard-tax" class="border rounded-xl p-3 bg-slate-50 border-slate-200 flex flex-col justify-between space-y-2">
                                <div onclick="selectQuickTemplate('tax')" class="cursor-pointer text-center text-xs font-bold">
                                    🏢 النمط الضريبي
                                </div>
                                <button type="button" onclick="previewSampleTemplate('tax')" class="bg-emerald-100 hover:bg-emerald-200 text-emerald-800 text-[10px] font-bold py-1 rounded-lg transition">👁️ معاينة القالب</button>
                            </div>

                            <div id="qCard-thermal" class="border rounded-xl p-3 bg-slate-50 border-slate-200 flex flex-col justify-between space-y-2">
                                <div onclick="selectQuickTemplate('thermal')" class="cursor-pointer text-center text-xs font-bold">
                                    🧾 الحراري / الكاشير
                                </div>
                                <button type="button" onclick="previewSampleTemplate('thermal')" class="bg-amber-100 hover:bg-amber-200 text-amber-800 text-[10px] font-bold py-1 rounded-lg transition">👁️ معاينة القالب</button>
                            </div>

                        </div>
                        <input type="hidden" id="invSelectedTemplate" value="modern">
                    </div>

                    <button onclick="createInvoice()" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 px-8 rounded-xl text-sm shadow-md transition">إصدار الفاتورة وتوليد معاينة الطباعة 🖨️</button>
                </div>

                <div class="bg-white p-6 rounded-2xl shadow-sm border">
                    <h3 class="font-bold text-lg mb-4">سجل الفواتير الصادرة</h3>
                    <div id="invoicesListTable" class="space-y-3"></div>
                </div>
            </section>

            <!-- 4. المشتريات -->
            <section id="sec-purchases" class="app-section hidden space-y-6">
                <div class="bg-white p-6 rounded-2xl shadow-sm border">
                    <h3 class="font-bold text-lg mb-4">تسجيل فاتورة مشتريات</h3>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                        <input type="text" id="purSupplier" placeholder="اسم المورد" class="border p-2.5 rounded-xl text-sm">
                        <select id="purProductId" class="border p-2.5 rounded-xl text-sm bg-white"></select>
                        <input type="number" id="purQuantity" placeholder="الكمية" class="border p-2.5 rounded-xl text-sm">
                        <input type="number" step="0.01" id="purUnitCost" placeholder="سعر التكلفة" class="border p-2.5 rounded-xl text-sm">
                    </div>
                    <button onclick="createPurchase()" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 px-6 rounded-xl text-sm">تسجيل المشتريات وترحيل القيود</button>
                </div>
            </section>

            <!-- 5. العملاء والعنوان الوطني التفصيلي -->
            <section id="sec-customers" class="app-section hidden space-y-6">
                <div class="bg-white p-6 rounded-2xl shadow-sm border space-y-4">
                    <h3 class="font-bold text-lg text-slate-900">👥 إضافة عميل جديد وبيانات العنوان الوطني</h3>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <input type="text" id="custName" placeholder="اسم العميل أو الشركة *" required class="border p-2.5 rounded-xl text-sm">
                        <input type="text" id="custPhone" placeholder="رقم الجوال" class="border p-2.5 rounded-xl text-sm">
                        <input type="text" id="custTaxNumber" placeholder="الرقم الضريبي" class="border p-2.5 rounded-xl text-sm">
                    </div>

                    <div class="bg-slate-50 p-4 rounded-xl border space-y-3">
                        <h4 class="font-bold text-xs text-indigo-900">📍 بيانات العنوان الوطني للعميل:</h4>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                            <div>
                                <label class="block font-bold text-slate-600 mb-1">الدولة</label>
                                <input type="text" id="custCountry" value="المملكة العربية السعودية" class="w-full border p-2 rounded-lg bg-white">
                            </div>
                            <div>
                                <label class="block font-bold text-slate-600 mb-1">المنطقة / المحافظة</label>
                                <input type="text" id="custRegion" placeholder="مثال: الرياض" class="w-full border p-2 rounded-lg bg-white">
                            </div>
                            <div>
                                <label class="block font-bold text-slate-600 mb-1">الحي</label>
                                <input type="text" id="custDistrict" placeholder="مثال: حي العليا" class="w-full border p-2 rounded-lg bg-white">
                            </div>
                            <div>
                                <label class="block font-bold text-slate-600 mb-1">رقم المبنى</label>
                                <input type="text" id="custBuildingNo" placeholder="مثال: 7421" class="w-full border p-2 rounded-lg bg-white">
                            </div>
                            <div>
                                <label class="block font-bold text-slate-600 mb-1">الرمز البريدي / رقم المنطقة</label>
                                <input type="text" id="custPostalCode" placeholder="مثال: 12211" class="w-full border p-2 rounded-lg bg-white">
                            </div>
                        </div>
                    </div>

                    <button onclick="addNewCustomer()" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 px-6 rounded-xl text-sm shadow">حفظ العميل والعنوان الوطني</button>
                </div>

                <div class="bg-white p-6 rounded-2xl shadow-sm border">
                    <h3 class="font-bold text-lg mb-4">قائمة العملاء والعناوين الوطنية</h3>
                    <div class="overflow-x-auto">
                        <table class="w-full text-right text-sm">
                            <thead>
                                <tr class="bg-slate-100 border-b text-slate-700">
                                    <th class="p-3">الاسم</th>
                                    <th class="p-3">الجوال</th>
                                    <th class="p-3">الرقم الضريبي</th>
                                    <th class="p-3">العنوان الوطني التفصيلي</th>
                                </tr>
                            </thead>
                            <tbody id="customersTable" class="divide-y"></tbody>
                        </table>
                    </div>
                </div>
            </section>

            <!-- 6. الموظفون -->
            <section id="sec-employees" class="app-section hidden space-y-6">
                <div class="bg-white p-6 rounded-2xl shadow-sm border">
                    <h3 class="font-bold text-lg mb-4">إضافة موظف جديد وتحديد الصلاحيات والعمولة</h3>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                        <input type="text" id="empName" placeholder="اسم الموظف" class="border p-2.5 rounded-xl text-sm">
                        <input type="text" id="empUsername" placeholder="اسم المستخدم للدخول" class="border p-2.5 rounded-xl text-sm">
                        <input type="password" id="empPassword" placeholder="كلمة المرور" class="border p-2.5 rounded-xl text-sm">
                        <select id="empRole" class="border p-2.5 rounded-xl text-sm bg-white">
                            <option value="sales">مسؤول مبيعات / كاشير</option>
                            <option value="accountant">محاسب</option>
                            <option value="admin">مدير نظام كامل</option>
                        </select>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                        <input type="number" step="0.1" id="empCommission" placeholder="نسبة العمولة (%)" class="border p-2.5 rounded-xl text-sm">
                    </div>
                    <button onclick="addNewEmployee()" class="bg-indigo-600 text-white font-bold py-2 px-6 rounded-xl text-sm">حفظ الموظف والحساب</button>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow-sm border">
                    <h3 class="font-bold text-lg mb-4">قائمة الموظفين والصلاحيات</h3>
                    <table class="w-full text-right text-sm">
                        <thead><tr class="bg-slate-100 border-b"><th class="p-2">اسم الموظف</th><th class="p-2">اسم المستخدم</th><th class="p-2">الدور/الصلاحية</th><th class="p-2">نسبة العمولة</th></tr></thead>
                        <tbody id="employeesTable"></tbody>
                    </table>
                </div>
            </section>

            <!-- 7. المنتجات -->
            <section id="sec-products" class="app-section hidden space-y-6">
                <div class="bg-white p-6 rounded-2xl shadow-sm border">
                    <h3 class="font-bold text-lg mb-4">إضافة منتج جديد</h3>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                        <input type="text" id="prodName" placeholder="اسم المنتج" class="border p-2.5 rounded-xl text-sm">
                        <input type="number" step="0.01" id="prodPrice" placeholder="سعر البيع" class="border p-2.5 rounded-xl text-sm">
                        <input type="number" step="0.01" id="prodCost" placeholder="التكلفة" class="border p-2.5 rounded-xl text-sm">
                        <input type="number" id="prodStock" placeholder="الرصيد بالمخزن" class="border p-2.5 rounded-xl text-sm">
                    </div>
                    <button onclick="addNewProduct()" class="bg-indigo-600 text-white font-bold py-2 px-6 rounded-xl text-sm">حفظ المنتج</button>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow-sm border">
                    <h3 class="font-bold text-lg mb-4">قائمة المنتجات والمخزون</h3>
                    <table class="w-full text-right text-sm">
                        <thead><tr class="bg-slate-100 border-b"><th class="p-2">الاسم</th><th class="p-2">السعر</th><th class="p-2">التكلفة</th><th class="p-2">المخزون</th></tr></thead>
                        <tbody id="productsTable"></tbody>
                    </table>
                </div>
            </section>

            <!-- 8. معرض القوالب والإعدادات -->
            <section id="sec-settings" class="app-section hidden space-y-8">
                
                <div class="bg-white p-6 rounded-2xl shadow-sm border space-y-4">
                    <div>
                        <h3 class="font-bold text-xl text-slate-900">🎨 معرض قوالب الفواتير واستعراضها</h3>
                        <p class="text-xs text-slate-500 mt-1">يمكنك استعراض معاينة لكل قالب ومعرفة شكل الطباعة قبل تعيينه كقالب افتراضي لمؤسستك</p>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 pt-2">
                        
                        <!-- 1. القالب العصري -->
                        <div id="galCard-modern" class="template-card border-2 border-slate-200 rounded-2xl p-4 bg-white flex flex-col justify-between space-y-4 shadow-sm">
                            <div class="space-y-3">
                                <div class="flex justify-between items-center">
                                    <span class="text-xs font-extrabold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-lg">Modern</span>
                                    <span class="status-badge text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">غير مفعل</span>
                                </div>
                                <div class="border rounded-xl p-3 bg-slate-900 text-white text-[9px] space-y-2 opacity-90">
                                    <div class="flex justify-between font-bold border-b border-slate-700 pb-1">
                                        <span>اسم الشركة</span>
                                        <span>#INV-001</span>
                                    </div>
                                    <div class="bg-slate-800 p-1.5 rounded text-[8px] text-indigo-300">تفاصيل العميل والعنوان الوطني</div>
                                    <div class="text-left font-bold text-emerald-400">100.00 ر.س</div>
                                </div>
                                <h4 class="font-bold text-sm text-slate-800">النمط العصري (Modern)</h4>
                                <p class="text-xs text-slate-500">تصميم كحلي حديث ومظاهر بصرية عالية الوضوح للفواتير الإلكترونية.</p>
                            </div>
                            <div class="space-y-2">
                                <button type="button" onclick="previewSampleTemplate('modern')" class="w-full bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold py-2 rounded-xl text-xs transition">👁️ استعراض ومعاينة القالب</button>
                                <button type="button" onclick="setDefaultTemplate('modern')" class="w-full bg-slate-800 hover:bg-indigo-600 text-white font-bold py-2 rounded-xl text-xs transition">تعيين كافتراضي ✨</button>
                            </div>
                        </div>

                        <!-- 2. القالب الكلاسيكي -->
                        <div id="galCard-classic" class="template-card border-2 border-slate-200 rounded-2xl p-4 bg-white flex flex-col justify-between space-y-4 shadow-sm">
                            <div class="space-y-3">
                                <div class="flex justify-between items-center">
                                    <span class="text-xs font-extrabold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg">Classic</span>
                                    <span class="status-badge text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">غير مفعل</span>
                                </div>
                                <div class="border-2 border-slate-800 rounded-xl p-3 bg-white text-slate-800 text-[9px] space-y-2">
                                    <div class="flex justify-between font-bold border-b border-slate-800 pb-1">
                                        <span>شركة الحلول</span>
                                        <span>فاتورة مبيعات</span>
                                    </div>
                                    <div class="border p-1 text-[8px]">جدول المنتجات والكميات</div>
                                    <div class="text-left font-bold">100.00 ر.س</div>
                                </div>
                                <h4 class="font-bold text-sm text-slate-800">النمط الكلاسيكي (Classic)</h4>
                                <p class="text-xs text-slate-500">إطار رسمي تقليدي وواضح ومناسب للطباعة على الأوراق الرسمية المروسة.</p>
                            </div>
                            <div class="space-y-2">
                                <button type="button" onclick="previewSampleTemplate('classic')" class="w-full bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold py-2 rounded-xl text-xs transition">👁️ استعراض ومعاينة القالب</button>
                                <button type="button" onclick="setDefaultTemplate('classic')" class="w-full bg-slate-800 hover:bg-indigo-600 text-white font-bold py-2 rounded-xl text-xs transition">تعيين كافتراضي ✨</button>
                            </div>
                        </div>

                        <!-- 3. القالب الضريبي -->
                        <div id="galCard-tax" class="template-card border-2 border-slate-200 rounded-2xl p-4 bg-white flex flex-col justify-between space-y-4 shadow-sm">
                            <div class="space-y-3">
                                <div class="flex justify-between items-center">
                                    <span class="text-xs font-extrabold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-lg">ZATCA Tax</span>
                                    <span class="status-badge text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">غير مفعل</span>
                                </div>
                                <div class="border border-emerald-500 rounded-xl p-3 bg-emerald-50 text-emerald-900 text-[9px] space-y-2">
                                    <div class="text-center font-bold bg-emerald-200 p-1 rounded">فاتورة ضريبية مبسطة</div>
                                    <div class="flex justify-between text-[8px]"><span>الرقم الضريبي</span><span>الضريبة: 15%</span></div>
                                    <div class="text-left font-bold text-emerald-800">115.00 ر.س</div>
                                </div>
                                <h4 class="font-bold text-sm text-slate-800">النمط الضريبي المعتمد (Tax)</h4>
                                <p class="text-xs text-slate-500">يركز على حساب تفاصيل الضريبة والـ VAT والعنوان الوطني بدقة متوافقة مع المتطلبات.</p>
                            </div>
                            <div class="space-y-2">
                                <button type="button" onclick="previewSampleTemplate('tax')" class="w-full bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-bold py-2 rounded-xl text-xs transition">👁️ استعراض ومعاينة القالب</button>
                                <button type="button" onclick="setDefaultTemplate('tax')" class="w-full bg-slate-800 hover:bg-indigo-600 text-white font-bold py-2 rounded-xl text-xs transition">تعيين كافتراضي ✨</button>
                            </div>
                        </div>

                        <!-- 4. القالب الحراري -->
                        <div id="galCard-thermal" class="template-card border-2 border-slate-200 rounded-2xl p-4 bg-white flex flex-col justify-between space-y-4 shadow-sm">
                            <div class="space-y-3">
                                <div class="flex justify-between items-center">
                                    <span class="text-xs font-extrabold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-lg">80mm POS</span>
                                    <span class="status-badge text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">غير مفعل</span>
                                </div>
                                <div class="border border-dashed rounded-xl p-3 bg-amber-50/50 text-slate-800 text-[9px] text-center space-y-1 font-mono">
                                    <div class="font-bold">*** إيصال كاشير ***</div>
                                    <div class="text-[8px] text-slate-500">طابعة حرارية 80mm</div>
                                    <div class="border-t border-b border-dashed py-0.5 font-bold">100.00 ر.س</div>
                                </div>
                                <h4 class="font-bold text-sm text-slate-800">إيصال كاشير حراري (Thermal)</h4>
                                <p class="text-xs text-slate-500">مخصص لطابعات الفواتير الصغيرة (POS Receipts) السريعة في نقاط البيع.</p>
                            </div>
                            <div class="space-y-2">
                                <button type="button" onclick="previewSampleTemplate('thermal')" class="w-full bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold py-2 rounded-xl text-xs transition">👁️ استعراض ومعاينة القالب</button>
                                <button type="button" onclick="setDefaultTemplate('thermal')" class="w-full bg-slate-800 hover:bg-indigo-600 text-white font-bold py-2 rounded-xl text-xs transition">تعيين كافتراضي ✨</button>
                            </div>
                        </div>

                    </div>
                </div>

                <div class="bg-white p-6 rounded-2xl shadow-sm border max-w-3xl space-y-6">
                    <h3 class="font-bold text-lg text-slate-900 border-b pb-2">🏢 إعدادات بيانات الشركة والمؤسسة</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                            <label class="font-bold block text-slate-700 mb-1">اسم الشركة أو المؤسسة</label>
                            <input type="text" id="setCompanyName" class="w-full border p-2.5 rounded-xl text-sm">
                        </div>
                        <div>
                            <label class="font-bold block text-slate-700 mb-1">الرقم الضريبي</label>
                            <input type="text" id="setCompanyTax" class="w-full border p-2.5 rounded-xl text-sm">
                        </div>
                        <div>
                            <label class="font-bold block text-slate-700 mb-1">رقم الهاتف</label>
                            <input type="text" id="setCompanyPhone" class="w-full border p-2.5 rounded-xl text-sm">
                        </div>
                        <div>
                            <label class="font-bold block text-slate-700 mb-1">العنوان</label>
                            <input type="text" id="setCompanyAddress" class="w-full border p-2.5 rounded-xl text-sm">
                        </div>
                    </div>

                    <h3 class="font-bold text-lg text-slate-900 border-b pb-2 pt-2">⚙️ إعدادات ميزات النظام</h3>
                    <div class="space-y-4 text-sm">
                        <div class="flex justify-between items-center p-3 bg-slate-50 rounded-xl border">
                            <div>
                                <span class="font-bold block text-slate-800">حساب ضريبة القيمة المضافة (VAT)</span>
                                <span class="text-xs text-slate-500">تفعيل أو تعطيل حساب ضريبة المبيعات والمشتريات</span>
                            </div>
                            <input type="checkbox" id="settingVat" class="w-5 h-5 accent-indigo-600">
                        </div>

                        <div class="flex justify-between items-center p-3 bg-slate-50 rounded-xl border">
                            <div>
                                <span class="font-bold block text-slate-800">توليد القيود المحاسبية اليومية المزدوجة آلياً</span>
                                <span class="text-xs text-slate-500">إنشاء القيود بمجرد حفظ الفواتير والمشتريات</span>
                            </div>
                            <input type="checkbox" id="settingJournals" class="w-5 h-5 accent-indigo-600">
                        </div>

                        <div class="flex justify-between items-center p-3 bg-slate-50 rounded-xl border">
                            <div>
                                <span class="font-bold block text-slate-800">حساب وتنفيذ عمولات الموظفين</span>
                                <span class="text-xs text-slate-500">احتساب نسب أرباح الموظفين بناءً على مبيعاتهم</span>
                            </div>
                            <input type="checkbox" id="settingCommissions" class="w-5 h-5 accent-indigo-600">
                        </div>

                        <div class="p-3 bg-slate-50 rounded-xl border space-y-2">
                            <label class="font-bold block text-slate-800">نسبة ضريبة القيمة المضافة الافتراضية (%)</label>
                            <input type="number" step="0.1" id="settingVatRate" class="border p-2 rounded-xl text-sm w-32">
                        </div>
                    </div>

                    <button onclick="updateSettings()" class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2.5 px-6 rounded-xl text-sm shadow">حفظ كافة الإعدادات والبيانات</button>
                </div>
            </section>

        </main>
    </div>

    <!-- 3. نافذة معاينة واستعراض الفاتورة -->
    <div id="invoiceModal" class="fixed inset-0 bg-slate-900 bg-opacity-80 z-50 hidden flex items-center justify-center p-4">
        <div class="bg-white rounded-3xl max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl relative">
            <div class="flex justify-between items-center mb-4 no-print border-b pb-3">
                <h3 class="font-bold text-slate-800 text-lg">🖨️ معاينة واستعراض تصميم الفاتورة</h3>
                <div class="space-x-2 space-x-reverse">
                    <button onclick="window.print()" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-4 py-2 rounded-xl text-xs">طباعة الفاتورة 🖨️</button>
                    <button onclick="closeInvoiceModal()" class="bg-slate-200 hover:bg-slate-300 text-slate-700 font-bold px-4 py-2 rounded-xl text-xs">إغلاق ✖️</button>
                </div>
            </div>
            <div id="printableInvoice" class="bg-white p-4"></div>
        </div>
    </div>

    <script>
        let db = JSON.parse(localStorage.getItem('erp_db')) || {
            users: [
                { username: "admin", password: "123", name: "مدير النظام", role: "admin" },
                { username: "accountant", password: "123", name: "المحاسب الرئيسي", role: "accountant" },
                { username: "sales", password: "123", name: "عبدالله الشمري", role: "sales" }
            ],
            settings: {
                companyName: "شركة الحلول المترامية المحدودة",
                companyTax: "310123456700003",
                companyPhone: "+966500000000",
                companyAddress: "الرياض - المملكة العربية السعودية",
                defaultTemplate: "modern",
                vatEnabled: true,
                journalsEnabled: true,
                commissionsEnabled: true,
                vatRate: 15.0
            },
            customers: [{ 
                id: 501, 
                name: "شركة الحلول المتقدمة", 
                phone: "0500000000", 
                tax_number: "310123456700003",
                country: "المملكة العربية السعودية",
                region: "الرياض",
                district: "حي العليا",
                building_no: "7421",
                postal_code: "12211"
            }],
            employees: [
                { id: 101, name: "عبدالله الشمري", username: "sales", role: "sales", commission_rate: 5.0 },
                { id: 102, name: "المحاسب الرئيسي", username: "accountant", role: "accountant", commission_rate: 0.0 }
            ],
            products: [{ id: 1001, name: "خادم سحابي Enterprise", price: 4500, cost: 3000, stock: 25 }],
            invoices: [],
            purchases: [],
            journals: []
        };

        if(!db.settings) {
            db.settings = { companyName: "مؤسستي التجارية", companyTax: "", companyPhone: "", companyAddress: "", defaultTemplate: "modern", vatEnabled: true, journalsEnabled: true, commissionsEnabled: true, vatRate: 15.0 };
        }

        let currentUser = JSON.parse(sessionStorage.getItem('erp_session')) || null;

        function saveDb() { localStorage.setItem('erp_db', JSON.stringify(db)); }

        function handleLogin(event) {
            if (event) event.preventDefault();
            
            let u = document.getElementById('loginUsername').value.trim();
            let p = document.getElementById('loginPassword').value.trim();

            if (!u || !p) {
                alert('يرجى إدخال اسم المستخدم وكلمة المرور');
                return;
            }

            let found = db.users.find(user => user.username.toLowerCase() === u.toLowerCase() && user.password === p);

            if (found) {
                currentUser = found;
                sessionStorage.setItem('erp_session', JSON.stringify(currentUser));
                initSessionUI();
            } else {
                alert('اسم المستخدم أو كلمة المرور غير صحيحة!\nجرب: admin / 123');
            }
        }

        function handleLogout() {
            sessionStorage.removeItem('erp_session');
            currentUser = null;
            document.getElementById('loginSection').classList.remove('hidden');
            document.getElementById('mainApp').classList.add('hidden');
        }

        function initSessionUI() {
            if (!currentUser) {
                document.getElementById('loginSection').classList.remove('hidden');
                document.getElementById('mainApp').classList.add('hidden');
                return;
            }

            document.getElementById('loginSection').classList.add('hidden');
            document.getElementById('mainApp').classList.remove('hidden');

            document.getElementById('currentUserDisplay').innerText = currentUser.name;
            let roleName = currentUser.role === 'admin' ? 'مدير نظام' : (currentUser.role === 'accountant' ? 'محاسب' : 'مسؤول مبيعات');
            document.getElementById('currentRoleDisplay').innerText = roleName;

            document.getElementById('headerCompanyName').innerText = db.settings.companyName || "نظام ERP السحابي";
            document.getElementById('headerCompanyDetails').innerText = `الرقم الضريبي: ${db.settings.companyTax || '-'} | هاتف: ${db.settings.companyPhone || '-'}`;

            const navIds = ['reports', 'journals', 'invoices', 'purchases', 'customers', 'employees', 'products', 'settings'];
            navIds.forEach(id => {
                let btn = document.getElementById('nav-' + id);
                if (btn) btn.classList.remove('hidden');
            });

            if (currentUser.role === 'sales') {
                ['reports', 'journals', 'purchases', 'employees', 'products', 'settings'].forEach(id => {
                    let btn = document.getElementById('nav-' + id);
                    if (btn) btn.classList.add('hidden');
                });
                switchTab('invoices', document.getElementById('nav-invoices'));
            } else if (currentUser.role === 'accountant') {
                ['employees', 'settings'].forEach(id => {
                    let btn = document.getElementById('nav-' + id);
                    if (btn) btn.classList.add('hidden');
                });
                switchTab('reports', document.getElementById('nav-reports'));
            } else {
                switchTab('reports', document.getElementById('nav-reports'));
            }

            document.getElementById('setCompanyName').value = db.settings.companyName || '';
            document.getElementById('setCompanyTax').value = db.settings.companyTax || '';
            document.getElementById('setCompanyPhone').value = db.settings.companyPhone || '';
            document.getElementById('setCompanyAddress').value = db.settings.companyAddress || '';

            document.getElementById('settingVat').checked = db.settings.vatEnabled;
            document.getElementById('settingJournals').checked = db.settings.journalsEnabled;
            document.getElementById('settingCommissions').checked = db.settings.commissionsEnabled;
            document.getElementById('settingVatRate').value = db.settings.vatRate;

            selectQuickTemplate(db.settings.defaultTemplate || 'modern');
            updateGalleryUI();
            renderUI();
        }

        function setDefaultTemplate(styleKey) {
            db.settings.defaultTemplate = styleKey;
            saveDb();
            selectQuickTemplate(styleKey);
            updateGalleryUI();
            alert('تم تعيين القالب المختار كقالب افتراضي للفواتير!');
        }

        function selectQuickTemplate(styleKey) {
            document.getElementById('invSelectedTemplate').value = styleKey;
            ['modern', 'classic', 'tax', 'thermal'].forEach(key => {
                let card = document.getElementById('qCard-' + key);
                if(card) {
                    if(key === styleKey) {
                        card.classList.add('border-indigo-600', 'bg-indigo-50', 'text-indigo-700');
                        card.classList.remove('border-slate-200', 'bg-slate-50', 'text-slate-800');
                    } else {
                        card.classList.remove('border-indigo-600', 'bg-indigo-50', 'text-indigo-700');
                        card.classList.add('border-slate-200', 'bg-slate-50', 'text-slate-800');
                    }
                }
            });
        }

        function updateGalleryUI() {
            let currentDef = db.settings.defaultTemplate || 'modern';
            ['modern', 'classic', 'tax', 'thermal'].forEach(key => {
                let gCard = document.getElementById('galCard-' + key);
                if(gCard) {
                    let badge = gCard.querySelector('.status-badge');
                    let btns = gCard.querySelectorAll('button');
                    let defBtn = btns[1];
                    
                    if(key === currentDef) {
                        gCard.classList.add('template-selected');
                        if(badge) {
                            badge.innerText = 'المفعل حالياً ✓';
                            badge.className = 'status-badge text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-indigo-600 text-white';
                        }
                        if(defBtn) defBtn.innerText = 'القالب المعتمد حالياً 👑';
                    } else {
                        gCard.classList.remove('template-selected');
                        if(badge) {
                            badge.innerText = 'غير مفعل';
                            badge.className = 'status-badge text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-500';
                        }
                        if(defBtn) defBtn.innerText = 'تعيين كافتراضي ✨';
                    }
                }
            });
        }

        function previewSampleTemplate(styleKey) {
            let sampleInvoice = {
                id: 999,
                date: new Date().toLocaleString(),
                customerName: "شركة الأعمال المتقدمة",
                customerTax: "310000000000003",
                customerAddressFormatted: "المملكة العربية السعودية، الرياض، حي العليا، مبنى 7421، الرمز البريدي: 12211",
                employeeName: currentUser ? currentUser.name : "مسؤول المبيعات",
                productName: "منتج تجريبي / نموذج استعراض القالب",
                unitPrice: 1000.00,
                quantity: 1,
                subtotal: 1000.00,
                vat_amount: 150.00,
                grand_total: 1150.00,
                total_cost: 700.00
            };
            renderInvoiceTemplate(sampleInvoice, styleKey);
        }

        function updateSettings() {
            db.settings.companyName = document.getElementById('setCompanyName').value;
            db.settings.companyTax = document.getElementById('setCompanyTax').value;
            db.settings.companyPhone = document.getElementById('setCompanyPhone').value;
            db.settings.companyAddress = document.getElementById('setCompanyAddress').value;

            db.settings.vatEnabled = document.getElementById('settingVat').checked;
            db.settings.journalsEnabled = document.getElementById('settingJournals').checked;
            db.settings.commissionsEnabled = document.getElementById('settingCommissions').checked;
            db.settings.vatRate = parseFloat(document.getElementById('settingVatRate').value) || 15.0;
            
            saveDb();
            initSessionUI();
            alert('تم حفظ إعدادات المؤسسة بنجاح!');
        }

        function switchTab(tabId, btnElement) {
            document.querySelectorAll('.app-section').forEach(s => s.classList.add('hidden'));
            const target = document.getElementById('sec-' + tabId);
            if(target) target.classList.remove('hidden');

            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('text-indigo-600', 'bg-indigo-50');
                btn.classList.add('text-slate-600', 'hover:bg-slate-100');
            });
            if(btnElement) {
                btnElement.classList.remove('text-slate-600', 'hover:bg-slate-100');
                btnElement.classList.add('text-indigo-600', 'bg-indigo-50');
            }
            renderUI();
        }

        function formatCustomerAddress(c) {
            if(!c) return '-';
            let parts = [];
            if(c.country) parts.push(c.country);
            if(c.region) parts.push(c.region);
            if(c.district) parts.push(c.district);
            if(c.building_no) parts.push(`مبنى ${c.building_no}`);
            if(c.postal_code) parts.push(`الرمز البريدي/المنطقة ${c.postal_code}`);
            return parts.length > 0 ? parts.join('، ') : 'غير محدد';
        }

        function renderUI() {
            document.getElementById('invCustomerId').innerHTML = db.customers.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
            document.getElementById('invEmployeeId').innerHTML = db.employees.map(e => `<option value="${e.id}">${e.name} (${e.commission_rate}%)</option>`).join('');
            document.getElementById('invProductId').innerHTML = db.products.map(p => `<option value="${p.id}">${p.name} - ${p.price} ر.س</option>`).join('');
            document.getElementById('purProductId').innerHTML = db.products.map(p => `<option value="${p.id}">${p.name}</option>`).join('');

            document.getElementById('customersTable').innerHTML = db.customers.map(c => `
                <tr class="border-b">
                    <td class="p-3 font-bold text-slate-800">${c.name}</td>
                    <td class="p-3">${c.phone || '-'}</td>
                    <td class="p-3 font-mono text-xs">${c.tax_number || '-'}</td>
                    <td class="p-3 text-xs text-slate-600">${formatCustomerAddress(c)}</td>
                </tr>
            `).join('');

            document.getElementById('employeesTable').innerHTML = db.employees.map(e => `<tr class="border-b"><td class="p-2">${e.name}</td><td class="p-2 font-mono">${e.username || '-'}</td><td class="p-2"><span class="bg-slate-100 px-2 py-0.5 rounded text-xs">${e.role || 'sales'}</span></td><td class="p-2">${e.commission_rate}%</td></tr>`).join('');
            document.getElementById('productsTable').innerHTML = db.products.map(p => `<tr class="border-b"><td class="p-2">${p.name}</td><td class="p-2">${p.price}</td><td class="p-2">${p.cost}</td><td class="p-2 font-bold text-emerald-600">${p.stock}</td></tr>`).join('');

            let invList = document.getElementById('invoicesListTable');
            if(db.invoices.length === 0) {
                invList.innerHTML = `<p class="text-sm text-slate-400 text-center py-2">لا توجد فواتير مبيعات سابقة</p>`;
            } else {
                invList.innerHTML = db.invoices.map((inv, idx) => `
                    <div class="flex justify-between items-center p-3 bg-slate-50 border rounded-xl text-xs">
                        <div>
                            <span class="font-bold text-slate-800">فاتورة #${inv.id}</span> - <span class="text-slate-500">${inv.date}</span>
                            <div class="text-slate-600 font-semibold mt-0.5">العميل: ${inv.customerName} | الإجمالي: ${inv.grand_total.toFixed(2)} ر.س</div>
                        </div>
                        <div class="space-x-1 space-x-reverse">
                            <button onclick="previewInvoice(${idx}, 'modern')" class="bg-indigo-600 text-white px-2.5 py-1 rounded-lg">عصري</button>
                            <button onclick="previewInvoice(${idx}, 'classic')" class="bg-slate-700 text-white px-2.5 py-1 rounded-lg">كلاسيكي</button>
                            <button onclick="previewInvoice(${idx}, 'tax')" class="bg-amber-600 text-white px-2.5 py-1 rounded-lg">ضريبي</button>
                            <button onclick="previewInvoice(${idx}, 'thermal')" class="bg-emerald-600 text-white px-2.5 py-1 rounded-lg">حراري</button>
                        </div>
                    </div>
                `).join('');
            }

            let totalSales = db.invoices.reduce((a, b) => a + b.subtotal, 0);
            let totalSalesVat = db.invoices.reduce((a, b) => a + b.vat_amount, 0);
            let totalCogs = db.invoices.reduce((a, b) => a + b.total_cost, 0);
            let totalPurchasesVat = db.purchases.reduce((a, b) => a + b.vat_amount, 0);

            document.getElementById('vatSales').innerText = totalSalesVat.toFixed(2) + ' ر.س';
            document.getElementById('vatPurchases').innerText = totalPurchasesVat.toFixed(2) + ' ر.س';
            document.getElementById('vatNet').innerText = (totalSalesVat - totalPurchasesVat).toFixed(2) + ' ر.س';

            document.getElementById('repSales').innerText = totalSales.toFixed(2) + ' ر.س';
            document.getElementById('repCogs').innerText = totalCogs.toFixed(2) + ' ر.س';
            document.getElementById('repProfit').innerText = (totalSales - totalCogs).toFixed(2) + ' ر.س';

            let jContainer = document.getElementById('journalsContainer');
            if(db.journals.length === 0) {
                jContainer.innerHTML = `<p class="text-sm text-slate-400 text-center py-4">لا توجد قيود مسجلة بعد.</p>`;
            } else {
                jContainer.innerHTML = db.journals.map(j => `
                    <div class="bg-slate-50 p-4 rounded-xl border">
                        <div class="flex justify-between items-center mb-2">
                            <span class="font-bold text-xs text-indigo-700 bg-indigo-100 px-2.5 py-1 rounded">مرجع القيد: ${j.ref}</span>
                            <span class="text-xs text-slate-500">${j.date}</span>
                        </div>
                        <p class="text-sm font-semibold text-slate-800 mb-3">${j.description}</p>
                        <table class="w-full text-right text-xs bg-white rounded-lg overflow-hidden border">
                            <thead class="bg-slate-200">
                                <tr><th class="p-2">الحساب</th><th class="p-2">مدين</th><th class="p-2">دائن</th></tr>
                            </thead>
                            <tbody>
                                ${j.lines.map(l => `
                                    <tr class="border-t">
                                        <td class="p-2 font-bold">${l.account}</td>
                                        <td class="p-2 text-indigo-600 font-bold">${l.debit > 0 ? l.debit.toFixed(2) : '-'}</td>
                                        <td class="p-2 text-emerald-600 font-bold">${l.credit > 0 ? l.credit.toFixed(2) : '-'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `).join('');
            }
        }

        function addNewCustomer() {
            let name = document.getElementById('custName').value.trim();
            let phone = document.getElementById('custPhone').value.trim();
            let tax_number = document.getElementById('custTaxNumber').value.trim();

            let country = document.getElementById('custCountry').value.trim();
            let region = document.getElementById('custRegion').value.trim();
            let district = document.getElementById('custDistrict').value.trim();
            let building_no = document.getElementById('custBuildingNo').value.trim();
            let postal_code = document.getElementById('custPostalCode').value.trim();

            if(!name) { alert('يرجى كتابة اسم العميل الأساسي'); return; }

            db.customers.push({
                id: Date.now(),
                name,
                phone,
                tax_number,
                country,
                region,
                district,
                building_no,
                postal_code
            });

            saveDb();
            renderUI();
            alert('تم حفظ العميل والعنوان الوطني التفصيلي بنجاح!');
        }

        function createInvoice() {
            let custId = parseInt(document.getElementById('invCustomerId').value);
            let prodId = parseInt(document.getElementById('invProductId').value);
            let empId = parseInt(document.getElementById('invEmployeeId').value);
            let qty = parseInt(document.getElementById('invQuantity').value);
            let templateStyle = document.getElementById('invSelectedTemplate').value;

            let customer = db.customers.find(c => c.id === custId);
            let product = db.products.find(p => p.id === prodId);
            let employee = db.employees.find(e => e.id === empId);

            if(!product || product.stock < qty) { alert('المخزون غير كافٍ!'); return; }

            product.stock -= qty;
            let subtotal = product.price * qty;
            let total_cost = product.cost * qty;
            let currentVatRate = db.settings.vatEnabled ? db.settings.vatRate : 0.0;
            let vat_amount = subtotal * (currentVatRate / 100);
            let grand_total = subtotal + vat_amount;

            let newInvoice = {
                id: db.invoices.length + 1,
                date: new Date().toLocaleString(),
                customerName: customer ? customer.name : "عميل نقدي",
                customerTax: customer ? customer.tax_number : "-",
                customerAddressFormatted: customer ? formatCustomerAddress(customer) : "-",
                employeeName: employee ? employee.name : "-",
                productName: product.name,
                unitPrice: product.price,
                quantity: qty,
                subtotal: subtotal,
                vat_amount: vat_amount,
                grand_total: grand_total,
                total_cost: total_cost
            };

            db.invoices.push(newInvoice);

            if(db.settings.journalsEnabled) {
                let invNum = db.invoices.length;
                let lines = [
                    { account: "الصندوق / النقدية", debit: grand_total, credit: 0 },
                    { account: "إيرادات المبيعات", debit: 0, credit: subtotal }
                ];
                if(db.settings.vatEnabled && vat_amount > 0) {
                    lines.push({ account: "ضريبة القيمة المضافة المستحقة (مبيعات)", debit: 0, credit: vat_amount });
                }

                db.journals.push({
                    ref: `INV-REF-${invNum}`,
                    date: new Date().toLocaleString(),
                    description: `إثبات فاتورة مبيعات رقم #${invNum}`,
                    lines: lines
                });

                db.journals.push({
                    ref: `COGS-REF-${invNum}`,
                    date: new Date().toLocaleString(),
                    description: `إثبات تكلفة البضاعة المباعة للفاتورة #${invNum}`,
                    lines: [
                        { account: "تكلفة البضاعة المباعة (COGS)", debit: total_cost, credit: 0 },
                        { account: "مخزون البضائع", debit: 0, credit: total_cost }
                    ]
                });
            }

            saveDb();
            renderUI();
            previewInvoice(db.invoices.length - 1, templateStyle);
        }

        function previewInvoice(index, template) {
            let inv = db.invoices[index];
            if(!inv) return;
            renderInvoiceTemplate(inv, template);
        }

        function renderInvoiceTemplate(inv, template) {
            let htmlContent = "";
            let comp = db.settings;

            if (template === 'classic') {
                htmlContent = `
                    <div class="border-4 border-slate-800 p-6 text-slate-800">
                        <div class="flex justify-between border-b-2 border-slate-800 pb-4 mb-4">
                            <div>
                                <h2 class="text-2xl font-black">${comp.companyName}</h2>
                                <p class="text-xs">${comp.companyAddress} | هاتف: ${comp.companyPhone}</p>
                                <p class="text-xs font-bold">الرقم الضريبي: ${comp.companyTax}</p>
                            </div>
                            <div class="text-left">
                                <h3 class="text-xl font-bold uppercase">فاتورة مبيعات</h3>
                                <p class="text-xs">رقم الفاتورة: #${inv.id}</p>
                                <p class="text-xs">التاريخ: ${inv.date}</p>
                            </div>
                        </div>
                        <div class="mb-4 bg-slate-50 p-3 border space-y-1">
                            <p class="text-xs"><b>العميل:</b> ${inv.customerName} (الرقم الضريبي: ${inv.customerTax})</p>
                            <p class="text-xs"><b>العنوان الوطني:</b> ${inv.customerAddressFormatted || '-'}</p>
                            <p class="text-xs"><b>الموظف المسؤول:</b> ${inv.employeeName}</p>
                        </div>
                        <table class="w-full text-right text-xs border-collapse border border-slate-800 mb-4">
                            <thead class="bg-slate-200">
                                <tr><th class="border border-slate-800 p-2">السلعة / الخدمة</th><th class="border border-slate-800 p-2">السعر</th><th class="border border-slate-800 p-2">الكمية</th><th class="border border-slate-800 p-2">المجموع</th></tr>
                            </thead>
                            <tbody>
                                <tr><td class="border border-slate-800 p-2">${inv.productName}</td><td class="border border-slate-800 p-2">${inv.unitPrice.toFixed(2)}</td><td class="border border-slate-800 p-2">${inv.quantity}</td><td class="border border-slate-800 p-2">${inv.subtotal.toFixed(2)}</td></tr>
                            </tbody>
                        </table>
                        <div class="text-left text-xs space-y-1">
                            <p>المبلغ الخاضع للضريبة: <b>${inv.subtotal.toFixed(2)} ر.س</b></p>
                            <p>ضريبة القيمة المضافة: <b>${inv.vat_amount.toFixed(2)} ر.س</b></p>
                            <p class="text-sm font-bold border-t border-slate-800 pt-1">الإجمالي الشامل: ${inv.grand_total.toFixed(2)} ر.س</p>
                        </div>
                    </div>
                `;
            } else if (template === 'tax') {
                htmlContent = `
                    <div class="border-2 border-emerald-600 p-6 rounded-2xl text-slate-800">
                        <div class="text-center bg-emerald-50 p-3 rounded-xl mb-4 border border-emerald-200">
                            <h2 class="text-xl font-extrabold text-emerald-900">فاتورة ضريبية مبسطة (TAX INVOICE)</h2>
                            <p class="text-xs text-emerald-700">${comp.companyName} - الرقم الضريبي: ${comp.companyTax}</p>
                        </div>
                        <div class="grid grid-cols-2 text-xs mb-4 gap-2 bg-slate-50 p-3 rounded-xl border">
                            <div><b>رقم الفاتورة:</b> INV-${inv.id}</div>
                            <div><b>التاريخ والوقت:</b> ${inv.date}</div>
                            <div><b>اسم العميل:</b> ${inv.customerName}</div>
                            <div><b>الرقم الضريبي للعميل:</b> ${inv.customerTax}</div>
                            <div class="col-span-2"><b>العنوان الوطني للعميل:</b> ${inv.customerAddressFormatted || '-'}</div>
                        </div>
                        <table class="w-full text-right text-xs mb-4">
                            <thead class="bg-emerald-600 text-white">
                                <tr><th class="p-2">الصنف</th><th class="p-2">السعر Uniprice</th><th class="p-2">الكمية Qty</th><th class="p-2">الضريبة VAT</th><th class="p-2">الإجمالي Total</th></tr>
                            </thead>
                            <tbody class="divide-y border-b">
                                <tr><td class="p-2 font-bold">${inv.productName}</td><td class="p-2">${inv.unitPrice.toFixed(2)}</td><td class="p-2">${inv.quantity}</td><td class="p-2">${inv.vat_amount.toFixed(2)}</td><td class="p-2 font-bold text-emerald-700">${inv.grand_total.toFixed(2)}</td></tr>
                            </tbody>
                        </table>
                        <div class="flex justify-between items-center bg-slate-50 p-4 rounded-xl border">
                            <div class="text-[10px] text-slate-500">ملاحظة: هذه الفاتورة صادرة إلكترونياً ومعتمدة ضريبياً</div>
                            <div class="text-xs space-y-1 text-left">
                                <div>الصافي: ${inv.subtotal.toFixed(2)} ر.س</div>
                                <div>إجمالي الضريبة (15%): ${inv.vat_amount.toFixed(2)} ر.س</div>
                                <div class="text-sm font-extrabold text-emerald-800">المبلغ المستحق: ${inv.grand_total.toFixed(2)} ر.س</div>
                            </div>
                        </div>
                    </div>
                `;
            } else if (template === 'thermal') {
                htmlContent = `
                    <div class="max-w-[300px] mx-auto p-3 font-mono text-xs text-center border shadow-sm bg-white">
                        <h3 class="font-bold text-sm">${comp.companyName}</h3>
                        <p class="text-[10px]">${comp.companyAddress}</p>
                        <p class="text-[10px]">الرقم الضريبي: ${comp.companyTax}</p>
                        <hr class="my-2 border-dashed">
                        <div class="text-right text-[10px] space-y-0.5">
                            <div>رقم الفاتورة: #${inv.id}</div>
                            <div>التاريخ: ${inv.date}</div>
                            <div>العميل: ${inv.customerName}</div>
                            <div>الكاشير: ${inv.employeeName}</div>
                        </div>
                        <hr class="my-2 border-dashed">
                        <table class="w-full text-right text-[10px] mb-2">
                            <thead><tr class="border-b"><th class="py-1">الصنف</th><th>العدد</th><th>المجموع</th></tr></thead>
                            <tbody>
                                <tr><td class="py-1">${inv.productName}</td><td>${inv.quantity}</td><td>${inv.subtotal.toFixed(2)}</td></tr>
                            </tbody>
                        </table>
                        <hr class="my-2 border-dashed">
                        <div class="text-left text-[10px] space-y-1">
                            <div class="flex justify-between"><span>المجموع:</span><span>${inv.subtotal.toFixed(2)}</span></div>
                            <div class="flex justify-between"><span>الضريبة (15%):</span><span>${inv.vat_amount.toFixed(2)}</span></div>
                            <div class="flex justify-between font-bold text-xs"><span>الإجمالي:</span><span>${inv.grand_total.toFixed(2)} ر.س</span></div>
                        </div>
                        <hr class="my-2 border-dashed">
                        <p class="text-[9px] text-slate-500">شكراً لزيارتكم! نتمنى لكم يوماً سعيداً</p>
                    </div>
                `;
            } else {
                htmlContent = `
                    <div class="p-6 text-slate-800">
                        <div class="flex justify-between items-center mb-6 bg-slate-900 text-white p-6 rounded-2xl">
                            <div>
                                <h2 class="text-xl font-extrabold">${comp.companyName}</h2>
                                <p class="text-xs text-indigo-200 mt-1">${comp.companyAddress} | ${comp.companyPhone}</p>
                                <p class="text-xs text-indigo-300">الرقم الضريبي: ${comp.companyTax}</p>
                            </div>
                            <div class="text-left">
                                <span class="bg-indigo-600 text-white px-3 py-1 rounded-full text-xs font-bold inline-block mb-1">فاتورة مبيعات</span>
                                <h3 class="text-lg font-bold">#INV-${inv.id}</h3>
                                <p class="text-[10px] text-slate-300">${inv.date}</p>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-4 mb-6 bg-slate-50 p-4 rounded-xl border text-xs">
                            <div>
                                <span class="text-slate-400 block mb-0.5">بيانات العميل والعنوان الوطني:</span>
                                <span class="font-bold text-sm block">${inv.customerName}</span>
                                <span class="text-slate-600 block mt-1">${inv.customerAddressFormatted || '-'}</span>
                            </div>
                            <div>
                                <span class="text-slate-400 block mb-0.5">الموظف المسؤول:</span>
                                <span class="font-bold block">${inv.employeeName}</span>
                                <span class="text-slate-500 block mt-1">الرقم الضريبي للعميل: ${inv.customerTax || '-'}</span>
                            </div>
                        </div>
                        <table class="w-full text-right text-xs mb-6">
                            <thead class="bg-slate-100 border-b"><tr class="text-slate-600"><th class="p-3">المنتج / الوصف</th><th class="p-3">السعر</th><th class="p-3">الكمية</th><th class="p-3">الإجمالي</th></tr></thead>
                            <tbody>
                                <tr class="border-b"><td class="p-3 font-bold">${inv.productName}</td><td class="p-3">${inv.unitPrice.toFixed(2)}</td><td class="p-3">${inv.quantity}</td><td class="p-3 font-bold text-indigo-600">${inv.subtotal.toFixed(2)}</td></tr>
                            </tbody>
                        </table>
                        <div class="flex justify-end">
                            <div class="w-64 bg-slate-50 p-4 rounded-xl border space-y-2 text-xs">
                                <div class="flex justify-between"><span>المبلغ غير شامل الضريبة:</span><span>${inv.subtotal.toFixed(2)} ر.س</span></div>
                                <div class="flex justify-between"><span>ضريبة القيمة المضافة:</span><span>${inv.vat_amount.toFixed(2)} ر.س</span></div>
                                <hr>
                                <div class="flex justify-between font-extrabold text-sm text-indigo-900"><span>الإجمالي النهائي:</span><span>${inv.grand_total.toFixed(2)} ر.س</span></div>
                            </div>
                        </div>
                    </div>
                `;
            }

            document.getElementById('printableInvoice').innerHTML = htmlContent;
            document.getElementById('invoiceModal').classList.remove('hidden');
        }

        function closeInvoiceModal() {
            document.getElementById('invoiceModal').classList.add('hidden');
        }

        function addNewEmployee() {
            let name = document.getElementById('empName').value;
            let username = document.getElementById('empUsername').value.trim();
            let password = document.getElementById('empPassword').value.trim();
            let role = document.getElementById('empRole').value;
            let commission_rate = parseFloat(document.getElementById('empCommission').value);

            if(!name || !username || !password) { alert('يرجى إدخال اسم الموظف وبيانات الدخول كاملة'); return; }

            db.users.push({ username, password, name, role });
            db.employees.push({ id: Date.now(), name, username, role, commission_rate: db.settings.commissionsEnabled ? (commission_rate || 0) : 0 });
            
            saveDb(); renderUI(); alert('تم إضافة الموظف وحساب الدخول بنجاح!');
        }

        function addNewProduct() {
            let name = document.getElementById('prodName').value;
            let price = parseFloat(document.getElementById('prodPrice').value);
            let cost = parseFloat(document.getElementById('prodCost').value);
            let stock = parseInt(document.getElementById('prodStock').value);
            if(!name) { alert('أدخل اسم المنتج'); return; }
            db.products.push({ id: Date.now(), name, price: price || 0, cost: cost || 0, stock: stock || 0 });
            saveDb(); renderUI(); alert('تم إضافة المنتج بنجاح!');
        }

        function createPurchase() {
            let supplier = document.getElementById('purSupplier').value;
            let prodId = parseInt(document.getElementById('purProductId').value);
            let qty = parseInt(document.getElementById('purQuantity').value);
            let unitCost = parseFloat(document.getElementById('purUnitCost').value);

            let product = db.products.find(p => p.id === prodId);
            if(!product) { alert('المنتج غير موجود'); return; }

            product.stock += qty;
            product.cost = unitCost;
            let subtotal = qty * unitCost;

            let currentVatRate = db.settings.vatEnabled ? db.settings.vatRate : 0.0;
            let vat_amount = subtotal * (currentVatRate / 100);
            let grand_total = subtotal + vat_amount;

            db.purchases.push({ subtotal, vat_amount });

            if(db.settings.journalsEnabled) {
                let purNum = db.purchases.length;
                let lines = [
                    { account: "مخزون البضائع", debit: subtotal, credit: 0 }
                ];
                if(db.settings.vatEnabled && vat_amount > 0) {
                    lines.push({ account: "ضريبة القيمة المضافة (مشتريات)", debit: vat_amount, credit: 0 });
                }
                lines.push({ account: "الصندوق / النقدية", debit: 0, credit: grand_total });

                db.journals.push({
                    ref: `PUR-REF-${purNum}`,
                    date: new Date().toLocaleString(),
                    description: `إثبات مشتريات من المورد (${supplier || 'مورد نقدي'})`,
                    lines: lines
                });
            }

            saveDb(); renderUI(); alert('تم تسجيل المشتريات بنجاح!');
        }

        window.onload = function() {
            initSessionUI();
        };
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    """عرض النظام السحابي بشكل مباشر بدون الاعتماد على ملفات خارجية"""
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    # دعم المنفذ الديناميكي لمنصات السحاب (مثل Render أو Heroku)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
