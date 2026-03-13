"""
AI xizmatlari — Gemini API orqali aqlli tahlil va tavsiyalar.
7 ta asosiy funksiya:
  1. Kategoriya tavsiya qilish (aktiv nomi asosida)
  2. Nosozlik xavfini bashorat qilish
  3. Inventarizatsiya/audit uchun tavsiyalar
  4. Muammoli aktivlarni izohlar orqali aniqlash
  5. AI Chatbot — tabiiy tilda savol-javob
  6. Aktiv avtomatik to'ldirish (auto-fill)
  7. Aktiv bo'yicha AI qisqacha xulosa (QR scan uchun)
"""
import json
import logging
import re
import time
from datetime import date, timedelta
from decimal import Decimal

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.config import settings
from app.models.asset import Asset
from app.models.category import AssetCategory
from app.models.assignment import AssetAssignment
from app.models.audit_log import AuditLog
from app.models.department import Department
from app.models.branch import Branch
from app.models.employee import Employee
from app.core.enums import AssetStatus


# ──────────────────────────────────────────────
# Multi-key + Multi-model fallback tizimi
# ──────────────────────────────────────────────

MODELS = [
    "gemini-2.5-flash-lite",  # 15 RPM, 1000 RPD
    "gemini-2.5-flash",       # 10 RPM, 250 RPD
    "gemini-2.5-pro",         #  5 RPM, 100 RPD
]

# Rate limit yegan key+model juftliklarini eslab qolish
# {("key_index", "model"): timestamp} — 24 soat o'tgach tozalanadi
_rate_limited: dict[tuple[int, str], float] = {}


def _get_api_keys() -> list[str]:
    """Barcha .env dagi GEMINI_API_KEY larni yig'ish."""
    keys = []
    if settings.GEMINI_API_KEY:
        keys.append(settings.GEMINI_API_KEY)
    if settings.GEMINI_API_KEY_2:
        keys.append(settings.GEMINI_API_KEY_2)
    if settings.GEMINI_API_KEY_3:
        keys.append(settings.GEMINI_API_KEY_3)
    return keys


def _is_rate_limited(key_idx: int, model: str) -> bool:
    """Bu key+model juftligi hali limitdami?"""
    key = (key_idx, model)
    if key not in _rate_limited:
        return False
    # 24 soat o'tgan bo'lsa — tozalash (kunlik limitlar)
    if time.time() - _rate_limited[key] > 86400:
        del _rate_limited[key]
        return False
    return True


def _mark_rate_limited(key_idx: int, model: str):
    """Bu key+model juftligini limitga tushgan deb belgilash."""
    _rate_limited[(key_idx, model)] = time.time()


def _ask_ai(system_prompt: str, user_message: str) -> dict:
    """AI ga so'rov yuborish. Barcha key va modellarni sinab ko'radi.
    Returns: {"text": str, "attempts": list[dict]} — natija va urinishlar tarixi.
    """
    keys = _get_api_keys()
    if not keys:
        raise ValueError("GEMINI_API_KEY sozlanmagan")

    attempts = []  # Frontend uchun — qaysi bosqichlardan o'tdi
    last_error = None

    for key_idx, api_key in enumerate(keys):
        key_label = f"Manba {key_idx + 1}"

        # Avval barcha modellarni bu key bilan sinash
        for model in MODELS:
            # Oldin limitga tushgan bo'lsa, o'tkazib yuborish
            if _is_rate_limited(key_idx, model):
                attempts.append({
                    "step": f"{key_label} — oldingi limit sababli o'tkazildi",
                    "status": "skipped",
                })
                continue

            attempts.append({
                "step": f"{key_label} orqali tahlil qilinmoqda...",
                "status": "trying",
            })

            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model,
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.3,
                        max_output_tokens=4096,
                        response_mime_type="application/json",
                    ),
                )
                result_text = response.text or ""
                result_text = re.sub(r"^```(?:json)?\s*\n?", "", result_text.strip())
                result_text = re.sub(r"\n?```\s*$", "", result_text.strip())

                attempts[-1]["status"] = "success"
                attempts[-1]["step"] = f"{key_label} — muvaffaqiyatli tahlil qilindi"

                logger.info(f"[key{key_idx}:{model}] success (first 200): {result_text[:200]}")
                return {"text": result_text, "attempts": attempts}

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    _mark_rate_limited(key_idx, model)
                    attempts[-1]["status"] = "limit"
                    attempts[-1]["step"] = f"{key_label} — limit tugagan, boshqa manba sinab ko'rilmoqda..."
                    logger.warning(f"[key{key_idx}:{model}] rate limited")
                    last_error = e
                    continue
                elif "403" in error_msg or "PERMISSION_DENIED" in error_msg:
                    # Bu key butunlay ishlamaydi — barcha modellarini o'tkazib yuborish
                    for m in MODELS:
                        _mark_rate_limited(key_idx, m)
                    attempts[-1]["status"] = "error"
                    attempts[-1]["step"] = f"{key_label} — kalit muammosi, keyingisiga o'tilmoqda..."
                    last_error = e
                    break  # bu key dan chiqish, keyingi key ga o'tish
                else:
                    attempts[-1]["status"] = "error"
                    attempts[-1]["step"] = f"Kutilmagan xato yuz berdi"
                    raise

    # Hamma key va modellar tugadi
    if last_error:
        attempts.append({
            "step": "Barcha AI manbalari limit tugagan. Keyinroq qayta urinib ko'ring.",
            "status": "exhausted",
        })
        raise last_error

    raise ValueError("Hech qanday API kalit sozlanmagan")


def _parse_json(text: str) -> dict | None:
    """AI javobidan JSON ni xavfsiz ajratib olish."""
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        json_str = text[start:end]
    except ValueError:
        logger.error(f"No JSON braces found in: {text[:200]}")
        return None

    # 1-urinish: to'g'ridan-to'g'ri parse
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # 2-urinish: O'zbek tilidagi apostrof muammosi
    try:
        fixed = re.sub(r"(?<=[\w])'(?=[\w])", "\u2019", json_str)
        return json.loads(fixed)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}. Text: {json_str[:300]}")
        return None


