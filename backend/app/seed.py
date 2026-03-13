"""
Demo ma'lumotlarni yaratish skripti.
Ishga tushirish: python -m app.seed
"""
import random
from datetime import date, timedelta, datetime

from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.branch import Branch
from app.models.department import Department
from app.models.employee import Employee
from app.models.category import AssetCategory
from app.models.asset import Asset
from app.models.assignment import AssetAssignment
from app.models.audit_log import AuditLog
from app.core.security import get_password_hash
from app.core.enums import AssetStatus
from app.services.qrcode_service import generate_qr

Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()

    if db.query(User).first():
        print("Ma'lumotlar allaqachon mavjud. Seed bekor qilindi.")
        db.close()
        return

    # ===== BRANCHES =====
    branches_data = [
        ("Bosh ofis", "HQ", "Toshkent sh., Amir Temur ko'chasi 1"),
        ("Chilonzor filiali", "BR-01", "Toshkent sh., Chilonzor tumani, 9-mavze"),
        ("Yakkasaroy filiali", "BR-02", "Toshkent sh., Yakkasaroy tumani, Shota Rustaveli 15"),
        ("Samarqand filiali", "BR-03", "Samarqand sh., Registon ko'chasi 5"),
        ("Buxoro filiali", "BR-04", "Buxoro sh., Mustaqillik ko'chasi 20"),
    ]
    branches = []
    for name, code, address in branches_data:
        b = Branch(name=name, code=code, address=address)
        branches.append(b)
    db.add_all(branches)
    db.flush()
    print(f"  {len(branches)} filial yaratildi")

    # ===== DEPARTMENTS =====
    dept_templates = [
        ("IT bo'limi", "IT"),
        ("Moliya bo'limi", "FIN"),
        ("Kredit bo'limi", "CRED"),
        ("Xavfsizlik bo'limi", "SEC"),
        ("Kassir bo'limi", "CASH"),
        ("HR bo'limi", "HR"),
    ]
    departments = []
    for branch in branches:
        for name, code in dept_templates:
            d = Department(name=name, code=f"{branch.code}-{code}", branch_id=branch.id)
            departments.append(d)
    db.add_all(departments)
    db.flush()
    print(f"  {len(departments)} bo'lim yaratildi")

    # ===== EMPLOYEES =====
    first_names = ["Sardor", "Aziza", "Bobur", "Dilnoza", "Eldor", "Feruza", "G'ayrat",
                   "Hulkar", "Islom", "Jamila", "Kamol", "Lola", "Mirzo", "Nodira",
                   "Otabek", "Parizod", "Ravshan", "Sabohat", "Temur", "Umida",
                   "Vohid", "Xurshid", "Yulduz", "Zafar", "Barno", "Dostonbek",
                   "Elmurod", "Farzona", "Gulnora", "Hayot"]
    last_names = ["Karimov", "Rahimova", "Mirzayev", "Toshmatova", "Aliyev", "Zokirova",
                  "Saidov", "Umarova", "Tursunov", "Nurmatova", "Ergashev", "Abdullayeva",
                  "Xolmatov", "Yusupova", "Nazarov", "Sultanova", "Raxmatullayev",
                  "Hasanova", "Qodirov", "Botirova"]
    positions = ["Dasturchi", "Tizim administratori", "Moliyachi", "Kredit eksperti",
                 "Xavfsizlik xodimi", "Kassir", "HR mutaxassisi", "Bo'lim boshlig'i",
                 "Bosh mutaxassis", "Kichik mutaxassis"]

    employees = []
    emp_counter = 1
    for dept in departments:
        num_emp = random.randint(2, 4)
        for _ in range(num_emp):
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            e = Employee(
                full_name=f"{fname} {lname}",
                employee_code=f"EMP-{emp_counter:03d}",
                position=random.choice(positions),
                department_id=dept.id,
                phone=f"+998{random.randint(90, 99)}{random.randint(1000000, 9999999)}",
                email=f"{fname.lower()}.{lname.lower()}.{emp_counter}@bank.uz",
            )
            employees.append(e)
            emp_counter += 1
    db.add_all(employees)
    db.flush()
    print(f"  {len(employees)} xodim yaratildi")

    # ===== USERS =====
    # user rolini birinchi xodimga bog'laymiz
    user_employee = employees[0]

    users = [
        User(username="admin", full_name="Administrator", email="admin@bank.uz",
             hashed_password=get_password_hash("admin123"), role="admin"),
        User(username="user", full_name=user_employee.full_name, email="user@bank.uz",
             hashed_password=get_password_hash("user123"), role="user",
             employee_id=user_employee.id),
    ]
    db.add_all(users)
    db.flush()
    print(f"  {len(users)} foydalanuvchi yaratildi")
    print("  Login ma'lumotlari:")
    print("    admin / admin123 (Administrator)")
    print(f"    user / user123 (Xodim: {user_employee.full_name})")

    # ===== CATEGORIES =====
    categories_data = [
        ("Noutbuk", "LAP", "Noutbuklar va ultrabuqlar", 60),
        ("Kompyuter", "PC", "Stol kompyuterlari", 60),
        ("Monitor", "MON", "LCD va LED monitorlar", 60),
        ("Printer", "PRT", "Printer va MFU qurilmalar", 48),
        ("Server", "SRV", "Server jihozlari", 72),
        ("Tarmoq jihozi", "NET", "Routerlar, switchlar, AP", 60),
        ("UPS", "UPS", "Uzluksiz quvvat manbalari", 36),
        ("Xavfsizlik kamerasi", "CAM", "CCTV va IP kameralar", 48),
        ("Bankomat", "ATM", "ATM va terminal qurilmalar", 84),
        ("Telefon", "PHN", "Mobil telefonlar va planshetlar", 36),
        ("Ofis mebellar", "FUR", "Stol, stul, shkaf", 120),
        ("Skaner", "SCN", "Hujjat skanerlari", 48),
    ]
    categories = []
    for name, code, desc, life in categories_data:
        c = AssetCategory(name=name, code=code, description=desc, useful_life_months=life)
        categories.append(c)
    db.add_all(categories)
    db.flush()
    print(f"  {len(categories)} kategoriya yaratildi")

    # ===== ASSETS =====
    asset_templates = {
        "LAP": [
            ("Dell Latitude 5540", "DELL-LAT"),
            ("Lenovo ThinkPad T14", "LEN-TP"),
            ("HP ProBook 450 G10", "HP-PB"),
            ("Dell Latitude 7440", "DELL-74"),
            ("Lenovo ThinkPad X1 Carbon", "LEN-X1"),
        ],
        "PC": [
            ("Dell OptiPlex 7010", "DELL-OP"),
            ("HP ProDesk 400 G9", "HP-PD"),
            ("Lenovo ThinkCentre M70q", "LEN-TC"),
        ],
        "MON": [
            ("Dell P2422H 24\"", "DELL-P24"),
            ("Samsung S24E650", "SAM-S24"),
            ("LG 27UL850", "LG-27"),
            ("HP E24 G5", "HP-E24"),
        ],
        "PRT": [
            ("HP LaserJet Pro M404", "HP-LJ"),
            ("Canon i-SENSYS LBP226", "CAN-LBP"),
            ("Epson L6190 MFU", "EPS-MFU"),
        ],
        "SRV": [
            ("Dell PowerEdge R750", "DELL-PE"),
            ("HP ProLiant DL380 Gen10", "HP-DL"),
        ],
        "NET": [
            ("Cisco Catalyst 2960-X", "CISCO-SW"),
            ("MikroTik RB4011", "MKT-RB"),
            ("TP-Link Archer AX6000", "TPL-AX"),
            ("Ubiquiti UniFi AP", "UBQ-AP"),
        ],
        "UPS": [
            ("APC Smart-UPS 1500VA", "APC-1500"),
            ("Eaton 5P 1150i", "EAT-5P"),
        ],
        "CAM": [
            ("Hikvision DS-2CD2143G2", "HIK-2143"),
            ("Dahua IPC-HFW2431S", "DAH-2431"),
        ],
        "ATM": [
            ("NCR SelfServ 80", "NCR-SS80"),
            ("Diebold Nixdorf CS 5550", "DN-5550"),
        ],
        "PHN": [
            ("Samsung Galaxy A54", "SAM-A54"),
            ("iPhone 14", "APL-14"),
        ],
        "FUR": [
            ("Ergonomik ofis stuli", "FUR-CH"),
            ("Ofis stoli 160x80", "FUR-DSK"),
        ],
        "SCN": [
            ("Fujitsu fi-7160", "FUJ-716"),
            ("Canon DR-C225II", "CAN-DRC"),
        ],
    }

    # Kategoriya kodiga mos rasm fayllari
    category_photos = {
        "LAP": "/api/uploads/asset_laptop.png",
        "PC": "/api/uploads/asset_pc.png",
        "MON": "/api/uploads/asset_monitor.png",
        "PRT": "/api/uploads/asset_printer.png",
        "SRV": "/api/uploads/asset_server.png",
        "NET": "/api/uploads/asset_network.png",
        "UPS": "/api/uploads/asset_ups.png",
        "CAM": "/api/uploads/asset_camera.png",
        "ATM": "/api/uploads/asset_atm.png",
        "PHN": "/api/uploads/asset_phone.png",
        "FUR": "/api/uploads/asset_furniture.png",
        "SCN": "/api/uploads/asset_scanner.png",
    }

    # Barcha 5 ta status — LOST va WRITTEN_OFF ham mavjud
    statuses = [AssetStatus.REGISTERED, AssetStatus.ASSIGNED, AssetStatus.IN_REPAIR,
                AssetStatus.ASSIGNED, AssetStatus.REGISTERED, AssetStatus.ASSIGNED,
                AssetStatus.ASSIGNED, AssetStatus.REGISTERED, AssetStatus.ASSIGNED,
                AssetStatus.LOST, AssetStatus.WRITTEN_OFF]

    # ── Muammoli izohlar (AI Feature 4 uchun) ──
    problem_notes = [
        "Bu jihoz tez-tez nosoz bo'ladi, almashtirilishi kerak",
        "Ekranda chiziqlar paydo bo'lgan, foydalanuvchilar shikoyat qilmoqda",
        "Batareya tez quvvat yo'qotadi, 30 daqiqada o'chib qoladi",
        "Printer qog'oz tez-tez tiqilib qoladi, mexanizm eskirgan",
        "Server vaqti-vaqti bilan o'chib qoladi, quvvat bloki shubhali",
        "Kamera tasvir sifati yomonlashgan, linza chirigan",
        "Klaviatura tugmalari ishlamaydi, suyuqlik tushgan",
        "Monitor ranglari noto'g'ri ko'rsatadi, panel eskirgan",
        "Tizim juda sekin ishlaydi, xotira yetishmayapti",
        "Qurilma qizib ketadi, sovutish tizimi buzilgan",
        "Tarmoqqa ulanmayapti, Wi-Fi moduli nosoz",
        "Qog'oz tortish mexanizmi shovqin chiqaradi, yeyilgan",
        "Akkumulyator shishgan, xavfli holat — foydalanish to'xtatildi",
        "Skaner hujjatni to'liq o'qimayapti, sensor eskirgan",
    ]

    # Ijobiy/neytral izohlar (muammoli bo'lmagan aktivlar uchun)
    normal_notes = [
        "Yaxshi holatda, muammosiz ishlayapti",
        "Oxirgi tekshiruvda hech qanday nuqson topilmadi",
        "Yangi kafolat bo'yicha almashtirilgan, a'lo holatda",
        None, None, None, None,  # ko'pchilik izohlarsiz
    ]

    # Muammoli assignment izohlari
    problem_assignment_notes = [
        "Xodim jihozdan ko'p shikoyat qildi, tez-tez muzlab qoladi",
        "Oldingi foydalanuvchi ham shu muammoni bildirgan edi",
        "Jihoz ishga yaroqsiz holda qaytarildi, ekrani singan",
        "Xodim nosoz deb qaytardi, diagnostika kerak",
        "Printer tez-tez qog'oz tiqilishi sababli qaytarildi",
        "Batareya muammosi — 1 soatdan ko'p ishlamaydi",
        "Tizim platasi nosozligi sababli foydalanib bo'lmaydi",
    ]

    assets = []
    asset_counter = {}

    for cat in categories:
        templates = asset_templates.get(cat.code, [])
        if not templates:
            continue

        num_assets = random.randint(8, 15) if cat.code in ["LAP", "PC", "MON"] else random.randint(3, 8)

        useful_life_days = (cat.useful_life_months or 60) * 30
        num_aging = random.randint(2, 3)

        for i in range(num_assets):
            template = random.choice(templates)
            name, sn_prefix = template

            if cat.code not in asset_counter:
                asset_counter[cat.code] = 0
            asset_counter[cat.code] += 1
            seq = asset_counter[cat.code]

            serial = f"{sn_prefix}-{random.randint(10000, 99999)}"
            inv_num = f"BNK-{cat.code}-2026-{seq:04d}"
            status = random.choice(statuses)

            if i >= num_assets - num_aging:
                extra_days = random.randint(180, 720)
                purchase_days_ago = useful_life_days + extra_days
            else:
                purchase_days_ago = random.randint(30, 1800)

            p_date = date.today() - timedelta(days=purchase_days_ago)
            price = round(random.uniform(500, 50000), 2)
            if cat.code in ["SRV", "ATM"]:
                price = round(random.uniform(10000, 100000), 2)
            elif cat.code == "FUR":
                price = round(random.uniform(200, 3000), 2)

            warranty_days = random.choice([365, 730, 1095])
            # 8-10 ta aktivning kafolati 30 kun ichida tugaydigan qilish (AI insights uchun)
            if len(assets) in (5, 12, 19, 26, 33, 40, 47, 54):
                w_date = date.today() + timedelta(days=random.randint(3, 28))
            else:
                w_date = p_date + timedelta(days=warranty_days)

            # ASSIGNED — user_employee ga 2-3 ta, qolganini random xodimlarga
            # LOST, WRITTEN_OFF, REGISTERED, IN_REPAIR — hech kimga biriktirilmaydi
            if status == AssetStatus.ASSIGNED:
                assigned_to_user = len([a for a in assets if a.current_employee_id == user_employee.id])
                if assigned_to_user < 3:
                    emp = user_employee
                else:
                    emp = random.choice(employees)
            else:
                emp = None

            # Muammoli aktivlarga salbiy izoh, qolganiga neytral/bo'sh
            if status in (AssetStatus.IN_REPAIR, AssetStatus.LOST):
                asset_note = random.choice(problem_notes)
            elif status == AssetStatus.WRITTEN_OFF:
                asset_note = random.choice(problem_notes + ["Ta'mirga yaroqsiz, hisobdan chiqarildi"])
            else:
                asset_note = random.choice(normal_notes)

            a = Asset(
                name=name,
                serial_number=serial,
                inventory_number=inv_num,
                category_id=cat.id,
                status=status,
                description=f"{name} - {cat.description}",
                purchase_date=p_date,
                purchase_price=price,
                warranty_expiry=w_date,
                photo_path=category_photos.get(cat.code),
                current_employee_id=emp.id if emp else None,
                current_department_id=emp.department_id if emp else None,
                current_branch_id=emp.department.branch_id if emp and emp.department else None,
                notes=asset_note,
                created_by=users[0].id,
            )
            assets.append(a)

    db.add_all(assets)
    db.flush()
    print(f"  {len(assets)} aktiv yaratildi")

    # ── REPEAT OFFENDER aktivlar (AI Risk & Problematic uchun) ──
    # Bu aktivlar ko'p marta ta'mirga tushgan, tezlashib boradigan pattern
    repeat_offenders = []
    repeat_configs = [
        ("Dell Latitude 5540 (Muammoli)", "LAP", "DELL-RPT-00001", "BNK-LAP-RPT-001",
         "Ko'p marta ta'mirga tushgan, ekran va klaviatura muammolari takrorlanmoqda",
         4, AssetStatus.IN_REPAIR),
        ("HP LaserJet Pro M404 (Eskirgan)", "PRT", "HP-RPT-00002", "BNK-PRT-RPT-002",
         "Printer mexanizmi yeyilgan, qog'oz tez-tez tiqiladi, kartridj o'rniga o'tirmasligi bor",
         3, AssetStatus.IN_REPAIR),
        ("APC Smart-UPS 1500VA (Nosoz)", "UPS", "APC-RPT-00003", "BNK-UPS-RPT-003",
         "UPS batareyasi 2 marta almashtirilgan, yana muammo qaytardi. Quvvat uzilishida ishlamaydi",
         5, AssetStatus.ASSIGNED),
        ("Cisco Catalyst 2960-X (Eski)", "NET", "CISCO-RPT-00004", "BNK-NET-RPT-004",
         "Switch portlari vaqti-vaqti bilan uziladi, firmware yangilanmaydi",
         3, AssetStatus.ASSIGNED),
        ("Lenovo ThinkPad T14 (Yo'qolish xavfi)", "LAP", "LEN-RPT-00005", "BNK-LAP-RPT-005",
         "3 marta turli xodimlarga biriktirilgan, har safar muammo bilan qaytarilgan",
         4, AssetStatus.REGISTERED),
    ]

    for rname, rcode, rserial, rinv, rnotes, repair_count, rstatus in repeat_configs:
        rcat = next((c for c in categories if c.code == rcode), categories[0])
        # Eski aktiv — 3+ yil oldin sotib olingan
        rp_date = date.today() - timedelta(days=random.randint(1100, 1500))
        rprice = round(random.uniform(3000, 25000), 2)
        # Kafolati allaqachon tugagan
        rw_date = rp_date + timedelta(days=730)

        ra = Asset(
            name=rname, serial_number=rserial, inventory_number=rinv,
            category_id=rcat.id, status=rstatus,
            description=f"{rname} - muammoli aktiv",
            purchase_date=rp_date, purchase_price=rprice, warranty_expiry=rw_date,
            photo_path=category_photos.get(rcode),
            notes=rnotes, created_by=users[0].id,
        )
        # ASSIGNED bo'lsa random xodimga biriktir
        if rstatus == AssetStatus.ASSIGNED:
            remp = random.choice(employees)
            ra.current_employee_id = remp.id
            ra.current_department_id = remp.department_id
            ra.current_branch_id = remp.department.branch_id if remp.department else branches[0].id

        repeat_offenders.append((ra, repair_count))
        db.add(ra)

    db.flush()
    assets.extend([ro[0] for ro in repeat_offenders])
    print(f"  {len(repeat_offenders)} ta repeat offender aktiv yaratildi")

    # Generate QR codes
    qr_count = 0
    for a in assets:
        try:
            filename = generate_qr(a.inventory_number)
            a.qr_code_path = filename
            qr_count += 1
        except Exception:
            pass
    db.commit()
    print(f"  {qr_count} QR kod generatsiya qilindi")

    # ===== ASSIGNMENTS (synthetic history) =====
    assignment_count = 0
    return_reasons = [
        "Yangi jihozga almashtirildi",
        "Xodim ishdan bo'shadi",
        "Bo'limlar o'rtasida ko'chirish",
        "Ta'mirga yuborildi",
        "Inventarizatsiya bo'yicha qaytarildi",
        "Kafolat bo'yicha almashtirildi",
    ]

    lost_reasons = [
        "Xodim yo'qotdi, izlash natija bermadi",
        "Xizmat safari paytida yo'qoldi",
        "Omborda inventarizatsiya paytida topilmadi",
    ]
    writeoff_reasons = [
        "Eskirganligi sababli hisobdan chiqarildi",
        "Ta'mirga yaroqsiz deb topildi",
        "Amortizatsiya muddati tugagan",
    ]

    for a in assets:
        if a.status not in (AssetStatus.ASSIGNED, AssetStatus.IN_REPAIR,
                            AssetStatus.LOST, AssetStatus.WRITTEN_OFF):
            continue

        past_count = random.randint(1, 3)
        base_date = a.purchase_date or (date.today() - timedelta(days=365))
        cursor_date = base_date + timedelta(days=random.randint(5, 30))

        for j in range(past_count):
            past_emp = random.choice(employees)
            assigned_at = datetime(cursor_date.year, cursor_date.month, cursor_date.day,
                                   random.randint(8, 17), random.randint(0, 59))
            duration = random.randint(30, 180)
            returned_date = cursor_date + timedelta(days=duration)
            returned_at = datetime(returned_date.year, returned_date.month, returned_date.day,
                                   random.randint(8, 17), random.randint(0, 59))

            reason = random.choice(return_reasons)
            if j == past_count - 1 and a.status == AssetStatus.IN_REPAIR:
                reason = "Ta'mirga yuborildi"
            elif j == past_count - 1 and a.status == AssetStatus.LOST:
                reason = random.choice(lost_reasons)
            elif j == past_count - 1 and a.status == AssetStatus.WRITTEN_OFF:
                reason = random.choice(writeoff_reasons)

            # Muammoli aktivlarga izohli assignment
            asgn_note = None
            if a.status in (AssetStatus.IN_REPAIR, AssetStatus.LOST, AssetStatus.WRITTEN_OFF):
                if random.random() < 0.6:
                    asgn_note = random.choice(problem_assignment_notes)

            asgn = AssetAssignment(
                asset_id=a.id,
                employee_id=past_emp.id,
                department_id=past_emp.department_id,
                branch_id=past_emp.department.branch_id if past_emp.department else branches[0].id,
                assigned_at=assigned_at,
                returned_at=returned_at,
                assigned_by=users[0].id,
                return_reason=reason,
                notes=asgn_note,
            )
            db.add(asgn)
            assignment_count += 1
            cursor_date = returned_date + timedelta(days=random.randint(1, 14))

        if a.status == AssetStatus.ASSIGNED and a.current_employee_id:
            current_assigned_at = datetime(cursor_date.year, cursor_date.month, cursor_date.day,
                                           random.randint(8, 17), random.randint(0, 59))
            asgn_current = AssetAssignment(
                asset_id=a.id,
                employee_id=a.current_employee_id,
                department_id=a.current_department_id,
                branch_id=a.current_branch_id or branches[0].id,
                assigned_at=current_assigned_at,
                returned_at=None,
                assigned_by=users[0].id,
                notes="Joriy biriktirish",
            )
            db.add(asgn_current)
            assignment_count += 1

    db.flush()
    print(f"  {assignment_count} ta biriktirish tarixi yaratildi")

    # ── Repeat offender aktivlar uchun ko'p assignment + ta'mir tarixi ──
    for ra, repair_count in repeat_offenders:
        cursor_dt = ra.purchase_date + timedelta(days=random.randint(10, 40))
        for rc in range(repair_count):
            remp = random.choice(employees)
            a_at = datetime(cursor_dt.year, cursor_dt.month, cursor_dt.day,
                            random.randint(8, 17), random.randint(0, 59))
            # Har safar interval qisqaradi (tezlashib borayotgan nosozlik)
            duration = max(30, 180 - rc * 40 + random.randint(-10, 10))
            r_date = cursor_dt + timedelta(days=duration)
            r_at = datetime(r_date.year, r_date.month, r_date.day,
                            random.randint(8, 17), random.randint(0, 59))

            asgn = AssetAssignment(
                asset_id=ra.id, employee_id=remp.id,
                department_id=remp.department_id,
                branch_id=remp.department.branch_id if remp.department else branches[0].id,
                assigned_at=a_at, returned_at=r_at, assigned_by=users[0].id,
                return_reason=random.choice(["Ta'mirga yuborildi", "Nosoz holda qaytarildi",
                                              "Xodim shikoyat qildi — jihozda muammo"]),
                notes=random.choice(problem_assignment_notes),
            )
            db.add(asgn)
            assignment_count += 1
            cursor_dt = r_date + timedelta(days=random.randint(5, 20))

        # Hozirgi ASSIGNED bo'lsa, oxirgi assignment
        if ra.status == AssetStatus.ASSIGNED and ra.current_employee_id:
            c_at = datetime(cursor_dt.year, cursor_dt.month, cursor_dt.day,
                            random.randint(8, 17), random.randint(0, 59))
            db.add(AssetAssignment(
                asset_id=ra.id, employee_id=ra.current_employee_id,
                department_id=ra.current_department_id,
                branch_id=ra.current_branch_id or branches[0].id,
                assigned_at=c_at, returned_at=None, assigned_by=users[0].id,
                notes="Joriy biriktirish — oldingi muammolar sababli kuzatuvda",
            ))
            assignment_count += 1

    db.flush()
    print(f"  (repeat offender uchun qo'shimcha assignmentlar qo'shildi)")

    # ===== AUDIT LOGS (real hayotga o'xshash to'liq tarix) =====
    import json

    # Har bir aktiv uchun assignment tarixini oldindan yig'ib olamiz
    asset_assignments_map: dict[int, list] = {}
    for asgn_obj in db.query(AssetAssignment).order_by(AssetAssignment.assigned_at).all():
        asset_assignments_map.setdefault(asgn_obj.asset_id, []).append(asgn_obj)

    in_repair_reasons = [
        "Ekran singan, almashtirilishi kerak",
        "Klaviatura ishlamayapti",
        "Batareya shishgan, xavfsizlik uchun olib tashlandi",
        "Tizim platasi nosoz, diagnostika o'tkazilmoqda",
        "Printer qog'oz tortmayapti, mexanizm buzilgan",
        "Tarmoq porti ishlamayapti",
        "Quvvat bloki yonib ketdi",
        "Kamera tasvir bermayapti, tekshiruvda",
    ]

    update_descriptions = [
        ("Kafolat muddati yangilandi", "warranty_expiry"),
        ("Xarid narxi tuzatildi (buxgalteriya so'rovi)", "purchase_price"),
        ("Tavsif to'ldirildi", "description"),
        ("Seriya raqami tuzatildi", "serial_number"),
    ]

    audit_count = 0
    admin_user = users[0]

    for a in assets:
        logs_for_asset: list[AuditLog] = []

        # 1) CREATED — aktiv ro'yxatga olingan sana (purchase_date + 1-5 kun)
        p_date = a.purchase_date or (date.today() - timedelta(days=365))
        created_dt = datetime(p_date.year, p_date.month, p_date.day,
                              random.randint(9, 17), random.randint(0, 59))
        created_dt += timedelta(days=random.randint(1, 5))
        logs_for_asset.append(AuditLog(
            asset_id=a.id, action="CREATED", entity_type="asset", entity_id=a.id,
            old_value=None,
            new_value=json.dumps({"status": "REGISTERED", "name": a.name, "serial_number": a.serial_number}),
            description=f"Aktiv '{a.name}' (SN: {a.serial_number}) ro'yxatga olindi. Inventar raqam: {a.inventory_number}",
            performed_by=admin_user.id,
            performed_at=created_dt,
        ))

        # 2) Ba'zi aktivlarga UPDATED log (20% ehtimollik)
        if random.random() < 0.2:
            upd_desc, upd_field = random.choice(update_descriptions)
            upd_dt = created_dt + timedelta(days=random.randint(3, 30),
                                             hours=random.randint(0, 8))
            logs_for_asset.append(AuditLog(
                asset_id=a.id, action="UPDATED", entity_type="asset", entity_id=a.id,
                old_value=json.dumps({upd_field: "eski qiymat"}),
                new_value=json.dumps({upd_field: "yangi qiymat"}),
                description=f"{upd_desc}",
                performed_by=admin_user.id,
                performed_at=upd_dt,
            ))

        # 3) Assignment tarixi bo'yicha ASSIGNED va RETURNED loglar
        asgns = asset_assignments_map.get(a.id, [])
        prev_status = "REGISTERED"
        for asgn_obj in asgns:
            emp = next((e for e in employees if e.id == asgn_obj.employee_id), None)
            emp_name = emp.full_name if emp else "Noma'lum"
            dept_obj = next((d for d in departments if d.id == asgn_obj.department_id), None)
            dept_name = dept_obj.name if dept_obj else ""

            # ASSIGNED log
            logs_for_asset.append(AuditLog(
                asset_id=a.id, action="ASSIGNED", entity_type="asset", entity_id=a.id,
                old_value=json.dumps({"status": prev_status, "employee": None}),
                new_value=json.dumps({"status": "ASSIGNED", "employee": emp_name, "department": dept_name}),
                description=f"'{a.name}' xodim {emp_name}ga biriktirildi ({dept_name})",
                performed_by=admin_user.id,
                performed_at=asgn_obj.assigned_at,
            ))
            prev_status = "ASSIGNED"

            # RETURNED log (agar qaytarilgan bo'lsa)
            if asgn_obj.returned_at:
                reason_text = asgn_obj.return_reason or "Qaytarildi"

                # Qaytarilgandan keyin qaysi statusga o'tgan?
                next_status = "REGISTERED"
                # Agar bu oxirgi assignment bo'lsa
                if asgn_obj == asgns[-1]:
                    if a.status == AssetStatus.IN_REPAIR:
                        next_status = "IN_REPAIR"
                    elif a.status == AssetStatus.LOST:
                        next_status = "LOST"
                    elif a.status == AssetStatus.WRITTEN_OFF:
                        next_status = "REGISTERED"  # avval REGISTERED, keyin WRITTEN_OFF
                    else:
                        next_status = "REGISTERED"

                logs_for_asset.append(AuditLog(
                    asset_id=a.id, action="RETURNED", entity_type="asset", entity_id=a.id,
                    old_value=json.dumps({"status": "ASSIGNED", "employee": emp_name}),
                    new_value=json.dumps({"status": next_status, "employee": None}),
                    description=f"'{a.name}' {emp_name}dan qaytarildi. Sabab: {reason_text}",
                    performed_by=admin_user.id,
                    performed_at=asgn_obj.returned_at,
                ))
                prev_status = next_status

        # 4) Hozirgi statusga mos yakuniy log
        if a.status == AssetStatus.IN_REPAIR:
            last_return = asgns[-1].returned_at if asgns and asgns[-1].returned_at else created_dt + timedelta(days=60)
            repair_dt = last_return + timedelta(hours=random.randint(1, 48))
            reason = random.choice(in_repair_reasons)
            logs_for_asset.append(AuditLog(
                asset_id=a.id, action="STATUS_CHANGED", entity_type="asset", entity_id=a.id,
                old_value=json.dumps({"status": prev_status}),
                new_value=json.dumps({"status": "IN_REPAIR", "reason": reason}),
                description=f"Status o'zgardi: {prev_status} → IN_REPAIR. Sabab: {reason}",
                performed_by=admin_user.id,
                performed_at=repair_dt,
            ))

        elif a.status == AssetStatus.LOST:
            last_return = asgns[-1].returned_at if asgns and asgns[-1].returned_at else created_dt + timedelta(days=90)
            lost_dt = last_return + timedelta(hours=random.randint(1, 24))
            reason = random.choice(lost_reasons)
            logs_for_asset.append(AuditLog(
                asset_id=a.id, action="STATUS_CHANGED", entity_type="asset", entity_id=a.id,
                old_value=json.dumps({"status": prev_status}),
                new_value=json.dumps({"status": "LOST", "reason": reason}),
                description=f"Status o'zgardi: {prev_status} → LOST. Sabab: {reason}",
                performed_by=admin_user.id,
                performed_at=lost_dt,
            ))

        elif a.status == AssetStatus.WRITTEN_OFF:
            last_return = asgns[-1].returned_at if asgns and asgns[-1].returned_at else created_dt + timedelta(days=120)
            wo_dt = last_return + timedelta(days=random.randint(5, 30),
                                             hours=random.randint(9, 16))
            reason = random.choice(writeoff_reasons)
            logs_for_asset.append(AuditLog(
                asset_id=a.id, action="STATUS_CHANGED", entity_type="asset", entity_id=a.id,
                old_value=json.dumps({"status": prev_status}),
                new_value=json.dumps({"status": "WRITTEN_OFF", "reason": reason}),
                description=f"Status o'zgardi: {prev_status} → WRITTEN_OFF. Sabab: {reason}",
                performed_by=admin_user.id,
                performed_at=wo_dt,
            ))

        # Loglarni sanaga mos tartibda saqlash
        for log in logs_for_asset:
            db.add(log)
            audit_count += 1

    # ── Repeat offender aktivlar uchun ko'p ta'mir audit loglari ──
    escalating_repair_reasons = [
        ["Klaviatura ba'zi tugmalari ishlamaydi", "Klaviatura butunlay ishdan chiqdi, almashtirildi",
         "Yangi klaviatura ham ishlamay qoldi, tizim platasi shubhali",
         "Tizim platasi nosoz — ta'mirga yaroqsiz bo'lishi mumkin"],
        ["Printer qog'oz tortishda qiyinchilik", "Printer tez-tez qog'oz tiqiladi",
         "Printer mexanizmi buzilgan, ehtiyot qism kerak",
         "Ehtiyot qism almashtirildi, lekin muammo qaytardi — yangi printer kerak"],
        ["UPS batareyasi tez quvvat yo'qotadi", "UPS batareyasi almashtirildi",
         "Yangi batareya ham muammo chiqardi — inverter nosoz",
         "UPS butunlay ishdan chiqdi, almashtirilishi shart",
         "Yangi UPS o'rnatilgunga qadar vaqtincha boshqa UPS ulandi"],
        ["Switch 2 ta porti ishlamayapti", "Switch firmware yangilandi, lekin portlar nosoz",
         "Switch qayta o'rnatildi, vaqtincha ishladi, yana uzildi"],
        ["Noutbuk ekrani titreydi", "Ekran kabeli almashtirildi, lekin muammo qaytardi",
         "Ekran paneli almashtirildi", "Videokarta nosoz — ekran yana titreydi"],
    ]

    for idx, (ra, repair_count) in enumerate(repeat_offenders):
        reasons = escalating_repair_reasons[idx % len(escalating_repair_reasons)]
        rp_date = ra.purchase_date or (date.today() - timedelta(days=1200))
        base_dt = datetime(rp_date.year, rp_date.month, rp_date.day, 10, 0) + timedelta(days=60)

        for rc in range(repair_count):
            # Har safar interval qisqaradi (tezlashib borayotgan nosozlik pattern)
            interval = max(30, 200 - rc * 50 + random.randint(-15, 15))
            repair_dt = base_dt + timedelta(days=interval * (rc + 1), hours=random.randint(0, 8))
            reason = reasons[rc] if rc < len(reasons) else reasons[-1]

            db.add(AuditLog(
                asset_id=ra.id, action="STATUS_CHANGED", entity_type="asset", entity_id=ra.id,
                old_value=json.dumps({"status": "ASSIGNED"}),
                new_value=json.dumps({"status": "IN_REPAIR", "reason": reason}),
                description=f"Status o'zgardi: ASSIGNED → IN_REPAIR. Sabab: {reason}",
                performed_by=admin_user.id, performed_at=repair_dt,
            ))
            # Ta'mirdan qaytish
            fixed_dt = repair_dt + timedelta(days=random.randint(3, 14))
            db.add(AuditLog(
                asset_id=ra.id, action="STATUS_CHANGED", entity_type="asset", entity_id=ra.id,
                old_value=json.dumps({"status": "IN_REPAIR"}),
                new_value=json.dumps({"status": "ASSIGNED", "reason": "Ta'mir yakunlandi"}),
                description=f"Status o'zgardi: IN_REPAIR → ASSIGNED. Ta'mir yakunlandi",
                performed_by=admin_user.id, performed_at=fixed_dt,
            ))
            audit_count += 2

    # ── Davr solishtirish uchun oxirgi 2 oy turli hajmdagi loglar ──
    # O'tgan oy — kam harakatlar, bu oy — ko'p harakatlar
    for extra_idx in range(15):
        extra_asset = random.choice(assets)
        # Bu oy — ko'proq
        this_month_dt = datetime(date.today().year, date.today().month,
                                  random.randint(1, min(28, date.today().day)),
                                  random.randint(9, 17), random.randint(0, 59))
        db.add(AuditLog(
            asset_id=extra_asset.id, action="UPDATED", entity_type="asset", entity_id=extra_asset.id,
            old_value=json.dumps({"status": extra_asset.status}),
            new_value=json.dumps({"status": extra_asset.status}),
            description=f"'{extra_asset.name}' — tekshiruv o'tkazildi, holati yaxshi",
            performed_by=admin_user.id, performed_at=this_month_dt,
        ))
        audit_count += 1

    db.commit()
    print(f"  {audit_count} ta audit log yaratildi")

    print("\nSeed muvaffaqiyatli bajarildi!")
    print(f"Jami: {len(users)} user, {len(branches)} filial, {len(departments)} bo'lim, "
          f"{len(employees)} xodim, {len(categories)} kategoriya, {len(assets)} aktiv")

    db.close()


if __name__ == "__main__":
    seed()