# ──────────────────────────────────────────────
# 1. Kategoriya tavsiya qilish
# ──────────────────────────────────────────────
def suggest_category(db: Session, name: str, description: str | None = None) -> dict:
    """Aktiv nomi va tavsifi asosida kategoriyani AI orqali tavsiya qilish."""
    categories = db.query(AssetCategory).filter(AssetCategory.is_active == True).all()
    cat_list = [{"id": c.id, "name": c.name, "code": c.code, "description": c.description}
                for c in categories]

    system = """Sen bank ofisi aktiv boshqaruv tizimining AI yordamchisisan.
Vazifang: berilgan aktiv nomi va tavsifi asosida eng mos kategoriyani tanlash.
Javobni FAQAT JSON formatda ber, boshqa hech narsa yozma:
{"category_id": <int>, "category_name": "<str>", "confidence": <0-100>, "reason": "<o'zbekcha tushuntirish>"}"""

    user_msg = f"""Mavjud kategoriyalar: {json.dumps(cat_list, ensure_ascii=False)}

Aktiv nomi: {name}
Tavsifi: {description or 'berilmagan'}

Qaysi kategoriyaga tegishli?"""

    ai_result = _ask_ai(system, user_msg)
    parsed = _parse_json(ai_result["text"])
    result = parsed or {"category_id": None, "category_name": None, "confidence": 0,
                        "reason": "AI tahlil qila olmadi"}
    result["_attempts"] = ai_result["attempts"]
    return result


# ──────────────────────────────────────────────
# 2. Nosozlik xavfini bashorat qilish
# ──────────────────────────────────────────────
def get_risk_assessment(db: Session) -> dict:
    """Aktivlardan foydalanish tarixiga qarab nosozlik xavfini BASHORAT qilish.

    Haqiqiy bashorat elementlari:
    - MTBR (Mean Time Between Repairs) — ta'mirlar orasidagi o'rtacha vaqt
    - Repair trend — nosozlik chastotasi tezlashyaptimi?
    - Predicted next failure — keyingi nosozlik taxmini
    - Similar category failure rate — shu kategoryadagi o'xshash aktivlar statistikasi
    """

    # Barcha faol aktivlar (WRITTEN_OFF bo'lmagan)
    assets = (
        db.query(Asset)
        .filter(Asset.status != AssetStatus.WRITTEN_OFF)
        .all()
    )

    # Barcha ta'mir loglarini bir so'rovda olish (samaradorlik uchun)
    repair_logs = (
        db.query(AuditLog.asset_id, AuditLog.performed_at)
        .filter(AuditLog.action == "STATUS_CHANGED",
                AuditLog.description.like("%IN_REPAIR%"))
        .order_by(AuditLog.performed_at)
        .all()
    )
    # Aktiv bo'yicha ta'mir sanalari
    repair_dates_map: dict[int, list[date]] = {}
    for log in repair_logs:
        rd = log.performed_at.date() if hasattr(log.performed_at, 'date') else log.performed_at
        repair_dates_map.setdefault(log.asset_id, []).append(rd)

    # Qaytarish sonlarini bir so'rovda
    return_counts_q = (
        db.query(AuditLog.asset_id, func.count(AuditLog.id))
        .filter(AuditLog.action == "RETURNED")
        .group_by(AuditLog.asset_id)
        .all()
    )
    return_count_map = {aid: cnt for aid, cnt in return_counts_q}

    # Kategoriya bo'yicha o'rtacha ta'mir statistikasi
    cat_repair_stats: dict[int, dict] = {}  # {cat_id: {"total": N, "repaired": N}}
    for a in assets:
        cid = a.category_id
        if cid not in cat_repair_stats:
            cat_repair_stats[cid] = {"total": 0, "repaired": 0}
        cat_repair_stats[cid]["total"] += 1
        if a.id in repair_dates_map:
            cat_repair_stats[cid]["repaired"] += 1

    # Har bir aktiv uchun bashorat ma'lumotlari
    asset_data = []
    for a in assets:
        repair_dates = repair_dates_map.get(a.id, [])
        repair_count = len(repair_dates)
        return_count = return_count_map.get(a.id, 0)

        # Yosh (oyda)
        age_months = 0
        if a.purchase_date:
            age_months = (date.today().year - a.purchase_date.year) * 12 + \
                         (date.today().month - a.purchase_date.month)
        useful_life = a.category.useful_life_months if (a.category and a.category.useful_life_months) else 60
        warranty_expired = bool(a.warranty_expiry and a.warranty_expiry < date.today())

        # ── MTBR hisoblash (Mean Time Between Repairs) ──
        mtbr_days = None
        repair_trend = "ma'lumot_yetarli_emas"
        if len(repair_dates) >= 2:
            intervals = []
            for i in range(1, len(repair_dates)):
                diff = (repair_dates[i] - repair_dates[i - 1]).days
                if diff > 0:
                    intervals.append(diff)
            if intervals:
                mtbr_days = round(sum(intervals) / len(intervals))
                # Trend aniqlash — oxirgi interval o'rtachadan qisqami?
                if len(intervals) >= 2:
                    recent_interval = intervals[-1]
                    avg_interval = sum(intervals) / len(intervals)
                    if recent_interval < avg_interval * 0.7:
                        repair_trend = "tezlashmoqda"  # xavfli
                    elif recent_interval > avg_interval * 1.3:
                        repair_trend = "sekinlashmoqda"  # yaxshi
                    else:
                        repair_trend = "barqaror"

        # ── Oxirgi ta'mirdan beri o'tgan kunlar ──
        days_since_last_repair = None
        if repair_dates:
            days_since_last_repair = (date.today() - repair_dates[-1]).days

        # ── Keyingi nosozlik bashorati ──
        predicted_next_failure_days = None
        if mtbr_days and days_since_last_repair is not None:
            predicted_next_failure_days = max(0, mtbr_days - days_since_last_repair)
            # Trend tezlashayotgan bo'lsa, bashoratni qisqartirish
            if repair_trend == "tezlashmoqda":
                predicted_next_failure_days = max(0, int(predicted_next_failure_days * 0.6))
        elif repair_count == 1 and days_since_last_repair is not None:
            # Birinchi ta'mirdan beri o'tgan vaqtga qarab taxmin
            predicted_next_failure_days = max(0, days_since_last_repair * 2 - days_since_last_repair)

        # ── O'xshash kategoriya failure rate ──
        cid = a.category_id
        cat_stats = cat_repair_stats.get(cid, {"total": 1, "repaired": 0})
        similar_failure_rate = round(cat_stats["repaired"] / max(cat_stats["total"], 1), 2)

        # ── Kafolat kunlari ──
        warranty_days_remaining = None
        if a.warranty_expiry and a.warranty_expiry >= date.today():
            warranty_days_remaining = (a.warranty_expiry - date.today()).days

        # ── Risk score — bashoratga asoslangan ──
        score = 0
        age_ratio = age_months / useful_life if useful_life > 0 else 0
        score += min(age_ratio * 25, 35)               # Yoshi — max 35
        score += repair_count * 12                       # Ta'mir soni
        score += 10 if warranty_expired else 0           # Kafolat
        score += 5 if a.status == "IN_REPAIR" else 0
        score += 3 if a.status == "LOST" else 0
        # Bashorat bonuslari
        if repair_trend == "tezlashmoqda":
            score += 15  # Tezlashayotgan nosozlik — jiddiy xavf
        if predicted_next_failure_days is not None and predicted_next_failure_days < 30:
            score += 10  # 30 kun ichida nosozlik kutilmoqda
        if similar_failure_rate > 0.4:
            score += 5   # Kategoriyada ko'p nosozlik

        asset_data.append({
            "id": a.id,
            "name": a.name,
            "inventory_number": a.inventory_number,
            "category": a.category.name if a.category else "—",
            "status": a.status,
            "age_months": age_months,
            "useful_life_months": useful_life,
            "age_ratio": round(age_ratio, 2),
            "repair_count": repair_count,
            "return_count": return_count,
            "warranty_expired": warranty_expired,
            "warranty_days_remaining": warranty_days_remaining,
            "purchase_price": float(a.purchase_price) if a.purchase_price else 0,
            # Bashorat maydonlari
            "mtbr_days": mtbr_days,
            "repair_trend": repair_trend,
            "days_since_last_repair": days_since_last_repair,
            "predicted_next_failure_days": predicted_next_failure_days,
            "similar_category_failure_rate": similar_failure_rate,
            "risk_score": min(round(score), 100),
        })

    top_risky = sorted(asset_data, key=lambda x: x["risk_score"], reverse=True)[:15]

    # Umumiy statistika
    summary = {
        "total_active": len(asset_data),
        "avg_age_months": round(sum(a["age_months"] for a in asset_data) / max(len(asset_data), 1)),
        "warranty_expired_count": sum(1 for a in asset_data if a["warranty_expired"]),
        "in_repair_count": sum(1 for a in asset_data if a["status"] == "IN_REPAIR"),
        "high_risk_count": sum(1 for a in asset_data if a["risk_score"] >= 60),
        "accelerating_failure_count": sum(1 for a in asset_data if a["repair_trend"] == "tezlashmoqda"),
        "predicted_failure_30d": sum(1 for a in asset_data
                                     if a["predicted_next_failure_days"] is not None
                                     and a["predicted_next_failure_days"] < 30),
    }

    system = """Sen bank ofisi aktiv boshqaruv tizimining AI BASHORAT tahlilchisisan.
Vazifang: aktivlarning KELAJAKDAGI nosozlik xavfini bashorat qilish — hozirgi holatni emas, KELAJAKNI taxmin qilish.

Har bir aktivda bashorat ma'lumotlari bor:
- mtbr_days: ta'mirlar orasidagi o'rtacha vaqt (Mean Time Between Repairs)
- repair_trend: "tezlashmoqda" = nosozlik chastotasi oshmoqda (XAVFLI), "sekinlashmoqda" = yaxshilanmoqda, "barqaror" = o'zgarishsiz
- predicted_next_failure_days: keyingi nosozlikgacha taxminiy kunlar soni
- similar_category_failure_rate: shu kategoryadagi boshqa aktivlarning nosozlik ulushi (0-1)
- days_since_last_repair: oxirgi ta'mirdan beri o'tgan kunlar

Javobni FAQAT JSON formatda ber:
{"analysis": "<2-3 jumlada BASHORAT umumiy xulosa o'zbekchada — nechta aktiv yaqin kelajakda nosozlikka uchrashi kutilmoqda>",
 "assets": [{"id": <int>, "name": "<str>", "risk_score": <int>,
   "risk_level": "past|o'rta|yuqori|kritik",
   "predicted_failure": "<keyingi nosozlik qachon kutilmoqda — masalan: '30 kun ichida' yoki '3 oy ichida'>",
   "trend": "<nosozlik trendiga asoslangan 1 jumlada izoh — masalan: 'Nosozlik chastotasi tezlashmoqda — oxirgi 2 ta ta'mir orasidagi interval qisqargan'>",
   "recommendation": "<aniq tavsiya o'zbekchada>"}]}
Faqat risk_score >= 30 bo'lganlarni qo'sh. Eng ko'pi 10 ta."""

    user_msg = f"""Umumiy statistika: {json.dumps(summary, ensure_ascii=False)}

Eng xavfli aktivlar (bashorat ma'lumotlari bilan): {json.dumps(top_risky, ensure_ascii=False)}

Bashorat tahlilini qil — har bir xavfli aktiv QACHON nosoz bo'lishi mumkinligini taxmin qil."""

    ai_result = _ask_ai(system, user_msg)
    parsed = _parse_json(ai_result["text"])
    result = parsed or {"analysis": "AI tahlil qila olmadi", "assets": []}
    result["_attempts"] = ai_result["attempts"]
    return result


# ──────────────────────────────────────────────
# 3. Inventarizatsiya va audit uchun tavsiyalar
# ──────────────────────────────────────────────
def get_insights(db: Session) -> dict:
    """AI asosidagi inventarizatsiya va audit tavsiyalari."""

    # Umumiy statistika yig'ish
    total = db.query(func.count(Asset.id)).scalar() or 0
    status_counts = {}
    for s in AssetStatus:
        cnt = db.query(func.count(Asset.id)).filter(Asset.status == s.value).scalar() or 0
        status_counts[s.value] = cnt

    total_value = float(db.query(func.sum(Asset.purchase_price)).scalar() or 0)

    # Kategoriya bo'yicha
    cat_stats = (
        db.query(AssetCategory.name, func.count(Asset.id))
        .join(Asset, Asset.category_id == AssetCategory.id)
        .group_by(AssetCategory.name).all()
    )

    # Bo'lim bo'yicha
    dept_stats = (
        db.query(Department.name, func.count(Asset.id))
        .join(Asset, Asset.current_department_id == Department.id)
        .group_by(Department.name).all()
    )

    # Kafolati tugayotganlar
    expiring_30 = (
        db.query(func.count(Asset.id))
        .filter(Asset.warranty_expiry.isnot(None),
                Asset.warranty_expiry <= date.today() + timedelta(days=30),
                Asset.warranty_expiry >= date.today(),
                Asset.status != AssetStatus.WRITTEN_OFF)
        .scalar() or 0
    )

    # Amortizatsiya muddati o'tganlar
    aging_assets = db.query(Asset).join(AssetCategory).filter(
        Asset.purchase_date.isnot(None),
        Asset.status != AssetStatus.WRITTEN_OFF
    ).all()
    aging_count = 0
    for a in aging_assets:
        age_m = (date.today().year - a.purchase_date.year) * 12 + (date.today().month - a.purchase_date.month)
        useful = a.category.useful_life_months or 60
        if age_m >= useful:
            aging_count += 1

    # Oxirgi 30 kundagi harakatlar
    recent_actions = (
        db.query(AuditLog.action, func.count(AuditLog.id))
        .filter(AuditLog.performed_at >= date.today() - timedelta(days=30))
        .group_by(AuditLog.action).all()
    )

    # ── YANGI: 90 kunda audit logi bo'lmagan aktivlar ──
    active_asset_ids = {a.id for a in db.query(Asset.id).filter(
        Asset.status != AssetStatus.WRITTEN_OFF
    ).all()}
    audited_90d_ids = {row.asset_id for row in db.query(AuditLog.asset_id).filter(
        AuditLog.performed_at >= date.today() - timedelta(days=90)
    ).distinct().all()}
    never_audited_90d = len(active_asset_ids - audited_90d_ids)

    # ── YANGI: Bo'lim bo'yicha audit bo'shliqlari ──
    dept_audit_gaps = []
    for dname, dcount in dept_stats:
        dept_obj = db.query(Department).filter(Department.name == dname).first()
        if not dept_obj:
            continue
        dept_asset_ids = {a.id for a in db.query(Asset.id).filter(
            Asset.current_department_id == dept_obj.id
        ).all()}
        dept_audited = {row.asset_id for row in db.query(AuditLog.asset_id).filter(
            AuditLog.asset_id.in_(dept_asset_ids),
            AuditLog.performed_at >= date.today() - timedelta(days=60)
        ).distinct().all()} if dept_asset_ids else set()
        not_audited = len(dept_asset_ids - dept_audited)
        if not_audited > 0 and dcount > 0:
            dept_audit_gaps.append({
                "department": dname,
                "total_assets": dcount,
                "not_audited_60d": not_audited,
                "audit_gap_percent": round(not_audited / dcount * 100),
            })
    dept_audit_gaps.sort(key=lambda x: x["not_audited_60d"], reverse=True)

    # ── YANGI: Oy-oyga solishtirish ──
    this_month_start = date.today().replace(day=1)
    prev_month_end = this_month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)

    this_month_count = db.query(func.count(AuditLog.id)).filter(
        AuditLog.performed_at >= this_month_start
    ).scalar() or 0
    prev_month_count = db.query(func.count(AuditLog.id)).filter(
        AuditLog.performed_at >= prev_month_start,
        AuditLog.performed_at < this_month_start,
    ).scalar() or 0
    monthly_change = round(
        ((this_month_count - prev_month_count) / max(prev_month_count, 1)) * 100
    )

    stats = {
        "total_assets": total,
        "status_breakdown": status_counts,
        "total_value": total_value,
        "category_distribution": {name: count for name, count in cat_stats},
        "department_distribution": {name: count for name, count in dept_stats},
        "warranty_expiring_30d": expiring_30,
        "aging_past_useful_life": aging_count,
        "recent_30d_actions": {action: count for action, count in recent_actions},
        # Yangi maydonlar
        "never_audited_90d": never_audited_90d,
        "department_audit_gaps": dept_audit_gaps[:5],
        "monthly_comparison": {
            "this_month_actions": this_month_count,
            "prev_month_actions": prev_month_count,
            "change_percent": monthly_change,
        },
    }

    system = """Sen bank ofisi aktiv boshqaruv tizimining AI maslahatchisisan.
Vazifang: inventarizatsiya va audit uchun amaliy tavsiyalar berish.

Qo'shimcha ma'lumotlar taqdim etilgan:
- never_audited_90d: 90 kunda hech qanday audit logi bo'lmagan aktivlar soni — BU MUHIM, agar bor bo'lsa albatta ogohlantir!
- department_audit_gaps: qaysi bo'limlarda audit bo'shliqlari bor — ko'p aktivi bor lekin kam tekshirilgan bo'limlar
- monthly_comparison: bu oylik va o'tgan oylik harakatlar soni solishtirilgan — trend haqida xulosa ber

Javobni FAQAT JSON formatda ber:
{"insights": [
  {"type": "warning|info|success|action", "title": "<qisqa sarlavha>", "description": "<1-2 jumla tavsiya>", "priority": "high|medium|low"}
]}

6-10 ta eng muhim tavsiyalarni ber. O'zbek tilida yoz. Har bir tavsiya aniq va amaliy bo'lsin.
Muhim yo'nalishlar:
- Kafolati tugayotgan aktivlar haqida ogohlantirish
- 90 kunda tekshirilmagan aktivlar — inventarizatsiya zarur
- Bo'limlar orasidagi audit bo'shliqlari — qaysi bo'limda tekshiruv o'tkazilmagan
- Oylik trend — harakatlar ko'payganmi yoki kamayganmi
- Eskirgan aktivlar, ta'mirda turganlar, taqsimot muammolari"""

    user_msg = f"Tizim statistikasi:\n{json.dumps(stats, ensure_ascii=False, indent=2)}"

    ai_result = _ask_ai(system, user_msg)
    parsed = _parse_json(ai_result["text"])
    result = parsed or {"insights": []}
    result["_attempts"] = ai_result["attempts"]
    return result


# ──────────────────────────────────────────────
# 4. Muammoli aktivlarni izohlar orqali aniqlash
# ──────────────────────────────────────────────

# Muammo kalit so'zlari — izoh matnlaridan qidirish uchun
PROBLEM_KEYWORDS = [
    "singan", "nosoz", "buzilgan", "yo'qoldi", "ishlamayapti", "ishlamaydi",
    "shishgan", "yonib ketdi", "topilmadi", "yaroqsiz", "eskirgan",
    "xavfli", "muammo", "shovqin", "qizib ketadi", "qizib ketdi", "sekin",
    "tiqilib", "tiqiladi", "shikoyat", "muzlab", "o'chib qoladi", "o'chib qoldi",
    "chirigan", "yeyilgan", "uziladi", "titreydi", "suyuqlik",
    "ta'mirga yaroqsiz", "almashtirilishi kerak", "foydalanib bo'lmaydi",
]


def _keyword_score(texts: list[str]) -> int:
    """Matnlar ro'yxatidagi muammo kalit so'zlarini hisoblash."""
    score = 0
    combined = " ".join(t.lower() for t in texts if t)
    for kw in PROBLEM_KEYWORDS:
        if kw in combined:
            score += 1
    return score


def get_problematic_assets(db: Session) -> dict:
    """Izohlar va audit tarixini tahlil qilib muammoli aktivlarni aniqlash."""

    # 1) Barcha faol aktivlarni olish (notes va description bilan)
    all_assets = (
        db.query(Asset)
        .filter(Asset.status != AssetStatus.WRITTEN_OFF)
        .all()
    )

    # 2) Audit loglardan voqealar yig'ish
    logs = (
        db.query(
            AuditLog.asset_id,
            AuditLog.action,
            AuditLog.description,
            AuditLog.new_value,
        )
        .filter(AuditLog.action.in_(["STATUS_CHANGED", "RETURNED", "ASSIGNED"]))
        .order_by(AuditLog.performed_at.desc())
        .limit(500)
        .all()
    )
    log_map: dict[int, list[dict]] = {}
    for log in logs:
        log_map.setdefault(log.asset_id, []).append({
            "action": log.action,
            "description": log.description,
        })

    # 3) Assignment izohlarini yig'ish (return_reason va notes)
    assignments = (
        db.query(
            AssetAssignment.asset_id,
            AssetAssignment.return_reason,
            AssetAssignment.notes,
        )
        .filter(AssetAssignment.returned_at.isnot(None))
        .all()
    )
    assign_texts: dict[int, list[str]] = {}
    for asgn in assignments:
        texts = assign_texts.setdefault(asgn.asset_id, [])
        if asgn.return_reason:
            texts.append(asgn.return_reason)
        if asgn.notes:
            texts.append(asgn.notes)

    # 4) Har bir aktiv uchun boy profil yaratish va keyword scoring
    asset_profiles = []
    for a in all_assets:
        # Barcha matnlarni yig'ish
        all_texts = []
        if a.notes:
            all_texts.append(a.notes)
        if a.description:
            all_texts.append(a.description)
        all_texts.extend(assign_texts.get(a.id, []))
        events = log_map.get(a.id, [])
        for ev in events:
            if ev["description"]:
                all_texts.append(ev["description"])

        # Keyword scoring
        kw_score = _keyword_score(all_texts)
        # Voqea soni ham hisobga olinadi
        repair_events = sum(1 for e in events if "IN_REPAIR" in (e.get("description") or ""))
        return_events = sum(1 for e in events if e["action"] == "RETURNED")

        total_score = kw_score * 3 + repair_events * 5 + return_events * 2

        if total_score < 3:
            continue  # Muammosiz aktiv

        asset_profiles.append({
            "id": a.id,
            "name": a.name,
            "inventory_number": a.inventory_number,
            "status": a.status,
            "category": a.category.name if a.category else "—",
            "notes": a.notes,
            "return_reasons": assign_texts.get(a.id, [])[:5],
            "audit_descriptions": [e["description"] for e in events[:8] if e["description"]],
            "keyword_hits": kw_score,
            "repair_count": repair_events,
            "return_count": return_events,
            "problem_score": total_score,
        })

    # Eng yuqori score bo'yicha saralash
    asset_profiles.sort(key=lambda x: x["problem_score"], reverse=True)
    top_assets = asset_profiles[:20]

    system = """Sen bank ofisi aktiv boshqaruv tizimining AI tahlilchisisan.
Vazifang: izohlar, qaytarish sabablari va voqealar tarixini MATN TAHLILI qilib MUAMMOLI aktivlarni aniqlash.

Har bir aktivda quyidagi ma'lumotlar bor:
- notes: aktiv izohi (ENG MUHIM — bu yerda muammolar yozilgan)
- return_reasons: qaytarish sabablari ro'yxati
- audit_descriptions: audit log tavsiflari
- keyword_hits: muammo kalit so'zlari soni
- repair_count: ta'mirga tushish soni
- return_count: qaytarilish soni

IZOH MATNLARINI CHUQUR TAHLIL QIL:
- Salbiy kalit so'zlar: singan, nosoz, buzilgan, ishlamaydi, shishgan, eskirgan, xavfli
- Muammo eskalatsiyasi: bir xil muammo qaytarilayotganligi (masalan: "ta'mir qilindi" → "yana buzildi")
- Qaytarish sabablarida salbiy belgilar

Javobni FAQAT JSON formatda ber:
{"problematic_assets": [
  {"id": <int>, "name": "<str>", "inventory_number": "<str>",
   "problem_type": "tez-tez ta'mir|yo'qolish xavfi|tez-tez almashinish|nosoz|izoh bo'yicha muammoli",
   "severity": "yuqori|o'rta|past",
   "reason": "<1-2 jumlada IZOH MATNLARIDAN aniqlangan muammo o'zbekchada>",
   "recommendation": "<aniq tavsiya>"}
],
"summary": "<umumiy xulosa 2-3 jumla — nechta muammoli, asosiy muammo turlari>"}

Faqat haqiqatan muammoli deb topilganlarni ko'rsat (3-10 ta). IZOH matnlariga asoslan!"""

    user_msg = f"Aktivlar va ularning izoh/voqea profillari:\n{json.dumps(top_assets, ensure_ascii=False, indent=2)}"

    ai_result = _ask_ai(system, user_msg)
    parsed = _parse_json(ai_result["text"])
    result = parsed or {"problematic_assets": [], "summary": "AI tahlil qila olmadi"}
    result["_attempts"] = ai_result["attempts"]
    return result


# ──────────────────────────────────────────────
# 5. AI Chatbot — tabiiy tilda savol-javob
# ──────────────────────────────────────────────

def _detect_chat_intent(message: str) -> str:
    """Foydalanuvchi xabaridan maqsadni aniqlash."""
    msg = message.lower()

    # Aktiv qidirish — inventar raqam, serial, aniq nom
    if any(k in msg for k in ["bnk-", "inv-", "inventar", "serial", "nomer", "raqam",
                                "qidirish", "qidir", "topib ber"]):
        return "asset_search"

    # Xodim yoki bo'lim bo'yicha savol
    if any(k in msg for k in ["xodim", "hodim", "emp-", "kim", "qaysi xodim",
                                "kimda", "kimga", "biriktirilgan"]):
        return "employee_query"

    # Bo'lim haqida savol
    if any(k in msg for k in ["bo'lim", "bolim", "department", "it bo'lim",
                                "moliya", "kredit", "xavfsizlik", "kassir", "hr"]):
        return "department_query"

    # Davr solishtirish
    if any(k in msg for k in ["oldingi oy", "o'tgan oy", "otgan oy", "solishtir",
                                "taqqos", "oylik", "o'zgarish", "trend", "dinamika"]):
        return "period_comparison"

    # Filtr / ro'yxat
    if any(k in msg for k in ["ro'yxat", "royxat", "filter", "ko'rsat", "qaysilar",
                                "barcha", "hammasi", "ta'mirda", "kafolat",
                                "eng qimmat", "eng arzon", "eng eski"]):
        return "filter_list"

    return "general_stats"


def _search_assets(db: Session, message: str) -> list[dict]:
    """Xabardagi kalit so'z bo'yicha aktivlarni qidirish."""
    # Inventar raqamni ajratish (BNK-XXX-YYYY-ZZZZ pattern)
    inv_match = re.search(r'(BNK-\w+-\w+-\w+)', message, re.IGNORECASE)
    if inv_match:
        search_term = inv_match.group(1)
        assets = db.query(Asset).filter(
            Asset.inventory_number.ilike(f"%{search_term}%")
        ).limit(5).all()
    else:
        # Umumiy qidirish — nomdan
        words = [w for w in message.split() if len(w) > 2 and w.lower() not in
                 ("qidirish", "qidir", "topib", "ber", "haqida", "nomer", "raqam",
                  "inventar", "serial", "aktiv", "aktivni")]
        if not words:
            return []
        search_term = words[0]
        assets = db.query(Asset).filter(
            (Asset.name.ilike(f"%{search_term}%")) |
            (Asset.inventory_number.ilike(f"%{search_term}%")) |
            (Asset.serial_number.ilike(f"%{search_term}%"))
        ).limit(5).all()

    results = []
    for a in assets:
        results.append({
            "id": a.id,
            "name": a.name,
            "inventory_number": a.inventory_number,
            "serial_number": a.serial_number,
            "status": a.status,
            "category": a.category.name if a.category else "—",
            "purchase_price": float(a.purchase_price) if a.purchase_price else None,
            "purchase_date": str(a.purchase_date) if a.purchase_date else None,
            "warranty_expiry": str(a.warranty_expiry) if a.warranty_expiry else None,
            "current_employee": a.current_employee.full_name if a.current_employee else None,
            "current_department": a.current_department.name if a.current_department else None,
            "current_branch": a.current_branch.name if a.current_branch else None,
            "notes": a.notes,
        })
    return results


def _search_employees(db: Session, message: str) -> list[dict]:
    """Xodim bo'yicha qidirish — kimda qancha aktiv bor."""
    words = [w for w in message.split() if len(w) > 2 and w.lower() not in
             ("xodim", "hodim", "kimda", "kimga", "qancha", "aktiv", "bor", "haqida")]

    if words:
        search = words[0]
        employees = db.query(Employee).filter(
            (Employee.full_name.ilike(f"%{search}%")) |
            (Employee.employee_code.ilike(f"%{search}%"))
        ).limit(5).all()
    else:
        # Eng ko'p aktivi bo'lgan xodimlar
        employees = (
            db.query(Employee)
            .join(Asset, Asset.current_employee_id == Employee.id)
            .group_by(Employee.id)
            .order_by(func.count(Asset.id).desc())
            .limit(5)
            .all()
        )

    results = []
    for emp in employees:
        asset_count = db.query(func.count(Asset.id)).filter(
            Asset.current_employee_id == emp.id
        ).scalar() or 0
        emp_assets = db.query(Asset.name, Asset.inventory_number, Asset.status).filter(
            Asset.current_employee_id == emp.id
        ).limit(10).all()

        results.append({
            "full_name": emp.full_name,
            "employee_code": emp.employee_code,
            "position": emp.position,
            "department": emp.department.name if emp.department else "—",
            "asset_count": asset_count,
            "assets": [{"name": a.name, "inv": a.inventory_number, "status": a.status}
                       for a in emp_assets],
        })
    return results


def _get_department_info(db: Session, message: str) -> list[dict]:
    """Bo'lim bo'yicha batafsil ma'lumot."""
    msg = message.lower()
    # Aniq bo'lim nomini aniqlash
    dept_keywords = {
        "it": "IT", "moliya": "Moliya", "kredit": "Kredit",
        "xavfsizlik": "Xavfsizlik", "kassir": "Kassir", "hr": "HR",
    }
    target_dept = None
    for kw, dept_name in dept_keywords.items():
        if kw in msg:
            target_dept = dept_name
            break

    if target_dept:
        departments = db.query(Department).filter(
            Department.name.ilike(f"%{target_dept}%")
        ).all()
    else:
        departments = db.query(Department).limit(10).all()

    results = []
    for dept in departments:
        assets_q = db.query(Asset).filter(Asset.current_department_id == dept.id)
        total = assets_q.count()
        status_dist = {}
        for s in AssetStatus:
            cnt = assets_q.filter(Asset.status == s.value).count()
            if cnt > 0:
                status_dist[s.value] = cnt
        total_value = float(assets_q.with_entities(func.sum(Asset.purchase_price)).scalar() or 0)

        results.append({
            "department": dept.name,
            "branch": dept.branch.name if dept.branch else "—",
            "total_assets": total,
            "status_breakdown": status_dist,
            "total_value": total_value,
        })
    return results


def _compare_periods(db: Session) -> dict:
    """Bu oy va o'tgan oyni solishtirish."""
    this_month_start = date.today().replace(day=1)
    prev_month_end = this_month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)

    def _period_stats(start: date, end: date) -> dict:
        base = db.query(AuditLog).filter(
            AuditLog.performed_at >= start,
            AuditLog.performed_at < end,
        )
        total_actions = base.count()
        new_assets = base.filter(AuditLog.action == "CREATED").count()
        repairs = base.filter(AuditLog.action == "STATUS_CHANGED",
                              AuditLog.description.like("%IN_REPAIR%")).count()
        assignments = base.filter(AuditLog.action == "ASSIGNED").count()
        returns = base.filter(AuditLog.action == "RETURNED").count()
        return {
            "jami_harakatlar": total_actions,
            "yangi_aktivlar": new_assets,
            "tamir": repairs,
            "biriktirishlar": assignments,
            "qaytarishlar": returns,
        }

    return {
        "bu_oy": _period_stats(this_month_start, date.today() + timedelta(days=1)),
        "otgan_oy": _period_stats(prev_month_start, this_month_start),
    }


def _filter_assets(db: Session, message: str) -> list[dict]:
    """Xabar asosida aktivlarni filtrlash."""
    msg = message.lower()
    query = db.query(Asset).filter(Asset.status != AssetStatus.WRITTEN_OFF)

    if "ta'mirda" in msg or "tamir" in msg:
        query = query.filter(Asset.status == AssetStatus.IN_REPAIR)
    elif "yo'qolgan" in msg or "lost" in msg:
        query = query.filter(Asset.status == AssetStatus.LOST)
    elif "kafolat" in msg:
        query = query.filter(
            Asset.warranty_expiry.isnot(None),
            Asset.warranty_expiry <= date.today() + timedelta(days=30),
            Asset.warranty_expiry >= date.today(),
        )
    elif "eng qimmat" in msg:
        query = query.order_by(Asset.purchase_price.desc())
    elif "eng arzon" in msg:
        query = query.order_by(Asset.purchase_price.asc())
    elif "eng eski" in msg:
        query = query.order_by(Asset.purchase_date.asc())

    assets = query.limit(15).all()
    return [{
        "name": a.name,
        "inventory_number": a.inventory_number,
        "status": a.status,
        "category": a.category.name if a.category else "—",
        "purchase_price": float(a.purchase_price) if a.purchase_price else None,
        "current_employee": a.current_employee.full_name if a.current_employee else "Biriktirilmagan",
        "current_department": a.current_department.name if a.current_department else "—",
    } for a in assets]


def chat_with_ai(db: Session, user_message: str) -> dict:
    """Foydalanuvchi savoliga tizim ma'lumotlari asosida javob berish.
    Intent-based kontekst boyitish bilan — umumiy statistika + aniq ma'lumotlar.
    """

    # ── Intent aniqlash ──
    intent = _detect_chat_intent(user_message)

    # ── Har doim: asosiy statistika ──
    total_assets = db.query(func.count(Asset.id)).scalar() or 0
    status_counts = {}
    for s in AssetStatus:
        cnt = db.query(func.count(Asset.id)).filter(Asset.status == s.value).scalar() or 0
        if cnt > 0:
            status_counts[s.value] = cnt

    total_value = float(db.query(func.sum(Asset.purchase_price)).scalar() or 0)

    cat_stats = (
        db.query(AssetCategory.name, func.count(Asset.id))
        .join(Asset, Asset.category_id == AssetCategory.id)
        .group_by(AssetCategory.name).all()
    )
    dept_stats = (
        db.query(Department.name, func.count(Asset.id))
        .join(Asset, Asset.current_department_id == Department.id)
        .group_by(Department.name).all()
    )
    branch_stats = (
        db.query(Branch.name, func.count(Asset.id))
        .join(Asset, Asset.current_branch_id == Branch.id)
        .group_by(Branch.name).all()
    )
    total_employees = db.query(func.count(Employee.id)).filter(Employee.is_active == True).scalar() or 0
    expiring_30 = (
        db.query(func.count(Asset.id))
        .filter(Asset.warranty_expiry.isnot(None),
                Asset.warranty_expiry <= date.today() + timedelta(days=30),
                Asset.warranty_expiry >= date.today(),
                Asset.status != AssetStatus.WRITTEN_OFF)
        .scalar() or 0
    )

    context = {
        "bugungi_sana": str(date.today()),
        "jami_aktivlar": total_assets,
        "status_taqsimoti": status_counts,
        "jami_qiymat_som": total_value,
        "kategoriya_taqsimoti": {name: count for name, count in cat_stats},
        "bolim_taqsimoti": {name: count for name, count in dept_stats},
        "filial_taqsimoti": {name: count for name, count in branch_stats},
        "faol_xodimlar_soni": total_employees,
        "kafolati_tugayotganlar_30_kun": expiring_30,
    }

    # ── Intent bo'yicha qo'shimcha kontekst ──
    intent_label = "umumiy_statistika"
    if intent == "asset_search":
        context["qidiruv_natijalari"] = _search_assets(db, user_message)
        intent_label = "aktiv_qidirish"
    elif intent == "employee_query":
        context["xodim_malumotlari"] = _search_employees(db, user_message)
        intent_label = "xodim_savoli"
    elif intent == "department_query":
        context["bolim_batafsil"] = _get_department_info(db, user_message)
        intent_label = "bolim_savoli"
    elif intent == "period_comparison":
        context["davr_solishtirish"] = _compare_periods(db)
        intent_label = "davr_solishtirish"
    elif intent == "filter_list":
        context["filtrlangan_aktivlar"] = _filter_assets(db, user_message)
        intent_label = "filtr_royxat"

    system = f"""Sen bank ofisi aktiv boshqaruv tizimining AI yordamchisisan. Ismingni "AI Yordamchi" deb ataysan.
Vazifang: foydalanuvchi savollariga tizim ma'lumotlari asosida aniq va foydali javob berish.

Aniqlangan savol turi: {intent_label}

Qoidalar:
- FAQAT o'zbek tilida javob ber
- Javobni FAQAT JSON formatda ber: {{"answer": "<javob matni>", "suggestions": ["<taklif 1>", "<taklif 2>", "<taklif 3>"]}}
- Javob qisqa, aniq va foydali bo'lsin (2-5 jumla)
- suggestions — foydalanuvchi keyingi qo'yishi mumkin bo'lgan 2-3 ta savol
- Agar savol tizimga tegishli bo'lmasa, muloyimlik bilan aktiv boshqaruviga yo'naltir
- Raqamlar va statistikalarni aniq ko'rsat
- Markdown formatdan foydalanma, oddiy matn yoz

Maxsus yo'riqnomalar:
- Agar "qidiruv_natijalari" bo'lsa — topilgan aktivlar haqida BATAFSIL javob ber (nom, inventar raqam, status, kimda, narx)
- Agar "xodim_malumotlari" bo'lsa — xodim va uning aktivlari haqida javob ber
- Agar "bolim_batafsil" bo'lsa — bo'lim statistikasi, aktiv soni, qiymati haqida javob ber
- Agar "davr_solishtirish" bo'lsa — bu oy va o'tgan oy orasidagi farqni tahlil qil (ko'payish/kamayish %)
- Agar "filtrlangan_aktivlar" bo'lsa — ro'yxatni chiroyli formatda ko'rsat (nom, inventar, status)"""

    user_msg = f"""Tizim ma'lumotlari:
{json.dumps(context, ensure_ascii=False, indent=2)}

Foydalanuvchi savoli: {user_message}"""

    ai_result = _ask_ai(system, user_msg)
    parsed = _parse_json(ai_result["text"])
    result = parsed or {"answer": "Kechirasiz, savolingizga javob bera olmadim. Iltimos, qayta urinib ko'ring.", "suggestions": []}
    result["_attempts"] = ai_result["attempts"]
    return result


# ──────────────────────────────────────────────
# 6. Aktiv avtomatik to'ldirish (auto-fill)
# ──────────────────────────────────────────────
def auto_fill_asset(db: Session, name: str) -> dict:
    """Aktiv nomi asosida barcha maydonlarni AI orqali tavsiya qilish."""
    categories = db.query(AssetCategory).filter(AssetCategory.is_active == True).all()
    cat_list = [{"id": c.id, "name": c.name, "code": c.code,
                 "description": c.description, "useful_life_months": c.useful_life_months}
                for c in categories]

    system = """Sen bank ofisi aktiv boshqaruv tizimining AI yordamchisisan.
Vazifang: aktiv nomi asosida qolgan maydonlarni aqlli tarzda to'ldirish.

Javobni FAQAT JSON formatda ber:
{
  "category_id": <int yoki null>,
  "category_name": "<str>",
  "description": "<aktivni tavsiflovchi 1-2 jumla o'zbekchada>",
  "estimated_price_uzs": <taxminiy narx so'mda yoki null>,
  "useful_life_months": <foydali umr oyda yoki null>,
  "confidence": <0-100>,
  "reason": "<qisqa tushuntirish o'zbekchada>"
}

Qoidalar:
- category_id mavjud kategoriyalar ichidan bo'lsin
- Narxni O'zbekiston bozor narxlariga yaqin qilib taxmin qil (so'mda)
- Tavsif professional va aniq bo'lsin
- Foydali umrni kategoriyaga mos qil"""

    user_msg = f"""Mavjud kategoriyalar: {json.dumps(cat_list, ensure_ascii=False)}

Aktiv nomi: {name}

Barcha maydonlarni to'ldir."""

    ai_result = _ask_ai(system, user_msg)
    parsed = _parse_json(ai_result["text"])
    result = parsed or {
        "category_id": None, "category_name": None,
        "description": None, "estimated_price_uzs": None,
        "useful_life_months": None, "confidence": 0,
        "reason": "AI tahlil qila olmadi"
    }
    result["_attempts"] = ai_result["attempts"]
    return result


