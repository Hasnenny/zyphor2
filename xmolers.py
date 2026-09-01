#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════════
#   🔥 MCV FUND PRO — النسخة الاحترافية V6
#   ✨ دعم متعدد المواقع | قناة الطلبات | عداد الطلبات | قاعدة البيانات
#   🎯 عجلة حظ محسنة | إضافة قنوات | دعم مواقع متعددة
#   🛍️ متجر مستقل بمنتجات خاصة | موافقة أدمن على كل الطلبات
#   📦 يتطلب: pyTelegramBotAPI >= 4.32 | Python 3.7+
# ══════════════════════════════════════════════════════════════════

import telebot
import threading
import time
import sqlite3
import random
import string
import requests
import math
import json
from datetime import datetime, date
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

# ══════════════════════════════════════════════════════════════════
#   1. الإعدادات الافتراضية
# ══════════════════════════════════════════════════════════════════
class config:
    BOT_TOKEN          = "8858062921:AAEnAsofuyxplg_rKpEkenmc8As5QPOiQZ8" 
    ADMIN_IDS          = [7618293197]
    BOT_NAME           = "بوت رشق ترند"
    BOT_USERNAME       = "@bdfbsdgbot"
    DB_PATH            = "pluspro.db"
    REFERRAL_POINTS    = 50
    WELCOME_POINTS     = 10
    DAILY_GIFT_POINTS  = 5
    WEEKLY_GIFT_POINTS = 50
    POINTS_PER_1000    = 10
    TRACK_MESSAGES     = True


# ══════════════════════════════════════════════════════════════════
#   2. دعم مواقع SMM متعددة
# ══════════════════════════════════════════════════════════════════
class smm:
    STATUS_MAP = {
        "Pending": "قيد الانتظار",
        "In progress": "قيد التنفيذ",
        "Completed": "مكتمل",
        "Partial": "مكتمل جزئياً",
        "Canceled": "ملغي",
        "Processing": "جاري المعالجة",
        "pending": "قيد الانتظار",
        "inprogress": "قيد التنفيذ",
        "completed": "مكتمل",
        "partial": "مكتمل جزئياً",
        "canceled": "ملغي",
    }

    @classmethod
    def _get_sites(cls):
        """إرجاع قائمة المواقع المتاحة"""
        try:
            conn = db.get_conn()
            rows = conn.execute(
                "SELECT * FROM smm_sites WHERE is_active=1 ORDER BY id"
            ).fetchall()
            conn.close()
            return rows
        except:
            return []

    @classmethod
    def _get_default_site(cls):
        """الموقع الافتراضي"""
        sites = cls._get_sites()
        if sites:
            return sites[0]
        return None

    @classmethod
    def _post(cls, url, api_key, action, **params):
        data = {"key": api_key, "action": action, **params}
        try:
            r = requests.post(url, data=data, timeout=15)
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def get_balance(cls, site_id=None):
        """رصيد موقع معين أو الافتراضي"""
        try:
            if site_id:
                conn = db.get_conn()
                site = conn.execute("SELECT * FROM smm_sites WHERE id=?", (site_id,)).fetchone()
                conn.close()
            else:
                site = cls._get_default_site()
            if not site:
                return 0.0
            r = cls._post(site["api_url"], site["api_key"], "balance")
            return float(r.get("balance", 0))
        except:
            return 0.0

    @classmethod
    def create_order(cls, svc_api_id, link, qty, site_id=None):
        """إنشاء طلب"""
        try:
            if site_id:
                conn = db.get_conn()
                site = conn.execute("SELECT * FROM smm_sites WHERE id=?", (site_id,)).fetchone()
                conn.close()
            else:
                site = cls._get_default_site()
            if not site:
                return {"error": "لا يوجد موقع API مفعّل"}
            return cls._post(site["api_url"], site["api_key"], "add",
                             service=svc_api_id, link=link, quantity=qty)
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def get_status(cls, order_id, site_id=None):
        """حالة الطلب"""
        try:
            if site_id:
                conn = db.get_conn()
                site = conn.execute("SELECT * FROM smm_sites WHERE id=?", (site_id,)).fetchone()
                conn.close()
            else:
                site = cls._get_default_site()
            if not site:
                return {}
            return cls._post(site["api_url"], site["api_key"], "status", order=order_id)
        except:
            return {}

    @classmethod
    def get_services_list(cls, site_id=None):
        """قائمة خدمات الموقع"""
        try:
            if site_id:
                conn = db.get_conn()
                site = conn.execute("SELECT * FROM smm_sites WHERE id=?", (site_id,)).fetchone()
                conn.close()
            else:
                site = cls._get_default_site()
            if not site:
                return []
            r = cls._post(site["api_url"], site["api_key"], "services")
            return r if isinstance(r, list) else []
        except:
            return []

    @classmethod
    def get_service_info(cls, svc_id, site_id=None):
        """معلومات خدمة معينة"""
        services = cls.get_services_list(site_id)
        sid = str(svc_id).strip()
        for s in services:
            if str(s.get("service", "")).strip() == sid:
                return s
        return None

    @classmethod
    def arabic_status(cls, s):
        return cls.STATUS_MAP.get(s, s)


# ══════════════════════════════════════════════════════════════════
#   3. قاعدة البيانات
# ══════════════════════════════════════════════════════════════════
class DictRow(dict):
    """صف يدعم الوصول بالاسم والفهرس الرقمي و .get() معاً."""
    __slots__ = ("_keys",)

    def __init__(self, keys, values):
        super().__init__(zip(keys, values))
        self._keys = keys

    def __getitem__(self, key):
        if isinstance(key, int):
            return super().__getitem__(self._keys[key])
        return super().__getitem__(key)


def _dict_row_factory(cursor, row):
    keys = [col[0] for col in cursor.description]
    return DictRow(keys, row)


class db:
    @classmethod
    def get_conn(cls):
        conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        conn.row_factory = _dict_row_factory
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @classmethod
    def init_db(cls):
        conn = cls.get_conn()
        c = conn.cursor()

        # ── المستخدمون ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id            INTEGER UNIQUE NOT NULL,
                username         TEXT DEFAULT '',
                full_name        TEXT DEFAULT '',
                balance          REAL    DEFAULT 0.0,
                points           INTEGER DEFAULT 0,
                referral_code    TEXT    UNIQUE,
                referred_by      INTEGER,
                join_date        TEXT    DEFAULT CURRENT_TIMESTAMP,
                is_banned        INTEGER DEFAULT 0,
                last_daily_gift  TEXT    DEFAULT '',
                last_weekly_gift TEXT    DEFAULT '',
                last_wheel_spin  TEXT    DEFAULT ''
            )
        """)

        # ── الطلبات ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                service_id    TEXT    NOT NULL,
                service_name  TEXT    DEFAULT '',
                app_name      TEXT    DEFAULT '',
                link          TEXT    NOT NULL,
                quantity      INTEGER NOT NULL,
                charge        REAL    NOT NULL DEFAULT 0,
                points_used   INTEGER DEFAULT 0,
                status        TEXT    DEFAULT 'pending',
                pending_approval INTEGER DEFAULT 1,
                api_order_id  TEXT,
                site_id       INTEGER DEFAULT NULL,
                notified_done INTEGER DEFAULT 0,
                created_at    TEXT    DEFAULT CURRENT_TIMESTAMP,
                updated_at    TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── مواقع SMM ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS smm_sites (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                api_url    TEXT NOT NULL,
                api_key    TEXT NOT NULL,
                is_active  INTEGER DEFAULT 1,
                is_default INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── الإعدادات ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # ── القنوات الإجبارية ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS mandatory_channels (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id      TEXT UNIQUE NOT NULL,
                channel_name    TEXT NOT NULL,
                channel_url     TEXT NOT NULL,
                target_members  INTEGER DEFAULT 0,
                current_members INTEGER DEFAULT 0,
                added_at        TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── قنوات النقاط ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS points_channels (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id    TEXT UNIQUE NOT NULL,
                channel_name  TEXT NOT NULL,
                channel_url   TEXT NOT NULL,
                points_reward INTEGER DEFAULT 20,
                added_at      TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS user_channel_points (
                user_id    INTEGER NOT NULL,
                channel_id TEXT NOT NULL,
                earned_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, channel_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS mandatory_joins (
                user_id    INTEGER NOT NULL,
                channel_id TEXT NOT NULL,
                joined_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, channel_id)
            )
        """)

        # ── الأقسام (Apps) ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS apps (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                emoji      TEXT DEFAULT '📱',
                is_active  INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── خدمات الأقسام ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS app_services (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id           INTEGER NOT NULL,
                name             TEXT NOT NULL,
                emoji            TEXT DEFAULT '',
                api_service_id   TEXT NOT NULL,
                site_id          INTEGER DEFAULT NULL,
                points_per_1000  INTEGER NOT NULL DEFAULT 10,
                min_qty          INTEGER NOT NULL DEFAULT 100,
                max_qty          INTEGER NOT NULL DEFAULT 100000,
                rate_per_1000    REAL    DEFAULT 0.5,
                is_active        INTEGER DEFAULT 1,
                created_at       TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (app_id) REFERENCES apps(id) ON DELETE CASCADE
            )
        """)

        # ── روابط الهدايا ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS gift_links (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                code        TEXT    NOT NULL UNIQUE,
                points      INTEGER NOT NULL DEFAULT 0,
                max_uses    INTEGER DEFAULT -1,
                used_count  INTEGER DEFAULT 0,
                is_active   INTEGER DEFAULT 1,
                note        TEXT    DEFAULT '',
                created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS gift_link_claims (
                user_id  INTEGER NOT NULL,
                code     TEXT    NOT NULL,
                claimed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, code)
            )
        """)

        # ── روابط الدعوة ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS invite_links (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                code          TEXT UNIQUE NOT NULL,
                points_reward INTEGER NOT NULL,
                max_uses      INTEGER DEFAULT 0,
                current_uses  INTEGER DEFAULT 0,
                is_active     INTEGER DEFAULT 1,
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_invite_claims (
                user_id     INTEGER NOT NULL,
                invite_code TEXT NOT NULL,
                claimed_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, invite_code)
            )
        """)

        # ── كوبونات الخصم ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS coupons (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                code        TEXT    NOT NULL UNIQUE,
                discount    INTEGER NOT NULL DEFAULT 10,
                max_uses    INTEGER DEFAULT -1,
                used_count  INTEGER DEFAULT 0,
                is_active   INTEGER DEFAULT 1,
                created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS coupon_uses (
                user_id    INTEGER NOT NULL,
                coupon_id  INTEGER NOT NULL,
                used_at    TEXT    DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, coupon_id)
            )
        """)

        # ── طلبات شحن الرصيد ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS recharge_requests (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                amount      REAL    DEFAULT 0,
                points      INTEGER DEFAULT 0,
                method      TEXT    DEFAULT 'vodafone',
                photo_id    TEXT    DEFAULT '',
                status      TEXT    DEFAULT 'pending',
                note        TEXT    DEFAULT '',
                created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS store_products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                description TEXT DEFAULT '',
                emoji       TEXT DEFAULT '🛍️',
                price       INTEGER NOT NULL DEFAULT 0,
                stock       INTEGER DEFAULT -1,
                is_active   INTEGER DEFAULT 1,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── طلبات المتجر ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS store_orders (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id          INTEGER NOT NULL,
                product_id       INTEGER NOT NULL,
                product_name     TEXT DEFAULT '',
                points_used      INTEGER DEFAULT 0,
                status           TEXT DEFAULT 'pending_approval',
                pending_approval INTEGER DEFAULT 1,
                notified_done    INTEGER DEFAULT 0,
                created_at       TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── سجل الإحالات ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS referral_log (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id     INTEGER NOT NULL,
                referred_id     INTEGER NOT NULL,
                points_awarded  INTEGER NOT NULL,
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(referrer_id, referred_id)
            )
        """)

        # ── جوائز عجلة الحظ ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS wheel_prizes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                points     INTEGER NOT NULL,
                weight     REAL    NOT NULL DEFAULT 10,
                emoji      TEXT    DEFAULT '',
                label      TEXT    DEFAULT '',
                is_active  INTEGER DEFAULT 1,
                created_at TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        n = c.execute("SELECT COUNT(*) FROM wheel_prizes").fetchone()[0]
        if n == 0:
            defaults = [
                (10,  30, '🟤', 'عادي'),
                (25,  20, '⚪', 'جيد'),
                (50,  15, '🟢', 'ممتاز'),
                (100, 10, '🔵', 'رائع'),
                (200,  6, '🟡', 'كبير'),
                (500,  3, '🟠', 'ضخم'),
                (1000, 1, '🔴', 'جائزة كبرى'),
            ]
            for pts, w, em, lbl in defaults:
                c.execute("INSERT INTO wheel_prizes (points,weight,emoji,label) VALUES(?,?,?,?)",
                          (pts, w, em, lbl))

        # ── الخدمات المجانية ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS free_services (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                name           TEXT NOT NULL,
                description    TEXT DEFAULT '',
                api_service_id TEXT DEFAULT '',
                site_id        INTEGER DEFAULT NULL,
                daily_limit    INTEGER DEFAULT 1,
                min_qty        INTEGER DEFAULT 100,
                max_qty        INTEGER DEFAULT 1000,
                is_active      INTEGER DEFAULT 1,
                created_at     TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS user_free_claims (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                service_id   INTEGER NOT NULL,
                claim_date   TEXT NOT NULL,
                quantity     INTEGER DEFAULT 0,
                link         TEXT DEFAULT '',
                api_order_id TEXT DEFAULT '',
                status       TEXT DEFAULT 'pending',
                created_at   TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── الأدمنية المتعددة ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS extra_admins (
                tg_id      INTEGER PRIMARY KEY,
                full_name  TEXT DEFAULT '',
                added_at   TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── قنوات الطلبات ──
        c.execute("""
            CREATE TABLE IF NOT EXISTS order_channels (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE NOT NULL,
                channel_name TEXT NOT NULL,
                is_active  INTEGER DEFAULT 1,
                added_at   TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── الإعدادات الافتراضية ──
        defaults = {
            "service_id":             "",
            "service_name":           "تمويل قنوات وجروبات",
            "service_min":            "100",
            "service_max":            "100000",
            "updates_channel":        "",
            "support_username":       "@ssusus",
            "bot_active":             "1",
            "rate_per_1000":          "0.5",
            "points_per_1000":        "10",
            "referral_points":        "50",
            "daily_gift_points":      "5",
            "weekly_gift_points":     "50",
            "welcome_points":         "10",
            "wheel_cooldown_hrs":     "6",
            "free_svc_enabled":          "1",
            "free_services_daily_limit": "3",
            "points_charge_info":        "لشحن النقاط تواصل مع الدعم",
            "charge_asia_info":          "07725066520",
            "charge_atheer_info":        "07864423033",
            "charge_zaincash_info":      "07864423033",
            "charge_master_info":        "1628715409",
            "agent_username":            "ssusus",
            "charge_vodafone_info":      "اسيا: 07725066520",
            "charge_stars_info":         "نجوم: تواصل مع @ssusus",
            "auto_approve_orders":       "0",
            "terms_text":                "",
            "low_points_alert":          "50",
            "daily_report_enabled":      "1",
            "stars_per_point":           "10",
        }
        for k, v in defaults.items():
            c.execute("INSERT OR IGNORE INTO config(key,value) VALUES(?,?)", (k, v))

        # ── موقع افتراضي (SMMParty) ──
        n2 = c.execute("SELECT COUNT(*) FROM smm_sites").fetchone()[0]
        if n2 == 0:
            c.execute("""INSERT INTO smm_sites (name, api_url, api_key, is_active, is_default)
                VALUES (?, ?, ?, 1, 1)""",
                ("SMMParty", "https://smmparty.com/api/v2", "d7ab98d24cdd1c95804bc75b26edc456"))

        conn.commit()
        conn.close()

    # ─── إضافة أعمدة قديمة إن لم تكن موجودة ─────────────────────
    @classmethod
    def _safe_add_col(cls, table, col, typ):
        try:
            conn = cls.get_conn()
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
            conn.commit()
            conn.close()
        except:
            pass

    # ─── المستخدمون ──────────────────────────────────────────────
    @classmethod
    def get_user(cls, tg_id):
        conn = cls.get_conn()
        u = conn.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        conn.close()
        return u

    @classmethod
    def get_user_by_username(cls, username):
        conn = cls.get_conn()
        uname = username.lstrip("@").lower()
        u = conn.execute("SELECT * FROM users WHERE LOWER(username)=?", (uname,)).fetchone()
        conn.close()
        return u

    @classmethod
    def create_user(cls, tg_id, username, full_name, ref_code=None):
        my_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        referred_by = None
        if ref_code:
            conn = cls.get_conn()
            r = conn.execute("SELECT tg_id FROM users WHERE referral_code=?", (ref_code,)).fetchone()
            conn.close()
            if r and r["tg_id"] != tg_id:
                referred_by = r["tg_id"]
        conn = cls.get_conn()
        try:
            welcome_pts = int(cls.get_config("welcome_points", "10"))
            conn.execute("""INSERT INTO users(tg_id,username,full_name,referral_code,referred_by,points)
                VALUES(?,?,?,?,?,?)""",
                (tg_id, username or '', full_name or '', my_code, referred_by, welcome_pts))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return None
        # النقاط لا تُضاف هنا — تُضاف بعد التحقق من الاشتراك الإجباري عبر complete_referral
        conn.close()
        return referred_by

    @classmethod
    def complete_referral(cls, tg_id):
        """تُستدعى بعد اجتياز الاشتراك الإجباري — تضيف نقاط الإحالة للمُحيل مرة واحدة فقط فقط.
        ملاحظة أمان: نعتمد على rowcount لعملية INSERT OR IGNORE بدل فحص وجود منفصل، لمنع
        إمكانية إضافة النقاط أكثر من مرة عند الضغط المتكرر/المتزامن على زر (تحقق من الاشتراك)."""
        conn = cls.get_conn()
        u = conn.execute("SELECT referred_by FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        if not u or not u["referred_by"]:
            conn.close()
            return None
        referred_by = u["referred_by"]
        pts = int(cls.get_config("referral_points", "50"))
        try:
            cur = conn.execute(
                "INSERT OR IGNORE INTO referral_log(referrer_id,referred_id,points_awarded) VALUES(?,?,?)",
                (referred_by, tg_id, pts))
            if cur.rowcount == 0:
                # سجل موجود مسبقاً (تم منحه من قبل) — لا نضيف نقاط مرة أخرى
                conn.commit()
                conn.close()
                return None
            conn.execute("UPDATE users SET points=points+? WHERE tg_id=?", (pts, referred_by))
            conn.commit()
        except:
            conn.close()
            return None
        conn.close()
        return (referred_by, pts)

    @classmethod
    def get_or_create(cls, tg_id, username, full_name, ref_code=None):
        u = cls.get_user(tg_id)
        if not u:
            rb = cls.create_user(tg_id, username, full_name, ref_code)
            return cls.get_user(tg_id), rb, True
        return u, None, False

    @classmethod
    def update_user(cls, tg_id, **kw):
        if not kw:
            return
        fields = ", ".join(f"{k}=?" for k in kw)
        conn = cls.get_conn()
        conn.execute(f"UPDATE users SET {fields} WHERE tg_id=?", list(kw.values()) + [tg_id])
        conn.commit()
        conn.close()

    @classmethod
    def add_points(cls, tg_id, pts):
        conn = cls.get_conn()
        conn.execute("UPDATE users SET points=points+? WHERE tg_id=?", (pts, tg_id))
        conn.commit()
        conn.close()

    @classmethod
    def deduct_points(cls, tg_id, pts):
        conn = cls.get_conn()
        u = conn.execute("SELECT points FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        if not u or u["points"] < pts:
            conn.close()
            return False
        conn.execute("UPDATE users SET points=points-? WHERE tg_id=?", (pts, tg_id))
        conn.commit()
        new_pts = u["points"] - pts
        conn.close()
        # إشعار انخفاض الرصيد
        try:
            threshold = int(db.get_config("low_points_alert", "50"))
            if threshold > 0 and new_pts <= threshold and u["points"] > threshold:
                threading.Thread(target=_send_low_points_alert,
                                 args=(tg_id, new_pts, threshold), daemon=True).start()
        except:
            pass
        return True

    @classmethod
    def claim_daily(cls, tg_id):
        today = date.today().isoformat()
        conn = cls.get_conn()
        u = conn.execute("SELECT last_daily_gift FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        if not u or u["last_daily_gift"] == today:
            conn.close()
            return False, 0
        pts = int(cls.get_config("daily_gift_points", "5"))
        conn.execute("UPDATE users SET points=points+?,last_daily_gift=? WHERE tg_id=?",
                     (pts, today, tg_id))
        conn.commit()
        conn.close()
        return True, pts

    @classmethod
    def claim_weekly(cls, tg_id):
        today = date.today()
        conn = cls.get_conn()
        u = conn.execute("SELECT last_weekly_gift FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        if not u:
            conn.close()
            return False, 0, 0
        last = u["last_weekly_gift"] or ""
        if last:
            try:
                d = date.fromisoformat(last)
                left = 7 - (today - d).days
                if left > 0:
                    conn.close()
                    return False, 0, left
            except:
                pass
        pts = int(cls.get_config("weekly_gift_points", "50"))
        conn.execute("UPDATE users SET points=points+?,last_weekly_gift=? WHERE tg_id=?",
                     (pts, today.isoformat(), tg_id))
        conn.commit()
        conn.close()
        return True, pts, 0

    @classmethod
    def can_spin(cls, tg_id):
        hrs = float(cls.get_config("wheel_cooldown_hrs", "6"))
        conn = cls.get_conn()
        u = conn.execute("SELECT last_wheel_spin FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        conn.close()
        if not u or not u["last_wheel_spin"]:
            return True, 0
        try:
            last = datetime.fromisoformat(u["last_wheel_spin"])
            diff = (datetime.now() - last).total_seconds() / 3600
            left = hrs - diff
            if left > 0:
                return False, round(left, 1)
        except:
            pass
        return True, 0

    @classmethod
    def mark_spin(cls, tg_id):
        conn = cls.get_conn()
        conn.execute("UPDATE users SET last_wheel_spin=? WHERE tg_id=?",
                     (datetime.now().isoformat(), tg_id))
        conn.commit()
        conn.close()

    @classmethod
    def get_all_users(cls):
        conn = cls.get_conn()
        u = conn.execute("SELECT * FROM users WHERE is_banned=0").fetchall()
        conn.close()
        return u

    @classmethod
    def get_users_count(cls):
        conn = cls.get_conn()
        n = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        conn.close()
        return n

    @classmethod
    def get_top_referrers(cls, limit=5):
        conn = cls.get_conn()
        rows = conn.execute("""
            SELECT u.tg_id, u.full_name, u.username,
                   COUNT(r.referred_id) as ref_count,
                   COALESCE(SUM(r.points_awarded),0) as total_pts
            FROM users u
            LEFT JOIN referral_log r ON r.referrer_id = u.tg_id
            GROUP BY u.tg_id
            HAVING ref_count > 0
            ORDER BY ref_count DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return rows

    @classmethod
    def get_referral_count(cls, tg_id):
        conn = cls.get_conn()
        n = conn.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (tg_id,)).fetchone()[0]
        conn.close()
        return n

    @classmethod
    def get_referral_log_count(cls):
        conn = cls.get_conn()
        n = conn.execute("SELECT COUNT(*) FROM referral_log").fetchone()[0]
        conn.close()
        return n

    # ─── الطلبات ──────────────────────────────────────────────────
    @classmethod
    def create_order(cls, user_id, svc_id, svc_name, link, qty, charge, pts=0, api_id=None, app_name="", site_id=None):
        conn = cls.get_conn()
        cur = conn.cursor()
        cur.execute("""INSERT INTO orders(user_id,service_id,service_name,app_name,link,
            quantity,charge,points_used,api_order_id,status,site_id,pending_approval) VALUES(?,?,?,?,?,?,?,?,?,?,?,1)""",
            (user_id, svc_id, svc_name, app_name, link, qty, charge, pts, api_id, "pending", site_id))
        oid = cur.lastrowid
        conn.commit()
        conn.close()
        return oid

    @classmethod
    def get_user_orders(cls, tg_id, limit=10):
        conn = cls.get_conn()
        rows = conn.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                            (tg_id, limit)).fetchall()
        conn.close()
        return rows

    @classmethod
    def get_user_orders_count(cls, tg_id):
        conn = cls.get_conn()
        n = conn.execute("SELECT COUNT(*) FROM orders WHERE user_id=?", (tg_id,)).fetchone()[0]
        conn.close()
        return n

    @classmethod
    def get_total_completed_orders(cls):
        """تعد كل الطلبات من أول ما اتبعتت (مش بس المكتملة)"""
        conn = cls.get_conn()
        n = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        conn.close()
        return n

    @classmethod
    def get_order(cls, oid):
        conn = cls.get_conn()
        o = conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
        conn.close()
        return o

    @classmethod
    def update_order(cls, oid, status, api_id=None):
        conn = cls.get_conn()
        if api_id:
            conn.execute("UPDATE orders SET status=?,api_order_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                         (status, api_id, oid))
        else:
            conn.execute("UPDATE orders SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                         (status, oid))
        conn.commit()
        conn.close()

    @classmethod
    def mark_notified(cls, oid):
        conn = cls.get_conn()
        conn.execute("UPDATE orders SET notified_done=1 WHERE id=?", (oid,))
        conn.commit()
        conn.close()

    @classmethod
    def approve_order(cls, oid):
        """موافقة على طلب SMM وتنفيذه"""
        conn = cls.get_conn()
        conn.execute("UPDATE orders SET pending_approval=0 WHERE id=?", (oid,))
        conn.commit()
        conn.close()

    @classmethod
    def reject_order(cls, oid):
        """رفض طلب SMM واسترداد النقاط"""
        conn = cls.get_conn()
        o = conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
        if o and o["pending_approval"] == 1:
            conn.execute("UPDATE users SET points=points+? WHERE tg_id=?",
                         (o["points_used"], o["user_id"]))
            conn.execute("UPDATE orders SET status='canceled', pending_approval=0 WHERE id=?", (oid,))
            conn.commit()
        conn.close()
        return o

    @classmethod
    def get_pending_orders(cls):
        """طلبات SMM تنتظر الموافقة"""
        conn = cls.get_conn()
        rows = conn.execute(
            "SELECT * FROM orders WHERE pending_approval=1 ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return rows

    # ─── المتجر ───────────────────────────────────────────────────
    @classmethod
    def get_store_products(cls, only_active=True):
        conn = cls.get_conn()
        q = "SELECT * FROM store_products"
        if only_active:
            q += " WHERE is_active=1"
        q += " ORDER BY id"
        r = conn.execute(q).fetchall()
        conn.close()
        return r

    @classmethod
    def get_store_product(cls, pid):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM store_products WHERE id=?", (pid,)).fetchone()
        conn.close()
        return r

    @classmethod
    def add_store_product(cls, name, desc, emoji, price, stock=-1):
        conn = cls.get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO store_products(name,description,emoji,price,stock) VALUES(?,?,?,?,?)",
                    (name, desc, emoji, price, stock))
        pid = cur.lastrowid
        conn.commit()
        conn.close()
        return pid

    @classmethod
    def delete_store_product(cls, pid):
        conn = cls.get_conn()
        conn.execute("DELETE FROM store_products WHERE id=?", (pid,))
        conn.commit()
        conn.close()

    @classmethod
    def toggle_store_product(cls, pid):
        conn = cls.get_conn()
        conn.execute("UPDATE store_products SET is_active=1-is_active WHERE id=?", (pid,))
        conn.commit()
        conn.close()

    @classmethod
    def create_store_order(cls, user_id, product_id, product_name, points):
        conn = cls.get_conn()
        cur = conn.cursor()
        cur.execute("""INSERT INTO store_orders(user_id,product_id,product_name,points_used)
                       VALUES(?,?,?,?)""", (user_id, product_id, product_name, points))
        oid = cur.lastrowid
        conn.commit()
        conn.close()
        return oid

    @classmethod
    def get_store_order(cls, oid):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM store_orders WHERE id=?", (oid,)).fetchone()
        conn.close()
        return r

    @classmethod
    def approve_store_order(cls, oid):
        conn = cls.get_conn()
        conn.execute("UPDATE store_orders SET pending_approval=0, status='approved' WHERE id=?", (oid,))
        conn.commit()
        conn.close()

    @classmethod
    def reject_store_order(cls, oid):
        conn = cls.get_conn()
        o = conn.execute("SELECT * FROM store_orders WHERE id=?", (oid,)).fetchone()
        if o and o["pending_approval"] == 1:
            conn.execute("UPDATE users SET points=points+? WHERE tg_id=?",
                         (o["points_used"], o["user_id"]))
            conn.execute("UPDATE store_orders SET status='rejected', pending_approval=0 WHERE id=?", (oid,))
            conn.commit()
        conn.close()
        return o

    @classmethod
    def get_pending_store_orders(cls):
        conn = cls.get_conn()
        rows = conn.execute(
            "SELECT * FROM store_orders WHERE pending_approval=1 ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return rows

    @classmethod
    def get_user_store_orders(cls, tg_id, limit=10):
        conn = cls.get_conn()
        rows = conn.execute("SELECT * FROM store_orders WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                            (tg_id, limit)).fetchall()
        conn.close()
        return rows

    # ─── طلبات الشحن ──────────────────────────────────────────
    @classmethod
    def create_recharge_request(cls, user_id, method, photo_id="", amount=0):
        conn = cls.get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO recharge_requests(user_id,method,photo_id,amount) VALUES(?,?,?,?)",
                    (user_id, method, photo_id, amount))
        rid = cur.lastrowid
        conn.commit()
        conn.close()
        return rid

    @classmethod
    def get_recharge_request(cls, rid):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM recharge_requests WHERE id=?", (rid,)).fetchone()
        conn.close()
        return r

    @classmethod
    def approve_recharge(cls, rid, points):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM recharge_requests WHERE id=?", (rid,)).fetchone()
        if r and r["status"] == "pending":
            conn.execute("UPDATE users SET points=points+? WHERE tg_id=?", (points, r["user_id"]))
            conn.execute("UPDATE recharge_requests SET status='approved', points=? WHERE id=?", (points, rid))
            conn.commit()
        conn.close()
        return r

    @classmethod
    def reject_recharge(cls, rid, note=""):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM recharge_requests WHERE id=?", (rid,)).fetchone()
        if r and r["status"] == "pending":
            conn.execute("UPDATE recharge_requests SET status='rejected', note=? WHERE id=?", (note, rid))
            conn.commit()
        conn.close()
        return r

    @classmethod
    def get_pending_recharges(cls):
        conn = cls.get_conn()
        rows = conn.execute(
            "SELECT * FROM recharge_requests WHERE status='pending' ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return rows

    # ─── كوبونات ──────────────────────────────────────────────
    @classmethod
    def get_coupon(cls, code):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM coupons WHERE code=? AND is_active=1", (code.upper(),)).fetchone()
        conn.close()
        return r

    @classmethod
    def get_coupon_by_id(cls, cid):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM coupons WHERE id=?", (cid,)).fetchone()
        conn.close()
        return r

    @classmethod
    def get_all_coupons(cls):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM coupons ORDER BY created_at DESC").fetchall()
        conn.close()
        return r

    @classmethod
    def add_coupon(cls, code, discount, max_uses=-1):
        conn = cls.get_conn()
        try:
            conn.execute("INSERT INTO coupons(code,discount,max_uses) VALUES(?,?,?)",
                         (code.upper(), discount, max_uses))
            conn.commit()
            result = True
        except:
            result = False
        conn.close()
        return result

    @classmethod
    def delete_coupon(cls, cid):
        conn = cls.get_conn()
        conn.execute("DELETE FROM coupons WHERE id=?", (cid,))
        conn.commit()
        conn.close()

    @classmethod
    def toggle_coupon(cls, cid):
        conn = cls.get_conn()
        conn.execute("UPDATE coupons SET is_active=1-is_active WHERE id=?", (cid,))
        conn.commit()
        conn.close()

    @classmethod
    def user_used_coupon(cls, user_id, coupon_id):
        conn = cls.get_conn()
        r = conn.execute("SELECT 1 FROM coupon_uses WHERE user_id=? AND coupon_id=?",
                         (user_id, coupon_id)).fetchone()
        conn.close()
        return r is not None

    @classmethod
    def mark_coupon_used(cls, user_id, coupon_id):
        conn = cls.get_conn()
        conn.execute("INSERT OR IGNORE INTO coupon_uses(user_id,coupon_id) VALUES(?,?)",
                     (user_id, coupon_id))
        conn.execute("UPDATE coupons SET used_count=used_count+1 WHERE id=?", (coupon_id,))
        conn.commit()
        conn.close()

    # ─── روابط الهدايا ────────────────────────────────────────
    @classmethod
    def create_gift_link(cls, points, max_uses=-1, note=""):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        conn = cls.get_conn()
        try:
            conn.execute(
                "INSERT INTO gift_links(code,points,max_uses,note) VALUES(?,?,?,?)",
                (code, points, max_uses, note))
            conn.commit()
        except:
            code = None
        conn.close()
        return code

    @classmethod
    def get_gift_link(cls, code):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM gift_links WHERE code=?", (code,)).fetchone()
        conn.close()
        return r

    @classmethod
    def get_all_gift_links(cls):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM gift_links ORDER BY created_at DESC").fetchall()
        conn.close()
        return r

    @classmethod
    def claim_gift_link(cls, user_id, code):
        """يحاول المستخدم يستلم الهدية — يرجع (ok, points, error_msg)"""
        conn = cls.get_conn()
        gl = conn.execute("SELECT * FROM gift_links WHERE code=?", (code,)).fetchone()
        if not gl:
            conn.close()
            return False, 0, "الرابط غير موجود"
        if not gl["is_active"]:
            conn.close()
            return False, 0, "هذا الرابط غير نشط"
        if gl["max_uses"] != -1 and gl["used_count"] >= gl["max_uses"]:
            conn.close()
            return False, 0, "انتهت استخدامات هذا الرابط"
        already = conn.execute(
            "SELECT 1 FROM gift_link_claims WHERE user_id=? AND code=?",
            (user_id, code)).fetchone()
        if already:
            conn.close()
            return False, 0, "استلمت هذه الهدية من قبل"
        pts = gl["points"]
        try:
            conn.execute("INSERT INTO gift_link_claims(user_id,code) VALUES(?,?)", (user_id, code))
            conn.execute("UPDATE gift_links SET used_count=used_count+1 WHERE code=?", (code,))
            conn.execute("UPDATE users SET points=points+? WHERE tg_id=?", (pts, user_id))
            conn.commit()
        except Exception as e:
            conn.close()
            return False, 0, "خطأ في قاعدة البيانات"
        conn.close()
        return True, pts, ""

    @classmethod
    def delete_gift_link(cls, gid):
        conn = cls.get_conn()
        conn.execute("DELETE FROM gift_links WHERE id=?", (gid,))
        conn.commit()
        conn.close()

    @classmethod
    def toggle_gift_link(cls, gid):
        conn = cls.get_conn()
        conn.execute("UPDATE gift_links SET is_active=1-is_active WHERE id=?", (gid,))
        conn.commit()
        conn.close()

    # ─── ليدربورد ─────────────────────────────────────────────
    @classmethod
    def get_leaderboard_points(cls, limit=10):
        conn = cls.get_conn()
        r = conn.execute(
            "SELECT tg_id, full_name, username, points FROM users ORDER BY points DESC LIMIT ?",
            (limit,)).fetchall()
        conn.close()
        return r

    @classmethod
    def get_leaderboard_orders(cls, limit=10):
        conn = cls.get_conn()
        r = conn.execute(
            "SELECT user_id, COUNT(*) as cnt, SUM(points_used) as total_pts FROM orders "
            "GROUP BY user_id ORDER BY cnt DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return r

    # ─── إحصائيات التقرير ─────────────────────────────────────
    @classmethod
    def get_daily_stats(cls):
        conn = cls.get_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        stats = {}
        stats["new_users"]    = conn.execute(
            "SELECT COUNT(*) FROM users WHERE created_at LIKE ?", (today+"%",)).fetchone()[0]
        stats["total_users"]  = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        stats["new_orders"]   = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE created_at LIKE ?", (today+"%",)).fetchone()[0]
        stats["total_orders"] = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        stats["points_spent"] = conn.execute(
            "SELECT COALESCE(SUM(points_used),0) FROM orders WHERE created_at LIKE ?",
            (today+"%",)).fetchone()[0]
        stats["store_orders"] = conn.execute(
            "SELECT COUNT(*) FROM store_orders WHERE created_at LIKE ?", (today+"%",)).fetchone()[0]
        stats["recharges"]    = conn.execute(
            "SELECT COUNT(*) FROM recharge_requests WHERE status='approved' AND created_at LIKE ?",
            (today+"%",)).fetchone()[0]
        conn.close()
        return stats

    @classmethod
    def get_orders_stats(cls):
        conn = cls.get_conn()
        total   = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        today   = conn.execute("SELECT COUNT(*) FROM orders WHERE DATE(created_at)=DATE('now')").fetchone()[0]
        revenue = conn.execute("SELECT COALESCE(SUM(charge),0) FROM orders").fetchone()[0]
        trev    = conn.execute("SELECT COALESCE(SUM(charge),0) FROM orders WHERE DATE(created_at)=DATE('now')").fetchone()[0]
        tpts    = conn.execute("SELECT COALESCE(SUM(points_used),0) FROM orders").fetchone()[0]
        conn.close()
        return total, today, revenue, trev, tpts

    # ─── الإعدادات ────────────────────────────────────────────────
    @classmethod
    def get_config(cls, key, default=""):
        conn = cls.get_conn()
        r = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
        conn.close()
        return r["value"] if r else default

    @classmethod
    def set_config(cls, key, value):
        conn = cls.get_conn()
        conn.execute("INSERT OR REPLACE INTO config(key,value) VALUES(?,?)", (key, value))
        conn.commit()
        conn.close()

    @classmethod
    def get_all_config(cls):
        conn = cls.get_conn()
        rows = conn.execute("SELECT key, value FROM config ORDER BY key").fetchall()
        conn.close()
        return rows

    # ─── القنوات الإجبارية ────────────────────────────────────────
    @classmethod
    def get_mandatory_channels(cls):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM mandatory_channels").fetchall()
        conn.close()
        return r

    @classmethod
    def add_mandatory_channel(cls, ch_id, name, url, target=0):
        conn = cls.get_conn()
        try:
            conn.execute("""INSERT INTO mandatory_channels(channel_id,channel_name,channel_url,target_members,current_members)
                VALUES(?,?,?,?,0)""", (ch_id, name, url, target))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    @classmethod
    def remove_mandatory_channel(cls, ch_id):
        conn = cls.get_conn()
        conn.execute("DELETE FROM mandatory_channels WHERE channel_id=?", (ch_id,))
        conn.commit()
        conn.close()

    @classmethod
    def record_join(cls, user_id, ch_id):
        conn = cls.get_conn()
        try:
            cur = conn.execute("INSERT OR IGNORE INTO mandatory_joins(user_id,channel_id) VALUES(?,?)",
                               (user_id, ch_id))
            if cur.rowcount > 0:
                conn.execute("UPDATE mandatory_channels SET current_members=current_members+1 WHERE channel_id=?", (ch_id,))
                conn.commit()
                r = conn.execute("SELECT target_members,current_members FROM mandatory_channels WHERE channel_id=?",
                                 (ch_id,)).fetchone()
                if r and r["target_members"] > 0 and r["current_members"] >= r["target_members"]:
                    conn.execute("DELETE FROM mandatory_channels WHERE channel_id=?", (ch_id,))
                    conn.commit()
        except:
            pass
        conn.close()

    # ─── قنوات النقاط ─────────────────────────────────────────────
    @classmethod
    def get_points_channels(cls):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM points_channels").fetchall()
        conn.close()
        return r

    @classmethod
    def add_points_channel(cls, ch_id, name, url, pts):
        conn = cls.get_conn()
        try:
            conn.execute("INSERT INTO points_channels(channel_id,channel_name,channel_url,points_reward) VALUES(?,?,?,?)",
                         (ch_id, name, url, pts))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    @classmethod
    def remove_points_channel(cls, ch_id):
        conn = cls.get_conn()
        conn.execute("DELETE FROM points_channels WHERE channel_id=?", (ch_id,))
        conn.commit()
        conn.close()

    @classmethod
    def has_channel_pts(cls, uid, ch_id):
        conn = cls.get_conn()
        r = conn.execute("SELECT 1 FROM user_channel_points WHERE user_id=? AND channel_id=?",
                         (uid, ch_id)).fetchone()
        conn.close()
        return r is not None

    @classmethod
    def mark_channel_pts(cls, uid, ch_id):
        conn = cls.get_conn()
        conn.execute("INSERT OR IGNORE INTO user_channel_points(user_id,channel_id) VALUES(?,?)", (uid, ch_id))
        conn.commit()
        conn.close()

    # ─── قنوات الطلبات ────────────────────────────────────────────
    @classmethod
    def get_order_channels(cls):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM order_channels WHERE is_active=1").fetchall()
        conn.close()
        return r

    @classmethod
    def add_order_channel(cls, ch_id, name):
        conn = cls.get_conn()
        try:
            conn.execute("INSERT INTO order_channels(channel_id,channel_name) VALUES(?,?)", (ch_id, name))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    @classmethod
    def remove_order_channel(cls, ch_id):
        conn = cls.get_conn()
        conn.execute("DELETE FROM order_channels WHERE channel_id=?", (ch_id,))
        conn.commit()
        conn.close()

    # ─── أكواد الدعوة ─────────────────────────────────────────────
    @classmethod
    def create_invite(cls, code, pts, max_uses=0):
        conn = cls.get_conn()
        try:
            conn.execute("INSERT INTO invite_links(code,points_reward,max_uses) VALUES(?,?,?)",
                         (code, pts, max_uses))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    @classmethod
    def get_invites(cls):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM invite_links ORDER BY created_at DESC").fetchall()
        conn.close()
        return r

    @classmethod
    def delete_invite(cls, code):
        conn = cls.get_conn()
        conn.execute("DELETE FROM invite_links WHERE code=?", (code,))
        conn.commit()
        conn.close()

    @classmethod
    def claim_invite(cls, uid, code):
        conn = cls.get_conn()
        lnk = conn.execute("SELECT * FROM invite_links WHERE code=?", (code,)).fetchone()
        if not lnk:
            conn.close()
            return False, 0, "الكود غير موجود"
        if not lnk["is_active"]:
            conn.close()
            return False, 0, "الكود غير نشط"
        if lnk["max_uses"] > 0 and lnk["current_uses"] >= lnk["max_uses"]:
            conn.close()
            return False, 0, "الكود وصل للحد الأقصى"
        claimed = conn.execute("SELECT 1 FROM user_invite_claims WHERE user_id=? AND invite_code=?",
                               (uid, code)).fetchone()
        if claimed:
            conn.close()
            return False, 0, "استخدمت هذا الكود من قبل"
        pts = lnk["points_reward"]
        try:
            conn.execute("INSERT INTO user_invite_claims(user_id,invite_code) VALUES(?,?)", (uid, code))
            conn.execute("UPDATE invite_links SET current_uses=current_uses+1 WHERE code=?", (code,))
            conn.execute("UPDATE users SET points=points+? WHERE tg_id=?", (pts, uid))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return False, 0, "استخدمت هذا الكود من قبل"
        conn.close()
        return True, pts, ""

    # ─── الأقسام ──────────────────────────────────────────────────
    @classmethod
    def get_apps(cls, only_active=True):
        conn = cls.get_conn()
        q = "SELECT * FROM apps" + (" WHERE is_active=1" if only_active else "") + " ORDER BY sort_order,id"
        r = conn.execute(q).fetchall()
        conn.close()
        return r

    @classmethod
    def get_app(cls, app_id):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM apps WHERE id=?", (app_id,)).fetchone()
        conn.close()
        return r

    @classmethod
    def add_app(cls, name, emoji=""):
        conn = cls.get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO apps(name,emoji) VALUES(?,?)", (name, emoji))
        aid = cur.lastrowid
        conn.commit()
        conn.close()
        return aid

    @classmethod
    def update_app(cls, app_id, name=None, emoji=None):
        fields = []
        params = []
        if name is not None:
            fields.append("name=?")
            params.append(name)
        if emoji is not None:
            fields.append("emoji=?")
            params.append(emoji)
        if not fields:
            return
        params.append(app_id)
        conn = cls.get_conn()
        conn.execute(f"UPDATE apps SET {', '.join(fields)} WHERE id=?", params)
        conn.commit()
        conn.close()

    @classmethod
    def delete_app(cls, app_id):
        conn = cls.get_conn()
        conn.execute("DELETE FROM app_services WHERE app_id=?", (app_id,))
        conn.execute("DELETE FROM apps WHERE id=?", (app_id,))
        conn.commit()
        conn.close()

    # ─── خدمات الأقسام ────────────────────────────────────────────
    @classmethod
    def get_app_services(cls, app_id, only_active=True):
        conn = cls.get_conn()
        q = "SELECT * FROM app_services WHERE app_id=?" + (" AND is_active=1" if only_active else "") + " ORDER BY id"
        r = conn.execute(q, (app_id,)).fetchall()
        conn.close()
        return r

    @classmethod
    def get_service(cls, sid):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM app_services WHERE id=?", (sid,)).fetchone()
        conn.close()
        return r

    @classmethod
    def add_service(cls, app_id, name, emoji, api_id, pts_per_1000, mn, mx, rate, site_id=None):
        conn = cls.get_conn()
        conn.execute("""INSERT INTO app_services(app_id,name,emoji,api_service_id,points_per_1000,min_qty,max_qty,rate_per_1000,site_id)
            VALUES(?,?,?,?,?,?,?,?,?)""", (app_id, name, emoji, api_id, pts_per_1000, mn, mx, rate, site_id))
        conn.commit()
        conn.close()

    @classmethod
    def update_service(cls, sid, name=None, emoji=None, api_service_id=None, site_id=-1):
        fields = []
        params = []
        if name is not None:
            fields.append("name=?")
            params.append(name)
        if emoji is not None:
            fields.append("emoji=?")
            params.append(emoji)
        if api_service_id is not None:
            fields.append("api_service_id=?")
            params.append(api_service_id)
        if site_id != -1:
            fields.append("site_id=?")
            params.append(site_id)
        if not fields:
            return
        params.append(sid)
        conn = cls.get_conn()
        conn.execute(f"UPDATE app_services SET {', '.join(fields)} WHERE id=?", params)
        conn.commit()
        conn.close()

    @classmethod
    def update_free_service(cls, sid, api_service_id=None, site_id=-1):
        fields = []
        params = []
        if api_service_id is not None:
            fields.append("api_service_id=?")
            params.append(api_service_id)
        if site_id != -1:
            fields.append("site_id=?")
            params.append(site_id)
        if not fields:
            return
        params.append(sid)
        conn = cls.get_conn()
        conn.execute(f"UPDATE free_services SET {', '.join(fields)} WHERE id=?", params)
        conn.commit()
        conn.close()

    @classmethod
    def delete_service(cls, sid):
        conn = cls.get_conn()
        conn.execute("DELETE FROM app_services WHERE id=?", (sid,))
        conn.commit()
        conn.close()

    # ─── مواقع SMM ────────────────────────────────────────────────
    @classmethod
    def get_smm_sites(cls, only_active=False):
        conn = cls.get_conn()
        q = "SELECT * FROM smm_sites" + (" WHERE is_active=1" if only_active else "") + " ORDER BY id"
        r = conn.execute(q).fetchall()
        conn.close()
        return r

    @classmethod
    def get_smm_site(cls, site_id):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM smm_sites WHERE id=?", (site_id,)).fetchone()
        conn.close()
        return r

    @classmethod
    def add_smm_site(cls, name, api_url, api_key):
        conn = cls.get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO smm_sites(name,api_url,api_key) VALUES(?,?,?)", (name, api_url, api_key))
        sid = cur.lastrowid
        conn.commit()
        conn.close()
        return sid

    @classmethod
    def delete_smm_site(cls, site_id):
        conn = cls.get_conn()
        conn.execute("DELETE FROM smm_sites WHERE id=?", (site_id,))
        conn.commit()
        conn.close()

    @classmethod
    def toggle_smm_site(cls, site_id):
        conn = cls.get_conn()
        conn.execute("UPDATE smm_sites SET is_active=1-is_active WHERE id=?", (site_id,))
        conn.commit()
        conn.close()

    # ─── عجلة الحظ ────────────────────────────────────────────────
    @classmethod
    def get_wheel_prizes(cls, only_active=True):
        conn = cls.get_conn()
        q = "SELECT * FROM wheel_prizes" + (" WHERE is_active=1" if only_active else "") + " ORDER BY points ASC"
        r = conn.execute(q).fetchall()
        conn.close()
        return r

    @classmethod
    def add_wheel_prize(cls, pts, weight, emoji="", label=""):
        conn = cls.get_conn()
        conn.execute("INSERT INTO wheel_prizes(points,weight,emoji,label) VALUES(?,?,?,?)",
                     (pts, weight, emoji, label))
        conn.commit()
        conn.close()

    @classmethod
    def delete_wheel_prize(cls, pid):
        conn = cls.get_conn()
        conn.execute("DELETE FROM wheel_prizes WHERE id=?", (pid,))
        conn.commit()
        conn.close()

    @classmethod
    def toggle_wheel_prize(cls, pid):
        conn = cls.get_conn()
        conn.execute("UPDATE wheel_prizes SET is_active=1-is_active WHERE id=?", (pid,))
        conn.commit()
        conn.close()

    # ─── الخدمات المجانية ─────────────────────────────────────────
    @classmethod
    def get_free_services(cls, only_active=True):
        conn = cls.get_conn()
        q = "SELECT * FROM free_services" + (" WHERE is_active=1" if only_active else "") + " ORDER BY id"
        r = conn.execute(q).fetchall()
        conn.close()
        return r

    @classmethod
    def get_free_service(cls, sid):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM free_services WHERE id=?", (sid,)).fetchone()
        conn.close()
        return r

    @classmethod
    def add_free_service(cls, name, desc, api_id, daily_limit, mn, mx, site_id=None):
        conn = cls.get_conn()
        conn.execute("""INSERT INTO free_services(name,description,api_service_id,daily_limit,min_qty,max_qty,site_id)
            VALUES(?,?,?,?,?,?,?)""", (name, desc, api_id, daily_limit, mn, mx, site_id))
        conn.commit()
        conn.close()

    @classmethod
    def delete_free_service(cls, sid):
        conn = cls.get_conn()
        conn.execute("DELETE FROM free_services WHERE id=?", (sid,))
        conn.commit()
        conn.close()

    @classmethod
    def get_free_claim_count_today(cls, uid, sid):
        today = date.today().isoformat()
        conn = cls.get_conn()
        n = conn.execute("SELECT COUNT(*) FROM user_free_claims WHERE user_id=? AND service_id=? AND claim_date=?",
                         (uid, sid, today)).fetchone()[0]
        conn.close()
        return n

    @classmethod
    def get_free_claim_count_today_total(cls, uid):
        today = date.today().isoformat()
        conn = cls.get_conn()
        n = conn.execute("SELECT COUNT(*) FROM user_free_claims WHERE user_id=? AND claim_date=?",
                         (uid, today)).fetchone()[0]
        conn.close()
        return n

    @classmethod
    def add_free_claim(cls, uid, sid, qty, link, api_id="", status="pending"):
        today = date.today().isoformat()
        conn = cls.get_conn()
        conn.execute("""INSERT INTO user_free_claims(user_id,service_id,claim_date,quantity,link,api_order_id,status)
            VALUES(?,?,?,?,?,?,?)""", (uid, sid, today, qty, link, api_id, status))
        conn.commit()
        conn.close()

    # ─── الأدمنية ─────────────────────────────────────────────────
    @classmethod
    def get_extra_admins(cls):
        conn = cls.get_conn()
        r = conn.execute("SELECT * FROM extra_admins").fetchall()
        conn.close()
        return r

    @classmethod
    def add_extra_admin(cls, tg_id, full_name=""):
        conn = cls.get_conn()
        try:
            conn.execute("INSERT INTO extra_admins(tg_id,full_name) VALUES(?,?)", (tg_id, full_name))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False

    @classmethod
    def remove_extra_admin(cls, tg_id):
        conn = cls.get_conn()
        conn.execute("DELETE FROM extra_admins WHERE tg_id=?", (tg_id,))
        conn.commit()
        conn.close()

    # ─── تصدير/استيراد قاعدة البيانات ────────────────────────────
    @classmethod
    def export_db_json(cls):
        """تصدير إعدادات قاعدة البيانات كـ JSON"""
        conn = cls.get_conn()
        data = {}

        tables = ["config", "smm_sites", "apps", "app_services",
                  "free_services", "wheel_prizes", "mandatory_channels",
                  "points_channels", "order_channels", "invite_links"]

        for table in tables:
            try:
                rows = conn.execute(f"SELECT * FROM {table}").fetchall()
                data[table] = [dict(r) for r in rows]
            except:
                data[table] = []

        conn.close()
        return json.dumps(data, ensure_ascii=False, indent=2)

    @classmethod
    def import_db_json(cls, json_str):
        """استيراد إعدادات قاعدة البيانات من JSON"""
        try:
            data = json.loads(json_str)
            conn = cls.get_conn()
            c = conn.cursor()

            # استيراد الإعدادات
            if "config" in data:
                for row in data["config"]:
                    c.execute("INSERT OR REPLACE INTO config(key,value) VALUES(?,?)",
                              (row["key"], row["value"]))

            # استيراد مواقع SMM
            if "smm_sites" in data:
                c.execute("DELETE FROM smm_sites")
                for row in data["smm_sites"]:
                    c.execute("""INSERT OR IGNORE INTO smm_sites(name,api_url,api_key,is_active,is_default)
                        VALUES(?,?,?,?,?)""",
                        (row.get("name",""), row.get("api_url",""), row.get("api_key",""),
                         1,  # ← دايماً نشط بعد الاستعادة
                         row.get("is_default",0)))
                # لو مفيش أي موقع اترفع، حط الموقع الافتراضي تلقائياً
                count = c.execute("SELECT COUNT(*) FROM smm_sites").fetchone()[0]
                if count == 0:
                    c.execute("""INSERT INTO smm_sites(name,api_url,api_key,is_active,is_default)
                        VALUES(?,?,?,1,1)""",
                        ("SMMParty","https://smmparty.com/api/v2","d7ab98d24cdd1c95804bc75b26edc456"))

            # استيراد الأقسام
            if "apps" in data:
                for row in data["apps"]:
                    c.execute("INSERT OR IGNORE INTO apps(id,name,emoji,is_active,sort_order) VALUES(?,?,?,?,?)",
                              (row.get("id"), row.get("name",""), row.get("emoji","📱"),
                               row.get("is_active",1), row.get("sort_order",0)))

            # استيراد الخدمات
            if "app_services" in data:
                for row in data["app_services"]:
                    c.execute("""INSERT OR IGNORE INTO app_services
                        (id,app_id,name,emoji,api_service_id,site_id,points_per_1000,min_qty,max_qty,rate_per_1000,is_active)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                        (row.get("id"), row.get("app_id"), row.get("name",""),
                         row.get("emoji",""), row.get("api_service_id",""),
                         row.get("site_id"), row.get("points_per_1000",10),
                         row.get("min_qty",100), row.get("max_qty",100000),
                         row.get("rate_per_1000",0.5), row.get("is_active",1)))

            # استيراد جوائز العجلة
            if "wheel_prizes" in data:
                c.execute("DELETE FROM wheel_prizes")
                for row in data["wheel_prizes"]:
                    c.execute("INSERT INTO wheel_prizes(points,weight,emoji,label,is_active) VALUES(?,?,?,?,?)",
                              (row.get("points",10), row.get("weight",10),
                               row.get("emoji",""), row.get("label",""), row.get("is_active",1)))

            # استيراد الخدمات المجانية
            if "free_services" in data:
                for row in data["free_services"]:
                    c.execute("""INSERT OR IGNORE INTO free_services
                        (name,description,api_service_id,site_id,daily_limit,min_qty,max_qty,is_active)
                        VALUES(?,?,?,?,?,?,?,?)""",
                        (row.get("name",""), row.get("description",""),
                         row.get("api_service_id",""), row.get("site_id"),
                         row.get("daily_limit",1), row.get("min_qty",100),
                         row.get("max_qty",1000), row.get("is_active",1)))

            # استيراد القنوات الإجبارية
            if "mandatory_channels" in data:
                for row in data["mandatory_channels"]:
                    c.execute("""INSERT OR IGNORE INTO mandatory_channels
                        (channel_id,channel_name,channel_url,target_members) VALUES(?,?,?,?)""",
                        (row.get("channel_id",""), row.get("channel_name",""),
                         row.get("channel_url",""), row.get("target_members",0)))

            conn.commit()
            conn.close()
            return True, "تم الاستيراد بنجاح!"
        except Exception as e:
            return False, f"خطأ في الاستيراد: {e}"


# ══════════════════════════════════════════════════════════════════
#   4. عجلة الحظ — الرسم
# ══════════════════════════════════════════════════════════════════
def build_wheel_display(prizes, highlight_idx=None):
    if not prizes:
        return "لا توجد جوائز"
    lines = ["╔═══════════════════════╗"]
    for i, p in enumerate(prizes):
        em = p.get("emoji") or ""
        lbl = p.get("label") or f"{p['points']} نقطة"
        pts_str = f"{p['points']:,}"
        if highlight_idx is not None and i == highlight_idx:
            lines.append(f"║ ► {em} {pts_str:>6} — {lbl:<10} ◄ ║")
        else:
            lines.append(f"║   {em} {pts_str:>6} — {lbl:<10}   ║")
    lines.append("╚═══════════════════════╝")
    return "\n".join(lines)


def spin_animation_frames(prizes, winner_idx):
    frames = []
    n = len(prizes)
    for step in range(4):
        idx = (winner_idx + step + 1) % n
        frames.append(("🎡 العجلة تدور...", build_wheel_display(prizes, idx)))
    frames.append(("🎯 توقفت العجلة!", build_wheel_display(prizes, winner_idx)))
    return frames


# ══════════════════════════════════════════════════════════════════
#   5. الأزرار
# ══════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════
#   دعم ألوان الأزرار الرسمية — Bot API 9.4
#   "success"=أخضر | "danger"=أحمر | "primary"=أزرق
# ══════════════════════════════════════════════════════════════════
class ColoredButton(InlineKeyboardButton):
    """زر ملوّن حقيقي — يستخدم حقل style الرسمي من Bot API 9.4"""
    def __init__(self, text, callback_data=None, url=None, style=None, **kwargs):
        super().__init__(text=text, callback_data=callback_data, url=url, **kwargs)
        self._btn_style = style

    def to_dict(self):
        d = super().to_dict()
        if self._btn_style:
            d["style"] = self._btn_style
        return d

    def to_json(self):
        import json
        return json.dumps(self.to_dict())


_STYLE_MAP = {
    "green": "success",   # أخضر
    "red":   "danger",    # أحمر
    "blue":  "primary",   # أزرق
}


def _btn(text, cb=None, url=None, color="blue"):
    """كل زر لازم له لون — green/red/blue"""
    style = _STYLE_MAP.get(color, "primary")
    return ColoredButton(text=text, callback_data=cb, url=url, style=style)


def mk(*rows):
    m = InlineKeyboardMarkup()
    for row in rows:
        m.row(*row)
    return m


class kb:
    # ─── القائمة الرئيسية ──────────────────────────────────────
    @classmethod
    def main_menu(cls, updates_ch=None, orders_count=0):
        services_label = db.get_config("menu_services_label", "🎯 الخدمات")
        fund_label = db.get_config("menu_fund_label", "💳 شحن نقاط")
        collect_label = db.get_config("menu_collect_points_label", "🎁 تجميع نقاط")
        account_label = db.get_config("menu_account_label", "📊 الحساب")
        use_code_label = db.get_config("menu_use_code_label", "🔑 استخدام كود")
        transfer_label = db.get_config("menu_transfer_label", "🌐 تحويل نقاط")
        track_order_label = db.get_config("menu_track_order_label", "🔎 متابعه طلب")
        my_orders_label = db.get_config("menu_my_orders_label", "📦 طلباتي")
        updates_label = db.get_config("menu_updates_label", "🔄 اكتمال الطلبات ↗")
        store_label = db.get_config("menu_store_label", "🛍️ ⭐ نجوم 🚀 جوائز 🛍 رصيد أرقام")
        terms_label = db.get_config("menu_terms_label", "📜 شروط الاستخدام")

        rows = [
            # ── صف 1: الخدمات (عرض كامل) ──
            [_btn(services_label, "my_services", color="green")],

            # ── صف 2: شحن مباشر ──

            # ── صف 3 ──
            [_btn(collect_label, "collect_section", color="blue"),
             _btn(account_label, "my_account", color="blue")],

            # ── صف 4 ──
            [_btn(use_code_label, "enter_invite_code", color="blue"),
             _btn(transfer_label, "my_balance", color="blue")],

            # ── صف 5 ──
            [_btn(track_order_label, "track_order", color="blue"),
             _btn(my_orders_label, "my_orders", color="blue")],

            # ── صف 7: قنوات (أزرق) ──
            [
    _btn(fund_label, "fund_start", color="blue"),
    _btn("🔄 اكتمال الطلبات", url="https://t.me/R_TREND1", color="blue"),
],

            # ── صف 8 ──
            [_btn(terms_label, "terms", color="red")],

            # ── صف 9 ──
            [_btn(store_label, "store", color="blue")],

            # ── صف 10: عداد الطلبات (أخضر) ──
            [_btn(f"طلبات انجزناها {orders_count:,} طلب ✅", "my_orders", color="green")],
        ]
        return mk(*rows)

    # ─── تجميع النقاط ─────────────────────────────────────────
    @classmethod
    def collect_menu(cls):
        return mk(
            [_btn("🎡 عجلة الحظ", "wheel_open", color="green")],
            [_btn("🌅 الهدية اليومية", "daily_gift", color="green"),
             _btn("🗓️ الهدية الأسبوعية", "weekly_gift", color="green")],
            [_btn("📢 الاشتراك بالقنوات", "points_channels", color="blue")],
            [_btn("🔗 رابط الدعوة الخاص بي", "my_referral_link", color="green")],
            [_btn("🎟️ كود دعوة", "enter_invite_code", color="blue")],
            [_btn("🏆 أفضل 5 بالدعوات", "top_referrers", color="blue")],
            [_btn("◀️ رجوع للقائمة", "back_main", color="red")],
        )

    # ─── الخدمات المجانية ─────────────────────────────────────
    @classmethod
    def free_services_menu(cls, services, back_cb="back_main"):
        rows = []
        for s in services:
            rows.append([_btn(
                f"🎁 {s['name']} | {s['min_qty']:,}-{s['max_qty']:,}",
                f"free_svc_{s['id']}", color="green")])
        rows.append([_btn("◀️ رجوع", back_cb, color="red")])
        return mk(*rows)

    # ─── ⭐ نجوم 🚀 جوائز 🛍 رصيد أرقام ──────────────────────────────────────────
    @classmethod
    def store_products_keyboard(cls, products):
        rows = []
        for p in products:
            nm = f"{p['emoji']} {p['name']}" if p.get("emoji") else p['name']
            stock_txt = "" if p["stock"] == -1 else f" | {p['stock']:,} متبقي"
            rows.append([_btn(f"{nm}  —  {p['price']:,} نقطة{stock_txt}",
                              f"store_product_{p['id']}", color="blue")])
        rows.append([_btn("📦 طلباتي في المتجر", "my_store_orders", color="green")])
        rows.append([_btn("◀️ رجوع للقائمة", "back_main", color="red")])
        return mk(*rows)

    @classmethod
    def admin_store_keyboard(cls, products):
        rows = []
        for p in products:
            nm = f"{p['emoji']} {p['name']}" if p.get("emoji") else p['name']
            st = "✅" if p["is_active"] else "❌"
            rows.append([_btn(f"{st} {nm}  —  {p['price']:,} نقطة",
                              f"adm_store_product_{p['id']}", color="blue" if p["is_active"] else "red")])
        rows.append([_btn("➕ إضافة منتج", "adm_add_store_product", color="green")])
        rows.append([_btn("📋 طلبات معلقة", "adm_pending_orders", color="green"),
                     _btn("💵 شحن معلق", "adm_pending_recharges", color="green")])
        rows.append([_btn("◀️ رجوع", "adm_back", color="red")])
        return mk(*rows)

    # ─── أقسام الخدمات ────────────────────────────────────────
    @classmethod
    def apps_keyboard(cls, apps, include_free=False):
        rows = []
        if include_free:
            rows.append([_btn("🎁 الخدمات المجانية", "my_services_free", color="green")])
        pair = []
        for a in apps:
            txt = f"{a['emoji']} {a['name']}" if a.get('emoji') else a['name']
            pair.append(_btn(txt, f"app_{a['id']}", color="blue"))
            if len(pair) == 2:
                rows.append(pair)
                pair = []
        if pair:
            rows.append(pair)
        rows.append([_btn("◀️ رجوع للقائمة", "back_main", color="red")])
        return mk(*rows)

    @classmethod
    def app_services_keyboard(cls, app_id, services):
        rows = []
        for s in services:
            p = s["points_per_1000"]
            nm = f"{s['emoji']} {s['name']}" if s.get("emoji") else s['name']
            rows.append([_btn(f"{nm}  |  {p:,} نقطة / 1000", f"svc_{s['id']}", color="blue")])
        rows.append([_btn("◀️ رجوع للأقسام", "my_services", color="red")])
        return mk(*rows)

    # ─── تأكيد ────────────────────────────────────────────────
    @classmethod
    def confirm_keyboard(cls):
        return mk(
            [_btn("✅ تأكيد وإرسال الطلب", "order_confirm", color="green"),
             _btn("❌ إلغاء", "back_main", color="red")],
        )

    @classmethod
    def order_detail_keyboard(cls, oid):
        return mk(
            [_btn("🔄 تحديث الحالة", f"order_refresh_{oid}", color="blue")],
            [_btn("◀️ رجوع للطلبات", "my_orders", color="red")],
        )

    @classmethod
    def orders_list_keyboard(cls, orders):
        icons = {"pending": "⏳", "inprogress": "🔄", "completed": "✅",
                 "partial": "⚠️", "canceled": "❌"}
        rows = []
        for o in orders:
            ic = icons.get(o["status"].lower(), "•")
            rows.append([_btn(f"📦 طلب #{o['id']}  {ic}", f"order_detail_{o['id']}", color="blue")])
        rows.append([_btn("◀️ رجوع", "back_main", color="red")])
        return mk(*rows)

    # ─── الاشتراك الإجباري ────────────────────────────────────
    @classmethod
    def subscribe_keyboard(cls, channels, uid):
        rows = []
        for ch in channels:
            rows.append([_btn(f"📢 اشترك في  {ch['channel_name']}", url=ch["channel_url"], color="blue")])
        rows.append([_btn("✅ تحققت من الاشتراك", f"check_sub_{uid}", color="green")])
        return mk(*rows)

    @classmethod
    def points_ch_keyboard(cls, channels):
        rows = []
        for ch in channels:
            rows.append([_btn(f"⭐ {ch['channel_name']}  +{ch['points_reward']} نقطة",
                              url=ch["channel_url"], color="blue")])
        rows.append([_btn("🎯 جمّعت نقاطي", "collect_pts_now", color="green"),
                     _btn("◀️ رجوع", "collect_section", color="red")])
        return mk(*rows)

    # ─── عجلة الحظ ────────────────────────────────────────────
    @classmethod
    def wheel_keyboard(cls, can_spin):
        if can_spin:
            return mk(
                [_btn("🎡 اضغط لتلف العجلة", "wheel_spin", color="green")],
                [_btn("◀️ رجوع", "collect_section", color="red")],
            )
        return mk([_btn("◀️ رجوع", "collect_section", color="red")])

    # ─── لوحة الأدمن ──────────────────────────────────────────
    @classmethod
    def admin_main(cls):
        return mk(
            [_btn("🗂️ إدارة الأقسام والخدمات", "adm_apps", color="blue")],
            [_btn("📢 قنوات إجبارية", "adm_mandatory", color="blue"),
             _btn("💎 قنوات النقاط", "adm_points_ch", color="blue")],
            [_btn("📣 قنوات الطلبات", "adm_order_channels", color="blue"),
             _btn("🌐 مواقع SMM", "adm_smm_sites", color="blue")],
            [_btn("📊 الإحصائيات", "adm_stats", color="blue"),
             _btn("👥 إدارة المستخدمين", "adm_users", color="blue")],
            [_btn("📣 إذاعة جماعية", "adm_broadcast", color="green"),
             _btn("🔋 شحن نقاط", "adm_topup", color="green")],
            [_btn("🎡 عجلة الحظ", "adm_wheel", color="green"),
             _btn("🎁 الخدمات المجانية", "adm_free_svcs", color="green")],
            [_btn("🎟️ أكواد الدعوة", "adm_invite_links", color="green"),
             _btn("⭐ إعدادات النقاط", "adm_pts_settings", color="blue")],
            [_btn("⚙️ إعدادات الخدمة", "adm_service_cfg", color="blue"),
             _btn("📡 قناة التحديثات / الدعم", "adm_bot_settings", color="blue")],
            [_btn("🗄️ قاعدة البيانات", "adm_database", color="red"),
             _btn("🛡️ إدارة الأدمنية", "adm_admins", color="red")],
            [_btn("🛍️ إدارة المتجر", "adm_store", color="blue"),
             _btn("📋 طلبات معلقة", "adm_pending_orders", color="green")],
            [_btn("🎁 روابط الهدايا", "adm_gift_links", color="blue"),
             _btn("🔔 التنبيهات والتقارير", "adm_alerts_settings", color="blue")],
            [_btn("🔒 إغلاق اللوحة", "adm_close", color="red")],
        )

    @classmethod
    def admin_apps_keyboard(cls, apps):
        rows = []
        for a in apps:
            nm = f"{a['emoji']} {a['name']}" if a.get("emoji") else a['name']
            rows.append([_btn(nm, f"adm_app_{a['id']}", color="blue")])
        rows.append([_btn("➕ إضافة قسم جديد", "adm_add_app", color="green")])
        rows.append([_btn("◀️ رجوع", "adm_back", color="red")])
        return mk(*rows)

    @classmethod
    def admin_app_view(cls, app_id, services):
        rows = []
        for s in services:
            nm = f"{s['emoji']} {s['name']}" if s.get("emoji") else s['name']
            rows.append([_btn(f"{nm}  |  {s['points_per_1000']:,}/1000",
                              f"adm_svc_{s['id']}", color="blue")])
        rows.append([_btn("✏️ تعديل اسم القسم", f"adm_edit_app_{app_id}", color="blue")])
        rows.append([_btn("➕ إضافة خدمة", f"adm_add_svc_{app_id}", color="green")])
        rows.append([_btn("🗑️ حذف القسم", f"adm_del_app_{app_id}", color="red"),
                     _btn("◀️ رجوع", "adm_apps", color="red")])
        return mk(*rows)

    @classmethod
    def admin_svc_view(cls, sid, app_id):
        return mk(
            [_btn("✏️ تعديل اسم الخدمة", f"adm_edit_svc_{sid}", color="blue")],
            [_btn("🗑️ حذف الخدمة",       f"adm_del_svc_{sid}", color="red")],
            [_btn("◀️ رجوع للقسم",        f"adm_app_{app_id}", color="red")],
        )

    @classmethod
    def admin_free_svcs(cls, services):
        rows = []
        for s in services:
            rows.append([_btn(f"🎁 {s['name']}  |  حد {s['daily_limit']} يومياً",
                              f"adm_free_svc_{s['id']}", color="blue")])
        rows.append([_btn("➕ إضافة خدمة مجانية", "adm_add_free_svc", color="green")])
        rows.append([_btn("◀️ رجوع", "adm_back", color="red")])
        return mk(*rows)

    @classmethod
    def admin_free_svc_view(cls, sid):
        return mk(
            [_btn("🗑️ حذف الخدمة المجانية", f"adm_del_free_{sid}", color="red")],
            [_btn("◀️ رجوع",                 "adm_free_svcs",       color="red")],
        )

    @classmethod
    def admin_wheel(cls, prizes):
        rows = []
        total_w = sum(float(p["weight"]) for p in prizes if p["is_active"])
        for p in prizes:
            st = "✅" if p["is_active"] else "❌"
            chance = (float(p["weight"]) / total_w * 100) if (p["is_active"] and total_w) else 0
            lbl = p.get("label") or ""
            em = p.get("emoji") or ""
            dot_color = "green" if p["is_active"] else "red"
            rows.append([
                _btn(f"{st} {em} {p['points']} نقطة {lbl}  {chance:.0f}%",
                     f"adm_wheel_tog_{p['id']}", color=dot_color),
                _btn("🗑️", f"adm_wheel_del_{p['id']}", color="red"),
            ])
        rows.append([_btn("➕ إضافة جائزة", "adm_wheel_add", color="green")])
        rows.append([_btn("◀️ رجوع", "adm_back", color="red")])
        return mk(*rows)

    @classmethod
    def admin_invite_links(cls, links):
        rows = []
        for lnk in links[:10]:
            rows.append([
                _btn(f"🎁 {lnk['code']}  +{lnk['points_reward']}نقطة  ({lnk['current_uses']}/{lnk['max_uses'] or '∞'})",
                     f"adm_view_invite_{lnk['code']}", color="blue"),
            ])
        rows.append([_btn("➕ إنشاء كود جديد", "adm_create_invite", color="green")])
        rows.append([_btn("◀️ رجوع", "adm_back", color="red")])
        return mk(*rows)

    @classmethod
    def admin_users_kb(cls):
        return mk(
            [_btn("🔍 بحث عن مستخدم", "adm_search_user", color="blue")],
            [_btn("◀️ رجوع", "adm_back", color="red")],
        )

    @classmethod
    def admin_user_view(cls, uid, banned):
        return mk(
            [_btn("➕ إضافة نقاط", f"adm_add_pts_{uid}", color="green"),
             _btn("➖ خصم نقاط", f"adm_sub_pts_{uid}", color="red")],
            [_btn("✅ فك الحظر" if banned else "🚫 حظر",
                  f"adm_{'unban' if banned else 'ban'}_{uid}",
                  color="green" if banned else "red")],
            [_btn("◀️ رجوع", "adm_users", color="red")],
        )

    @classmethod
    def admin_admins_kb(cls, admins):
        rows = []
        for a in admins:
            rows.append([_btn(f"🗑️ إزالة  {a['full_name'] or a['tg_id']}",
                              f"adm_rem_admin_{a['tg_id']}", color="red")])
        rows.append([_btn("➕ إضافة أدمن", "adm_add_admin", color="green")])
        rows.append([_btn("◀️ رجوع", "adm_back", color="red")])
        return mk(*rows)

    @classmethod
    def admin_smm_sites(cls, sites):
        rows = []
        for s in sites:
            dot_color = "green" if s["is_active"] else "red"
            rows.append([
                _btn(f"{'✅' if s['is_active'] else '❌'} {s['name']}",
                     f"adm_smm_site_{s['id']}", color=dot_color),
                _btn("🗑️", f"adm_del_smm_{s['id']}", color="red"),
            ])
        rows.append([_btn("➕ إضافة موقع SMM", "adm_add_smm_site", color="green")])
        rows.append([_btn("◀️ رجوع", "adm_back", color="red")])
        return mk(*rows)

    @classmethod
    def admin_order_channels(cls, channels):
        rows = []
        for ch in channels:
            rows.append([_btn(f"🗑️ حذف {ch['channel_name']}",
                              f"adm_del_orch_{ch['channel_id']}", color="red")])
        rows.append([_btn("➕ إضافة قناة طلبات", "adm_add_orch", color="green")])
        rows.append([_btn("◀️ رجوع", "adm_back", color="red")])
        return mk(*rows)

    @classmethod
    def admin_database(cls):
        return mk(
            [_btn("📤 تصدير قاعدة البيانات (JSON)", "adm_db_export", color="blue")],
            [_btn("📥 استيراد قاعدة البيانات (JSON)", "adm_db_import", color="green")],
            [_btn("ℹ️ معلومات القاعدة", "adm_db_info", color="blue")],
            [_btn("◀️ رجوع", "adm_back", color="red")],
        )

    @classmethod
    def back(cls, cb="back_main"):
        return mk([_btn("◀️ رجوع", cb, color="red")])


# ══════════════════════════════════════════════════════════════════
#   6. تشغيل البوت
# ══════════════════════════════════════════════════════════════════
bot = telebot.TeleBot(config.BOT_TOKEN, parse_mode="HTML")
db.init_db()

USER_STATE = {}

# حماية من سبام زر "تحقق من الاشتراك" — يمنع تنفيذ الطلب لنفس المستخدم أكثر من مرة بالتزامن
_CHECK_SUB_INFLIGHT = set()
_CHECK_SUB_LOCK = threading.Lock()


def get_state(uid):
    return USER_STATE.get(uid, {"state": None, "data": {}})


def set_state(uid, s, **d):
    USER_STATE[uid] = {"state": s, "data": d}


def clear_state(uid):
    USER_STATE.pop(uid, None)


def is_admin(uid):
    if uid in config.ADMIN_IDS:
        return True
    conn = db.get_conn()
    r = conn.execute("SELECT 1 FROM extra_admins WHERE tg_id=?", (uid,)).fetchone()
    conn.close()
    return r is not None


def send(cid, text, markup=None, **kw):
    try:
        return bot.send_message(cid, text, reply_markup=markup, **kw)
    except Exception as e:
        print(f"[send error] {e}")
        return None


def edit(call, text, markup=None):
    try:
        bot.edit_message_text(text, call.message.chat.id,
                              call.message.message_id, reply_markup=markup, parse_mode="HTML")
    except Exception:
        try:
            bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")
        except Exception as e:
            print(f"[edit error] {e}")


def check_subs(uid):
    channels = db.get_mandatory_channels()
    missing = []
    for ch in channels:
        try:
            m = bot.get_chat_member(ch["channel_id"], uid)
            if m.status in ("left", "kicked"):
                missing.append(ch)
            else:
                db.record_join(uid, ch["channel_id"])
        except:
            missing.append(ch)
    return len(missing) == 0, missing


def welcome_text(user, ref_count):
    return (
        f"<b>اهـلاً بك في بوت رشق ترند - Trend 💎</b>\n\n"
        f"• البوت مختص لرشق جميع البرامج 🚀\n"
        f"• سارع بتجربة أسرع وافضل الخدمات ⚡\n\n"
        f"🎁 | ايديك : <code>{user['tg_id']}</code>\n"
        f"👤 | عدد نقاطك : <b>{user['points']:,}</b>"
    )


# ── إشعار انخفاض الرصيد ─────────────────────────────────────
def _send_low_points_alert(tg_id, pts, threshold):
    try:
        bot.send_message(tg_id,
            f"<b>⚠️ تنبيه: رصيدك منخفض!</b>\n\n"
            f"رصيدك الحالي: <b>{pts:,}</b> نقطة\n\n"
            f"<i>اشحن رصيدك الآن للاستمرار في استخدام الخدمات 🔋</i>",
            reply_markup=mk([_btn("🔋 شحن الآن", "back_main", color="green")]),
            parse_mode="HTML")
    except:
        pass


# ── التقرير اليومي ───────────────────────────────────────────
def send_daily_report():
    if db.get_config("daily_report_enabled", "1") != "1":
        return
    stats = db.get_daily_stats()
    text = (
        f"<b>📊 التقرير اليومي — {datetime.now().strftime('%Y-%m-%d')}</b>\n\n"
        f"<b></b>\n"
        f"👤 مستخدمون جدد: <b>{stats['new_users']:,}</b> | الإجمالي: {stats['total_users']:,}\n"
        f"📦 طلبات اليوم: <b>{stats['new_orders']:,}</b> | الإجمالي: {stats['total_orders']:,}\n"
        f"🛍️ طلبات المتجر: <b>{stats['store_orders']:,}</b>\n"
        f"⭐ نقاط مُنفقة: <b>{stats['points_spent']:,}</b>\n"
        f"💵 شحن مؤكد: <b>{stats['recharges']:,}</b> طلب\n"
        f"<b></b>"
    )
    all_admins = list(config.ADMIN_IDS) + [a["tg_id"] for a in db.get_extra_admins()]
    for aid in all_admins:
        try:
            bot.send_message(aid, text, parse_mode="HTML")
        except:
            pass


def daily_report_loop():
    """يبعت التقرير كل يوم الساعة 8 صباحاً"""
    import time as _time
    from datetime import timedelta
    while True:
        now = datetime.now()
        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= target:
            target = target + timedelta(days=1)
            target = target.replace(hour=8, minute=0, second=0, microsecond=0)
        wait = (target - now).total_seconds()
        _time.sleep(wait)
        send_daily_report()

def notify_order_channels(order_id, user, service_name, app_name, link, qty, pts_used):
    """إرسال تفاصيل الطلب لقنوات الطلبات"""
    channels = db.get_order_channels()
    if not channels:
        return
    text = (
        f"<b>✅ طلب جديد تم اكتماله #{order_id}</b>\n\n"
        f"<b></b>\n"
        f"<b>المستخدم:</b> {user.get('full_name', '—')}"
        f" (<code>{user.get('tg_id', '—')}</code>)\n"
        f"<b>القسم:</b> {app_name or '—'}\n"
        f"<b>الخدمة:</b> {service_name}\n"
        f"<b>الرابط:</b> <code>{link}</code>\n"
        f"<b>الكمية:</b> {qty:,}\n"
        f"<b>النقاط:</b> {pts_used:,}\n"
        f"<b>التاريخ:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"<b></b>"
    )
    bot_markup = mk(
        [_btn("دخول البوت🤖", url=f"https://t.me/{config.BOT_USERNAME.lstrip('@')}", color="green")]
    )
    for ch in channels:
        try:
            bot.send_message(ch["channel_id"], text, reply_markup=bot_markup)
        except Exception as e:
            print(f"[order_channel error] {ch['channel_id']}: {e}")




def _notify_admin_approve_order(order_id, user, service_name, app_name, link, qty, pts_used, order_type="smm"):
    """إشعار الأدمن بطلب جديد يحتاج موافقة"""
    text = (
        f"<b>🔔 طلب جديد يحتاج موافقتك #{order_id}</b>\n\n"
        f"<b></b>\n"
        f"<b>المستخدم:</b> {user.get('full_name', '—')} (<code>{user.get('tg_id', '—')}</code>)\n"
        f"<b>القسم:</b> {app_name or '—'}\n"
        f"<b>الخدمة:</b> {service_name}\n"
        f"<b>الرابط:</b> <code>{link}</code>\n"
        f"<b>الكمية:</b> {qty:,}\n"
        f"<b>النقاط:</b> {pts_used:,}\n"
        f"<b></b>"
    )
    markup = mk(
        [_btn("✅ موافقة وتنفيذ", f"adm_approve_{order_type}_{order_id}", color="green"),
         _btn("❌ رفض", f"adm_reject_{order_type}_{order_id}", color="red")],
    )
    all_admins = list(config.ADMIN_IDS) + [a["tg_id"] for a in db.get_extra_admins()]
    for aid in all_admins:
        try:
            bot.send_message(aid, text, reply_markup=markup)
        except Exception as e:
            print(f"[admin_notify error] {aid}: {e}")


def _notify_admin_approve_store_order(order_id, user, product_name, pts):
    """إشعار الأدمن بطلب متجر جديد"""
    text = (
        f"<b>🛍️ طلب متجر جديد #{order_id}</b>\n\n"
        f"<b></b>\n"
        f"<b>المستخدم:</b> {user.get('full_name', '—')} (<code>{user.get('tg_id', '—')}</code>)\n"
        f"<b>المنتج:</b> {product_name}\n"
        f"<b>النقاط:</b> {pts:,}\n"
        f"<b></b>"
    )
    markup = mk(
        [_btn("✅ موافقة وتسليم", f"adm_approve_store_{order_id}", color="green"),
         _btn("❌ رفض", f"adm_reject_store_{order_id}", color="red")],
    )
    all_admins = list(config.ADMIN_IDS) + [a["tg_id"] for a in db.get_extra_admins()]
    for aid in all_admins:
        try:
            bot.send_message(aid, text, reply_markup=markup)
        except Exception as e:
            print(f"[admin_store_notify error] {aid}: {e}")


def notify_admin_new_user(user_msg):
    u = user_msg.from_user
    total = db.get_users_count()
    text = (
        f"<b>مستخدم جديد دخل البوت</b>\n\n"
        f"<b>الاسم:</b> {u.full_name}\n"
        f"<b>المعرف:</b> @{u.username or '—'}\n"
        f"<b>الـ ID:</b> <code>{u.id}</code>\n\n"
        f"<b>إجمالي المستخدمين:</b> {total}"
    )
    for aid in config.ADMIN_IDS:
        try:
            bot.send_message(aid, text)
        except:
            pass
    for a in db.get_extra_admins():
        try:
            bot.send_message(a["tg_id"], text)
        except:
            pass


# ══════════════════════════════════════════════════════════════════
#   دوال مساعدة — إشعار الأدمن عند استلام رابط هدية
# ══════════════════════════════════════════════════════════════════
def _build_gift_notify_text(user_id, full_name, username, gift_code, pts):
    uname_str = f"@{username}" if username else "—"
    bu = config.BOT_USERNAME.lstrip("@")
    gift_link = f"https://t.me/{bu}?start=gift_{gift_code}"
    return (
        f"<b>🎁 مستخدم دخل برابط هدية!</b>\n\n"
        f"<b></b>\n"
        f"👤 الاسم: <b>{full_name}</b>\n"
        f"🔖 يوزر: {uname_str}\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"<b></b>\n"
        f"🔗 الرابط: {gift_link}\n"
        f"💰 النقاط المستلمة: <b>{pts:,}</b> نقطة\n"
        f"<b></b>"
    )

def _notify_admins_gift_claim(tg_user, gift_code, pts):
    """إشعار لما يجي المستخدم من msg (start)"""
    text = _build_gift_notify_text(
        tg_user.id,
        tg_user.full_name or "",
        tg_user.username or "",
        gift_code, pts
    )
    for admin_id in config.ADMIN_IDS:
        try:
            bot.send_message(admin_id, text, parse_mode="HTML")
        except:
            pass
    # إشعار الأدمنية الإضافية
    try:
        extra = db.get_extra_admins()
        for a in extra:
            try:
                bot.send_message(a["tg_id"], text, parse_mode="HTML")
            except:
                pass
    except:
        pass

def _notify_admins_gift_claim_db(uid, user_obj, gift_code, pts):
    """إشعار لما يجي المستخدم من قاعدة البيانات (بعد الاشتراك الإجباري)"""
    full_name = user_obj["full_name"] if user_obj else str(uid)
    username  = user_obj["username"]  if user_obj else ""
    text = _build_gift_notify_text(uid, full_name, username, gift_code, pts)
    for admin_id in config.ADMIN_IDS:
        try:
            bot.send_message(admin_id, text, parse_mode="HTML")
        except:
            pass
    try:
        extra = db.get_extra_admins()
        for a in extra:
            try:
                bot.send_message(a["tg_id"], text, parse_mode="HTML")
            except:
                pass
    except:
        pass


# ══════════════════════════════════════════════════════════════════
#   7. معالجات المستخدم
# ══════════════════════════════════════════════════════════════════
@bot.message_handler(commands=["start"])
def cmd_start(msg: Message):
    if db.get_config("bot_active", "1") == "0" and not is_admin(msg.from_user.id):
        send(msg.chat.id, "البوت متوقف حالياً. تابع القناة لمعرفة وقت العودة.")
        return

    args = msg.text.split(maxsplit=1)
    ref_code = invite_code = gift_code = None
    if len(args) > 1:
        p = args[1].strip()
        if p.startswith("invite_"):
            invite_code = p.replace("invite_", "")
        elif p.startswith("gift_"):
            gift_code = p.replace("gift_", "")
        else:
            ref_code = p

    user, referred_by, is_new = db.get_or_create(
        msg.from_user.id, msg.from_user.username or "",
        msg.from_user.full_name or "", ref_code
    )

    if is_new:
        notify_admin_new_user(msg)
        # الإحالة ستُكتمل بعد الاشتراك الإجباري عبر cb_check_sub → complete_referral

    if invite_code:
        ok, pts, err = db.claim_invite(msg.from_user.id, invite_code)
        if ok:
            send(msg.chat.id, f"<b>تم تفعيل كود الدعوة!</b>\n\nحصلت على <b>{pts}</b> نقطة!")

    ok, missing = check_subs(msg.from_user.id)
    if not ok:
        # خزّن كود الهدية مؤقتاً في الـ state لو فيه قنوات إجبارية
        if gift_code:
            set_state(msg.from_user.id, "pending_gift", gift_code=gift_code)
        send(msg.chat.id,
            "<b>يجب الاشتراك في القنوات التالية لاستخدام البوت:</b>",
            kb.subscribe_keyboard(missing, msg.from_user.id))
        return

    # لو وصل هنا يعني اشترك — نعطيه الهدية فوراً
    if gift_code:
        ok2, pts, err = db.claim_gift_link(msg.from_user.id, gift_code)
        if ok2:
            send(msg.chat.id,
                f"<b>🎁 تهانينا! استلمت هديتك!</b>\n\n"
                f"حصلت على <b>{pts:,}</b> نقطة! 🎉")
            # إشعار الأدمن
            _notify_admins_gift_claim(msg.from_user, gift_code, pts)
        else:
            send(msg.chat.id, f"<b>⚠️ {err}</b>")

    # لو مفيش قنوات إجبارية — نكمل الإحالة هنا مباشرة
    if is_new:
        result = db.complete_referral(msg.from_user.id)
        if result:
            ref_uid, ref_pts = result
            try:
                bot.send_message(ref_uid,
                    f"<b>🎉 دعوة مكتملة!</b>\n\n"
                    f"{msg.from_user.full_name} انضم عبر رابطك.\n"
                    f"حصلت على <b>{ref_pts:,}</b> نقطة!")
            except:
                pass

    user = db.get_user(msg.from_user.id)
    ref_c = db.get_referral_count(msg.from_user.id)
    orders_count = db.get_total_completed_orders()
    updates_ch = db.get_config("updates_channel")
    send(msg.chat.id, welcome_text(user, ref_c), kb.main_menu(updates_ch, orders_count))


@bot.callback_query_handler(func=lambda c: c.data == "back_main")
def cb_back_main(call: CallbackQuery):
    clear_state(call.from_user.id)
    user = db.get_user(call.from_user.id)
    ref_c = db.get_referral_count(call.from_user.id)
    orders_count = db.get_total_completed_orders()
    updates_ch = db.get_config("updates_channel")
    edit(call, welcome_text(user, ref_c), kb.main_menu(updates_ch, orders_count))


# ─── نقاطي ────────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "my_balance")
def cb_my_balance(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    edit(call,
        f"<b>💰 نقاطي</b>\n\n"
        f"<b></b>\n"
        f"رصيدك الحالي: <b>{user['points']:,}</b> نقطة\n"
        f"<b></b>",
        mk(
            [_btn("🔄 تحويل نقاط لمستخدم", "transfer_points", color="green")],
            [_btn("◀️ رجوع", "back_main", color="red")],
        ))


@bot.callback_query_handler(func=lambda c: c.data == "transfer_points")
def cb_transfer_points(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    set_state(call.from_user.id, "transfer_username")
    edit(call,
        f"<b>🔄 تحويل نقاط</b>\n\n"
        f"رصيدك: <b>{user['points']:,}</b> نقطة\n\n"
        f"<b></b>\n"
        f"أرسل <b>يوزرنيم</b> المستخدم اللي تريد تحويل له:\n"
        f"<i>مثال: @ahmed أو ahmed</i>",
        kb.back())


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "transfer_username")
def msg_transfer_username(msg: Message):
    uid = msg.from_user.id
    text = (msg.text or "").strip()
    # بحث بـ ID أو username
    target = None
    if text.lstrip("@").isdigit():
        target = db.get_user(int(text.lstrip("@")))
    else:
        target = db.get_user_by_username(text)
    if not target:
        send(msg.chat.id,
            f"❌ المستخدم غير موجود!\n\n"
            f"<i>تأكد إن المستخدم فتح البوت من قبل، وإن الـ username صح</i>\n"
            f"يمكنك أيضاً إرسال الـ ID مباشرة (مثال: <code>123456789</code>)")
        return
    if target["tg_id"] == uid:
        send(msg.chat.id, "❌ لا يمكنك التحويل لنفسك!")
        return
    user = db.get_user(uid)
    set_state(uid, "transfer_amount", target_id=target["tg_id"],
              target_name=target["full_name"], target_uname=target["username"] or str(target["tg_id"]))
    send(msg.chat.id,
        f"<b>🔄 تحويل إلى:</b> {target['full_name']}"
        f"{(' (@' + target['username'] + ')') if target['username'] else ''}\n\n"
        f"رصيدك: <b>{user['points']:,}</b> نقطة\n\n"
        f"كم نقطة تريد تحويلها؟",
        kb.back())


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "transfer_amount")
def msg_transfer_amount(msg: Message):
    uid = msg.from_user.id
    try:
        amount = int((msg.text or "").strip().replace(",", ""))
        if amount <= 0:
            raise ValueError
    except:
        send(msg.chat.id, "⚠️ أرسل رقماً صحيحاً أكبر من صفر!")
        return
    d = get_state(uid).get("data", {})
    user = db.get_user(uid)
    if user["points"] < amount:
        send(msg.chat.id,
            f"❌ رصيدك غير كافٍ!\n"
            f"رصيدك: <b>{user['points']:,}</b> | المطلوب: <b>{amount:,}</b>")
        return
    set_state(uid, "transfer_confirm",
              target_id=d["target_id"], target_name=d["target_name"],
              target_uname=d["target_uname"], amount=amount)
    send(msg.chat.id,
        f"<b>تأكيد التحويل</b>\n\n"
        f"<b></b>\n"
        f"إلى: <b>{d['target_name']}</b> (@{d['target_uname']})\n"
        f"المبلغ: <b>{amount:,}</b> نقطة\n"
        f"رصيدك بعد التحويل: <b>{user['points'] - amount:,}</b> نقطة\n"
        f"<b></b>",
        mk(
            [_btn("✅ تأكيد التحويل", "transfer_do", color="green")],
            [_btn("❌ إلغاء", "back_main", color="red")],
        ))


@bot.callback_query_handler(func=lambda c: c.data == "transfer_do")
def cb_transfer_do(call: CallbackQuery):
    uid = call.from_user.id
    state = get_state(uid)
    if state.get("state") != "transfer_confirm":
        bot.answer_callback_query(call.id, "انتهت الجلسة، حاول مجدداً.")
        return
    d = state.get("data", {})
    amount = d.get("amount", 0)
    target_id = d.get("target_id")
    if not db.deduct_points(uid, amount):
        bot.answer_callback_query(call.id, "❌ رصيدك غير كافٍ!", show_alert=True)
        return
    db.add_points(target_id, amount)
    clear_state(uid)
    sender = db.get_user(uid)
    target = db.get_user(target_id)
    edit(call,
        f"<b>✅ تم التحويل بنجاح!</b>\n\n"
        f"<b></b>\n"
        f"إلى: <b>{d['target_name']}</b>\n"
        f"المبلغ: <b>{amount:,}</b> نقطة\n"
        f"رصيدك الجديد: <b>{sender['points']:,}</b> نقطة\n"
        f"<b></b>",
        kb.back())
    try:
        bot.send_message(target_id,
            f"<b>🎁 استلمت تحويل نقاط!</b>\n\n"
            f"من: <b>{sender['full_name']}</b>\n"
            f"المبلغ: <b>+ {amount:,}</b> نقطة 🎉\n"
            f"رصيدك الجديد: <b>{target['points']:,}</b> نقطة")
    except:
        pass


# ─── لوحتي الشخصية ───────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "my_account")
def cb_my_account(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    ref_c = db.get_referral_count(call.from_user.id)
    orders = db.get_user_orders(call.from_user.id, limit=100)
    comp = sum(1 for o in orders if o["status"].lower() == "completed")
    pend = sum(1 for o in orders if o["status"].lower() in ("pending", "inprogress"))
    edit(call,
        f"<b>لوحتي الشخصية</b>\n\n"
        f"<b></b>\n"
        f"<b>المعرف:</b>  <code>{call.from_user.id}</code>\n"
        f"<b>الاسم:</b>  {call.from_user.full_name}\n"
        f"<b>اليوزر:</b>  @{call.from_user.username or '—'}\n"
        f"<b></b>\n"
        f"<b>النقاط:</b>  <b>{user['points']:,}</b>\n"
        f"<b>الدعوات:</b>  <b>{ref_c}</b>\n"
        f"<b></b>\n"
        f"<b>إجمالي الطلبات:</b>  <b>{len(orders)}</b>\n"
        f"<b>مكتملة:</b>  {comp}  |  <b>جارية:</b>  {pend}\n",
        kb.back())


# ─── طلباتي ──────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "my_orders")
def cb_my_orders(call: CallbackQuery):
    orders = db.get_user_orders(call.from_user.id, limit=8)
    total = db.get_user_orders_count(call.from_user.id)
    if not orders:
        edit(call, "<b>طلباتي</b>\n\nلا توجد طلبات بعد.", kb.back())
        return
    icons = {"pending": "⏳", "inprogress": "🔄", "completed": "✅",
             "partial": "⚠️", "canceled": "❌"}
    text = f"<b>طلباتي  |  الإجمالي: {total}</b>\n\n"
    for o in orders:
        ic = icons.get(o["status"].lower(), "•")
        text += (f"{ic} <b>طلب #{o['id']}</b> — {o.get('service_name', '')}\n"
                 f"    الكمية: {o['quantity']:,} | نقاط: {o['points_used']:,}\n\n")
    edit(call, text, kb.orders_list_keyboard(orders))


@bot.callback_query_handler(func=lambda c: c.data.startswith("order_detail_"))
def cb_order_detail(call: CallbackQuery):
    oid = int(call.data.split("_")[-1])
    o = db.get_order(oid)
    if not o or o["user_id"] != call.from_user.id:
        bot.answer_callback_query(call.id, "الطلب غير موجود")
        return
    status_ar = smm.arabic_status(o["status"])
    edit(call,
        f"<b>تفاصيل الطلب #{o['id']}</b>\n\n"
        f"<b></b>\n"
        f"<b>القسم:</b>  {o.get('app_name', '—')}\n"
        f"<b>الخدمة:</b>  {o['service_name']}\n"
        f"<b>رقم API:</b>  <code>{o['api_order_id'] or 'لا يوجد'}</code>\n"
        f"<b>الرابط:</b>  <code>{o['link']}</code>\n"
        f"<b>الكمية:</b>  {o['quantity']:,}\n"
        f"<b>النقاط:</b>  {o['points_used']:,}\n"
        f"<b>الحالة:</b>  {status_ar}\n"
        f"<b>التاريخ:</b>  {str(o['created_at'])[:16]}\n"
        f"<b></b>",
        kb.order_detail_keyboard(oid))


@bot.callback_query_handler(func=lambda c: c.data.startswith("order_refresh_"))
def cb_order_refresh(call: CallbackQuery):
    oid = int(call.data.split("_")[-1])
    o = db.get_order(oid)
    if not o or not o["api_order_id"]:
        bot.answer_callback_query(call.id, "لا يوجد رقم API للطلب")
        return
    site_id = o["site_id"] if "site_id" in o.keys() else None
    r = smm.get_status(o["api_order_id"], site_id)
    status = r.get("status", o["status"])
    db.update_order(oid, status.lower())
    bot.answer_callback_query(call.id, f"الحالة: {smm.arabic_status(status)}")
    call.data = f"order_detail_{oid}"
    cb_order_detail(call)


# ─── الدعم ───────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "support")
def cb_support(call: CallbackQuery):
    sup = db.get_config("support_username", "@ssusus")
    edit(call,
        f"<b>الدعم الفني</b>\n\n"
        f"<b></b>\n"
        f"للتواصل: {sup}\n"
        f"الرد خلال 24 ساعة\n"
        f"<b></b>",
        kb.back())


TERMS_DEFAULT = (
    "شروط الاستخدام : ⛔️\n\n"
    "• في حال تغير اليوزر خلال تنفيذ الطلب يعتبر الطلب مكتمل جزئي ولا يحق لصاحبه المطالبه باي تعويض كان ❌\n\n"
    "• عند التواصل مع خدمة العملاء لدينا يرجي التحدث بطريقة جيدة وتبادل الاحترام حتي لا يتم حظر حسابك ✔️\n\n"
    "• في حال حذف اي منشور او فيديو خلال تنفيذ الطلب يعتبر الطلب مكتمل ولا يحق لصاحبه المطالبه باي تعويض كان ❌\n\n"
    "• في حال قمت بتغيير يوزر الحساب بعد ان تم انتهاء من الطلب لا يمكنك ان تقوم بالمطالبة بتعويض ‼️\n\n"
    "• جميع الحسابات يجب أن تكون عامة وليست خاصة ‼️\n\n"
    "• لا يمكن إلغاء أي طلب بعد إرساله، إنتبه جيداً قبل عمل طلب جديد ‼️\n\n"
    "• في حال تم وضع الحساب خاص اثناء التنفيذ يعتبر الطلب مكتمل جزئي ولا يتم تعويضك ‼️\n\n"
    "• سيرفراتنا تعتمد على الاعداد الذي يتم تثبيتها تلقائيا في الطلب 🔥\n\n"
    "• يجب عليك قراءة تفاصيل كل خدمة قبل عمل طلب جديد ‼️\n\n"
    "• لا يتم إلغاء وإرجاع مبلغ أي طلب لأي سبب من الاسباب، إلا في حال فشل النظام بإتمام العمل\n\n"
    "• عمل طلب جديد يعني أنك قرأت جيداً ووافقت على جميع شروط البوت وسياسة الإسترجاع ✔️\n\n"
    "⚠️ هام — نظام تعويض تلقائي !!"
)


@bot.callback_query_handler(func=lambda c: c.data == "terms")
def cb_terms(call: CallbackQuery):
    sup = db.get_config("support_username", "@ssusus")
    terms = db.get_config("terms_text", "").strip() or TERMS_DEFAULT
    full_text = terms + f"\n\n• للتواصل مع المطور: {sup} ✔️"
    edit(call, full_text, kb.back())


# ══════════════════════════════════════════════════════════════════
#   8. تجميع النقاط
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "collect_section")
def cb_collect(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    points_info = db.get_config("points_charge_info", "لشحن النقاط تواصل مع الدعم").strip()
    info_text = f"\n\n💳 {points_info}" if points_info else ""
    edit(call,
        f"<b>تجميع النقاط</b>\n\n"
        f"<b></b>\n"
        f"رصيدك الحالي:  <b>{user['points']:,}</b> نقطة\n"
        f"<b></b>\n\n"
        f"<b>طرق التجميع:</b>\n"
        f"  🎡 عجلة الحظ — من 10 إلى 1000 نقطة\n"
        f"  🌅 الهدية اليومية\n"
        f"  🗓️ الهدية الأسبوعية\n"
        f"  📢 الاشتراك بالقنوات\n"
        f"  🔗 رابط الدعوة\n"
        f"  🎟️ كود دعوة"
        f"{info_text}",
        kb.collect_menu())


# ─── الهدية اليومية ──────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "daily_gift")
def cb_daily(call: CallbackQuery):
    ok, pts = db.claim_daily(call.from_user.id)
    user = db.get_user(call.from_user.id)
    if ok:
        edit(call,
            "<b>الهدية اليومية</b>\n\n"
            f"حصلت على <b>{pts}</b> نقطة! 🎉\n"
            f"رصيدك الآن: <b>{user['points']:,}</b>\n\n"
            f"<i>عد غداً لهدية جديدة</i>",
            kb.back("collect_section"))
    else:
        edit(call,
            "<b>الهدية اليومية</b>\n\n"
            "حصلت على هديتك اليوم بالفعل!\n\n<i>عد غداً</i>",
            kb.back("collect_section"))


# ─── الهدية الأسبوعية ────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "weekly_gift")
def cb_weekly(call: CallbackQuery):
    ok, pts, days = db.claim_weekly(call.from_user.id)
    user = db.get_user(call.from_user.id)
    if ok:
        edit(call,
            f"<b>الهدية الأسبوعية</b>\n\n"
            f"حصلت على <b>{pts}</b> نقطة! 🎉\n"
            f"رصيدك: <b>{user['points']:,}</b>\n\n<i>عد بعد 7 أيام</i>",
            kb.back("collect_section"))
    else:
        edit(call,
            f"<b>الهدية الأسبوعية</b>\n\n"
            f"تبقى <b>{days}</b> يوم على هديتك القادمة.",
            kb.back("collect_section"))


# ─── عجلة الحظ ───────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "wheel_open")
def cb_wheel_open(call: CallbackQuery):
    can, hrs = db.can_spin(call.from_user.id)
    prizes = db.get_wheel_prizes()
    user = db.get_user(call.from_user.id)
    cool_hrs = db.get_config("wheel_cooldown_hrs", "6")

    if not prizes:
        edit(call, "<b>عجلة الحظ</b>\n\nلا توجد جوائز متاحة حالياً.", kb.back("collect_section"))
        return

    if not can:
        edit(call,
            f"<b>عجلة الحظ</b>\n\n"
            f"<b></b>\n"
            f"تبقى <b>{hrs}</b> ساعة على الدورة القادمة.\n"
            f"رصيدك: <b>{user['points']:,}</b>\n"
            f"<b></b>",
            kb.wheel_keyboard(False))
        return

    wheel_txt = build_wheel_display(prizes)
    edit(call,
        f"<b>عجلة الحظ</b>\n\n"
        f"<b></b>\n"
        f"الجوائز المتاحة:\n<code>{wheel_txt}</code>\n"
        f"<b></b>\n"
        f"رصيدك: <b>{user['points']:,}</b>\n"
        f"كل <b>{cool_hrs}</b> ساعات\n"
        f"<b></b>",
        kb.wheel_keyboard(True))


@bot.callback_query_handler(func=lambda c: c.data == "wheel_spin")
def cb_wheel_spin(call: CallbackQuery):
    can, hrs = db.can_spin(call.from_user.id)
    if not can:
        bot.answer_callback_query(call.id, f"تبقى {hrs} ساعة!", show_alert=True)
        return

    prizes = db.get_wheel_prizes()
    if not prizes:
        bot.answer_callback_query(call.id, "لا توجد جوائز!", show_alert=True)
        return

    # اختيار الفائز بالوزن
    total = sum(float(p["weight"]) for p in prizes)
    if total <= 0:
        bot.answer_callback_query(call.id, "خطأ في إعداد الجوائز!", show_alert=True)
        return

    r = random.uniform(0, total)
    cum = 0.0
    won_idx = 0
    won_pts = prizes[0]["points"]
    for i, p in enumerate(prizes):
        cum += float(p["weight"])
        if r <= cum:
            won_idx = i
            won_pts = p["points"]
            break

    db.add_points(call.from_user.id, won_pts)
    db.mark_spin(call.from_user.id)

    # حركة العجلة
    frames = spin_animation_frames(prizes, won_idx)
    for title, wheel in frames[:-1]:
        try:
            bot.edit_message_text(
                f"<b>{title}</b>\n\n<code>{wheel}</code>",
                call.message.chat.id, call.message.message_id,
                parse_mode="HTML")
            time.sleep(0.7)
        except:
            pass

    # النتيجة النهائية
    final_title, final_wheel = frames[-1]
    user = db.get_user(call.from_user.id)
    max_p = max(p["points"] for p in prizes)
    if won_pts >= max_p:
        reaction = "🏆 جائزة كبرى! الكل يحسدك الآن!"
    elif won_pts >= max_p * 0.4:
        reaction = "🎉 جائزة ممتازة!"
    elif won_pts >= max_p * 0.1:
        reaction = "👍 جائزة جيدة"
    else:
        reaction = "💪 لا بأس، حاول مرة أخرى لاحقاً"

    try:
        bot.edit_message_text(
            f"<b>🎯 نتيجة عجلة الحظ</b>\n\n"
            f"<code>{final_wheel}</code>\n\n"
            f"<b></b>\n"
            f"ربحت <b>{won_pts:,}</b> نقطة! {reaction}\n"
            f"رصيدك الآن: <b>{user['points']:,}</b>\n"
            f"<b></b>",
            call.message.chat.id, call.message.message_id,
            reply_markup=kb.back("collect_section"),
            parse_mode="HTML")
    except:
        try:
            edit(call,
                f"<b>ربحت {won_pts:,} نقطة!</b>\nرصيدك: {user['points']:,}",
                kb.back("collect_section"))
        except:
            pass


# ─── الإحالة ─────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "my_referral_link")
def cb_referral(call: CallbackQuery):
    user = db.get_user(call.from_user.id)
    ref_c = db.get_referral_count(call.from_user.id)
    ref_pts = int(db.get_config("referral_points", "50"))
    bu = config.BOT_USERNAME.lstrip("@")
    link = f"https://t.me/{bu}?start={user['referral_code']}"
    edit(call,
        f"<b>رابط الدعوة الخاص بك</b>\n\n"
        f"<b></b>\n"
        f"رابطك:\n<code>{link}</code>\n"
        f"<b></b>\n"
        f"مكافأة كل صديق: <b>{ref_pts}</b> نقطة\n"
        f"دعواتك حتى الآن: <b>{ref_c}</b>\n"
        f"<b></b>\n\n"
        f"<i>شارك الرابط واجمع نقاط بلا حدود!</i>",
        kb.back("collect_section"))


# ─── كود دعوة ─────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "enter_invite_code")
def cb_enter_code(call: CallbackQuery):
    set_state(call.from_user.id, "waiting_invite_code")
    edit(call,
        "<b>إدخال كود دعوة</b>\n\nأرسل الكود الآن:",
        kb.back("collect_section"))


# ─── أفضل 5 محيلين ───────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "top_referrers")
def cb_top_referrers(call: CallbackQuery):
    top = db.get_top_referrers(5)
    if not top:
        edit(call, "<b>أفضل 5 بالدعوات</b>\n\nلا توجد دعوات بعد.", kb.back("collect_section"))
        return
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    text = "<b>أفضل 5 بالدعوات</b>\n\n<b></b>\n"
    for i, r in enumerate(top):
        name = r["full_name"] or f"مستخدم {r['tg_id']}"
        uname = f"@{r['username']}" if r["username"] else ""
        text += (f"{medals[i]} <b>{name}</b> {uname}\n"
                 f"   الدعوات: <b>{r['ref_count']}</b> | النقاط: <b>{r['total_pts']:,}</b>\n")
    text += "<b></b>"
    edit(call, text, kb.back("collect_section"))


# ─── قنوات النقاط ────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "points_channels")
def cb_points_channels(call: CallbackQuery):
    channels = db.get_points_channels()
    if not channels:
        edit(call, "<b>قنوات النقاط</b>\n\nلا توجد قنوات حالياً.",
             kb.back("collect_section"))
        return
    text = "<b>اشترك في القنوات واكسب نقاط!</b>\n\n<b></b>\n"
    for ch in channels:
        text += f"  {ch['channel_name']}  —  +{ch['points_reward']} نقطة\n"
    text += "<b></b>\n\n<i>اشترك ثم اضغط جمّعت نقاطي</i>"
    edit(call, text, kb.points_ch_keyboard(channels))


@bot.callback_query_handler(func=lambda c: c.data == "collect_pts_now")
def cb_collect_pts(call: CallbackQuery):
    uid = call.from_user.id
    earned = 0
    for ch in db.get_points_channels():
        if db.has_channel_pts(uid, ch["channel_id"]):
            continue
        try:
            m = bot.get_chat_member(ch["channel_id"], uid)
            if m.status not in ("left", "kicked"):
                db.add_points(uid, ch["points_reward"])
                db.mark_channel_pts(uid, ch["channel_id"])
                earned += ch["points_reward"]
        except:
            pass
    msg = f"حصلت على {earned:,} نقطة! 🎉" if earned > 0 else "لم تحصل على نقاط جديدة."
    bot.answer_callback_query(call.id, msg, show_alert=True)
    cb_collect(call)


# ─── الاشتراك الإجباري ────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("check_sub_"))
def cb_check_sub(call: CallbackQuery):
    uid = call.from_user.id
    # منع سبام الضغط المتكرر/المتزامن على زر التحقق (يمنع أي احتمال لمنح نقاط دعوة مضاعفة)
    with _CHECK_SUB_LOCK:
        if uid in _CHECK_SUB_INFLIGHT:
            bot.answer_callback_query(call.id, "جارٍ التحقق بالفعل، انتظر لحظة... ⏳")
            return
        _CHECK_SUB_INFLIGHT.add(uid)
    try:
        ok, missing = check_subs(uid)
        if ok:
            bot.answer_callback_query(call.id, "تم التحقق! أهلاً بك. ✅", show_alert=True)
            # تسجيل الدعوة بعد اجتياز الاشتراك الإجباري
            result = db.complete_referral(uid)
            if result:
                referred_by, ref_pts = result
                user = db.get_user(uid)
                try:
                    bot.send_message(referred_by,
                        f"<b>🎉 دعوة مكتملة!</b>\n\n"
                        f"{user['full_name']} اشترك في القنوات وأصبح عضواً.\n"
                        f"حصلت على <b>{ref_pts:,}</b> نقطة!")
                except:
                    pass
            # معالجة هدية مؤجلة (لو المستخدم جه عبر رابط هدية وكانت فيه قنوات إجبارية)
            pending = get_state(uid)
            if pending.get("state") == "pending_gift":
                gift_code = pending.get("data", {}).get("gift_code", "")
                clear_state(uid)
                if gift_code:
                    ok2, pts, err = db.claim_gift_link(uid, gift_code)
                    if ok2:
                        try:
                            bot.send_message(uid,
                                f"<b>🎁 تهانينا! استلمت هديتك!</b>\n\n"
                                f"حصلت على <b>{pts:,}</b> نقطة! 🎉")
                            # إشعار الأدمن
                            user_obj = db.get_user(uid)
                            _notify_admins_gift_claim_db(uid, user_obj, gift_code, pts)
                        except:
                            pass
            cb_back_main(call)
        else:
            bot.answer_callback_query(call.id, f"لم تشترك بعد في {len(missing)} قناة!", show_alert=True)
    finally:
        with _CHECK_SUB_LOCK:
            _CHECK_SUB_INFLIGHT.discard(uid)


# ══════════════════════════════════════════════════════════════════
#   9. الخدمات المجانية
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "free_services")
def cb_free_services(call: CallbackQuery):
    if db.get_config("free_svc_enabled", "1") == "0":
        edit(call, "<b>🎁 الخدمات المجانية</b>\n\nهذا القسم متوقف حالياً.", kb.back("my_services"))
        return
    services = db.get_free_services()
    if not services:
        edit(call, "<b>🎁 الخدمات المجانية</b>\n\nلا توجد خدمات متاحة حالياً.", kb.back("my_services"))
        return
    daily_limit = int(db.get_config("free_services_daily_limit", "3"))
    used_today = db.get_free_claim_count_today_total(call.from_user.id)
    if used_today >= daily_limit:
        edit(call,
            "<b>🎁 الخدمات المجانية</b>\n\n"
            f"⚠️ استنفدت حد اليوم ({daily_limit} مرات).\n"
            "عد غداً للمحاولة مجدداً.",
            kb.back("my_services"))
        return
    # تسجيل دخول القسم كمرة استخدام
    db.add_free_claim(call.from_user.id, 0, 0, "", "", "section_visit")
    used_today += 1
    remaining = max(daily_limit - used_today, 0)
    edit(call,
        "<b>🎁 الخدمات المجانية</b>\n\n"
        "<b></b>\n"
        f"حد الاستخدام اليومي للمستخدم: <b>{daily_limit}</b> مرة\n"
        f"المتبقي اليوم: <b>{remaining}</b> مرة\n"
        "<b></b>\n"
        "اختر الخدمة المجانية المطلوبة.\n"
        "يمكنك استخدام خدمة مجانية واحدة فقط في اليوم.\n"
        "<b></b>",
        kb.free_services_menu(services, back_cb="my_services"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("free_svc_"))
def cb_free_svc_select(call: CallbackQuery):
    sid = int(call.data.split("_")[-1])
    svc = db.get_free_service(sid)
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة")
        return

    uid = call.from_user.id
    set_state(uid, "free_svc_link", svc_id=sid)
    edit(call,
        f"<b>{svc['name']}</b>\n\n"
        f"<b></b>\n"
        f"الوصف: {svc['description'] or '—'}\n"
        f"الكمية: من {svc['min_qty']:,} إلى {svc['max_qty']:,}\n"
        f"<b></b>\n\n"
        f"<b>الخطوة 1:</b> أرسل الرابط المطلوب:",
        kb.back("free_services"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "free_svc_link")
def msg_free_svc_link(msg: Message):
    link = msg.text.strip() if msg.text else ""
    if not (link.startswith("http") or link.startswith("@") or "t.me" in link):
        send(msg.chat.id, "⚠️ الرابط غير صحيح! أرسل رابطاً صحيحاً:")
        return
    d = get_state(msg.from_user.id)["data"]
    svc = db.get_free_service(d["svc_id"])
    if not svc:
        send(msg.chat.id, "الخدمة غير موجودة!")
        clear_state(msg.from_user.id)
        return
    set_state(msg.from_user.id, "free_svc_qty", svc_id=d["svc_id"], link=link)
    send(msg.chat.id,
        f"الرابط: <code>{link}</code>\n\n"
        f"<b>الخطوة 2:</b> أرسل الكمية (من {svc['min_qty']:,} إلى {svc['max_qty']:,}):",
        kb.back("free_services"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "free_svc_qty")
def msg_free_svc_qty(msg: Message):
    try:
        qty = int((msg.text or "").strip().replace(",", ""))
    except:
        send(msg.chat.id, "⚠️ أرسل رقماً صحيحاً!")
        return
    d = get_state(msg.from_user.id)["data"]
    svc = db.get_free_service(d["svc_id"])
    if not svc:
        send(msg.chat.id, "الخدمة غير موجودة!")
        clear_state(msg.from_user.id)
        return
    if qty < svc["min_qty"] or qty > svc["max_qty"]:
        send(msg.chat.id, f"⚠️ الكمية بين {svc['min_qty']:,} و {svc['max_qty']:,}!")
        return

    uid = msg.from_user.id
    site_id = svc["site_id"] if "site_id" in svc.keys() else None
    result = smm.create_order(svc["api_service_id"], d["link"], qty, site_id)
    api_id = str(result.get("order", ""))
    err = result.get("error")

    if err:
        db.add_free_claim(uid, svc["id"], qty, d["link"], "", "failed")
        send(msg.chat.id, f"<b>❌ فشل الطلب!</b>\n\n{err}\n\n<i>تم احتساب هذه المحاولة من حدك اليومي</i>", kb.back("free_services"))
    else:
        db.add_free_claim(uid, svc["id"], qty, d["link"], api_id, "inprogress")
        send(msg.chat.id,
            f"<b>✅ تم إرسال الطلب المجاني!</b>\n\n"
            f"<b></b>\n"
            f"الخدمة: {svc['name']}\n"
            f"الكمية: {qty:,}\n"
            f"رقم API: <code>{api_id or 'معلق'}</code>\n"
            f"<b></b>",
            kb.back("free_services"))
    clear_state(uid)


# ══════════════════════════════════════════════════════════════════
#   10. خدماتي (الأقسام)
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "my_services")
def cb_my_services(call: CallbackQuery):
    apps = db.get_apps()
    free_services_available = (db.get_config("free_svc_enabled", "1") == "1") and bool(db.get_free_services())
    if not apps and not free_services_available:
        edit(call, "<b>خدماتي</b>\n\nلا توجد أقسام متاحة حالياً.", kb.back())
        return
    user = db.get_user(call.from_user.id)
    edit(call,
        f"<b>خدماتي — اختر القسم</b>\n\n"
        f"<b></b>\n"
        f"رصيدك: <b>{user['points']:,}</b> نقطة\n"
        f"<b></b>",
        kb.apps_keyboard(apps, include_free=free_services_available))


@bot.callback_query_handler(func=lambda c: c.data == "my_services_free")
def cb_my_services_free(call: CallbackQuery):
    if db.get_config("free_svc_enabled", "1") == "0":
        edit(call, "<b>🎁 الخدمات المجانية</b>\n\nهذا القسم متوقف حالياً.", kb.back("my_services"))
        return
    services = db.get_free_services()
    if not services:
        edit(call, "<b>🎁 الخدمات المجانية</b>\n\nلا توجد خدمات متاحة حالياً.", kb.back("my_services"))
        return
    daily_limit = int(db.get_config("free_services_daily_limit", "3"))
    used_today = db.get_free_claim_count_today_total(call.from_user.id)
    if used_today >= daily_limit:
        edit(call,
            "<b>🎁 الخدمات المجانية</b>\n\n"
            f"⚠️ استنفدت حد اليوم ({daily_limit} مرات).\n"
            "عد غداً للمحاولة مجدداً.",
            kb.back("my_services"))
        return
    # تسجيل دخول القسم كمرة استخدام
    db.add_free_claim(call.from_user.id, 0, 0, "", "", "section_visit")
    used_today += 1
    remaining = max(daily_limit - used_today, 0)
    edit(call,
        "<b>🎁 الخدمات المجانية</b>\n\n"
        "<b></b>\n"
        f"حد الاستخدام اليومي للمستخدم: <b>{daily_limit}</b> مرة\n"
        f"المتبقي اليوم: <b>{remaining}</b> مرة\n"
        "<b></b>\n"
        "اختر الخدمة المجانية المطلوبة.\n"
        "يمكنك استخدام خدمة مجانية واحدة فقط في اليوم.\n"
        "<b></b>",
        kb.free_services_menu(services, back_cb="my_services"))


@bot.callback_query_handler(func=lambda c: c.data == "adm_pending_orders_placeholder")
def _placeholder(call):
    pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("app_") and not c.data.startswith("app_s"))
def cb_open_app(call: CallbackQuery):
    try:
        app_id = int(call.data.split("_")[1])
    except:
        return
    app = db.get_app(app_id)
    if not app:
        bot.answer_callback_query(call.id, "القسم غير موجود")
        return
    services = db.get_app_services(app_id)
    user = db.get_user(call.from_user.id)
    if not services:
        edit(call, f"<b>{app['name']}</b>\n\nلا توجد خدمات في هذا القسم.",
             kb.back("my_services"))
        return
    nm = f"{app['emoji']} {app['name']}" if app.get("emoji") else app['name']
    edit(call,
        f"<b>{nm}</b>\n\n"
        f"<b></b>\n"
        f"رصيدك: <b>{user['points']:,}</b> نقطة\n"
        f"السعر: بالنقاط لكل 1000 وحدة\n"
        f"<b></b>",
        kb.app_services_keyboard(app_id, services))


@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_"))
def cb_open_service(call: CallbackQuery):
    try:
        sid = int(call.data.split("_")[1])
    except:
        return
    svc = db.get_service(sid)
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة")
        return
    app = db.get_app(svc["app_id"])
    user = db.get_user(call.from_user.id)
    p1k = svc["points_per_1000"]
    max_can = user["points"] * 1000 // p1k if p1k else 0
    nm = f"{svc['emoji']} {svc['name']}" if svc.get("emoji") else svc['name']
    app_nm = f"{app['emoji']} {app['name']}" if app and app.get("emoji") else (app['name'] if app else "—")

    set_state(call.from_user.id, "svc_link", svc_id=sid, app_id=svc["app_id"])
    edit(call,
        f"<b>{nm}</b>\n"
        f"القسم: {app_nm}\n\n"
        f"<b></b>\n"
        f"السعر: <b>{p1k:,}</b> نقطة / 1000 وحدة\n"
        f"الحد الأدنى: <b>{svc['min_qty']:,}</b>\n"
        f"الحد الأقصى: <b>{svc['max_qty']:,}</b>\n"
        f"رصيدك: <b>{user['points']:,}</b> نقطة\n"
        f"يمكنك طلب: <b>{max_can:,}</b> وحدة\n"
        f"<b></b>\n\n"
        f"<b>الخطوة 1:</b> أرسل الرابط:",
        kb.back(f"app_{svc['app_id']}"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "svc_link")
def msg_svc_link(msg: Message):
    link = (msg.text or "").strip()
    if not (link.startswith("http") or "t.me" in link or link.startswith("@")):
        send(msg.chat.id, "⚠️ الرابط غير صحيح!")
        return
    d = get_state(msg.from_user.id)["data"]
    svc = db.get_service(d["svc_id"])
    if not svc:
        send(msg.chat.id, "الخدمة غير موجودة!")
        clear_state(msg.from_user.id)
        return
    set_state(msg.from_user.id, "svc_qty", svc_id=d["svc_id"], app_id=d["app_id"], link=link)
    send(msg.chat.id,
        f"الرابط: <code>{link}</code>\n\n"
        f"<b>الخطوة 2:</b> أرسل الكمية (من {svc['min_qty']:,} إلى {svc['max_qty']:,}):",
        kb.back(f"app_{d['app_id']}"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "svc_qty")
def msg_svc_qty(msg: Message):
    try:
        qty = int((msg.text or "").strip().replace(",", ""))
    except:
        send(msg.chat.id, "⚠️ أرسل رقماً!")
        return
    d = get_state(msg.from_user.id)["data"]
    svc = db.get_service(d["svc_id"])
    if not svc:
        send(msg.chat.id, "الخدمة غير موجودة!")
        clear_state(msg.from_user.id)
        return
    if qty < svc["min_qty"] or qty > svc["max_qty"]:
        send(msg.chat.id, f"⚠️ الكمية بين {svc['min_qty']:,} و {svc['max_qty']:,}!")
        return
    p1k = svc["points_per_1000"]
    pts_needed = math.ceil(qty * p1k / 1000)
    user = db.get_user(msg.from_user.id)
    enough = user["points"] >= pts_needed
    app = db.get_app(svc["app_id"])
    app_nm = f"{app['emoji']} {app['name']}" if app and app.get("emoji") else (app['name'] if app else "—")
    svc_nm = f"{svc['emoji']} {svc['name']}" if svc.get("emoji") else svc['name']
    warn = "" if enough else f"\n\n<b>⚠️ نقاطك غير كافية!</b> ينقصك <b>{pts_needed - user['points']:,}</b> نقطة."
    set_state(msg.from_user.id, "svc_confirm",
              svc_id=d["svc_id"], app_id=d["app_id"], link=d["link"], qty=qty, pts_needed=pts_needed)
    send(msg.chat.id,
        f"<b>تأكيد الطلب</b>\n\n"
        f"<b></b>\n"
        f"القسم: {app_nm}\n"
        f"الخدمة: {svc_nm}\n"
        f"الرابط: <code>{d['link']}</code>\n"
        f"الكمية: <b>{qty:,}</b>\n"
        f"التكلفة: <b>{pts_needed:,}</b> نقطة\n"
        f"رصيدك: <b>{user['points']:,}</b>\n"
        f"<b></b>{warn}",
        kb.confirm_keyboard() if enough else kb.back("my_services"))


@bot.callback_query_handler(func=lambda c: c.data == "order_confirm")
def cb_order_confirm(call: CallbackQuery):
    state = get_state(call.from_user.id)
    s = state.get("state")
    d = state.get("data", {})
    if s == "svc_confirm":
        _do_svc_order(call, d)
    elif s == "fund_confirm":
        _do_fund_order(call, d)
    else:
        bot.answer_callback_query(call.id, "انتهت الجلسة، ابدأ من جديد.")


def _do_svc_order(call, d):
    svc = db.get_service(d["svc_id"])
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير متاحة")
        return
    pts = d["pts_needed"]
    qty = d["qty"]
    if not db.deduct_points(call.from_user.id, pts):
        bot.answer_callback_query(call.id, "نقاطك غير كافية!", show_alert=True)
        return
    charge = round((qty / 1000) * float(svc["rate_per_1000"] or 0.5), 5)
    site_id = svc["site_id"] if "site_id" in svc.keys() else None
    app = db.get_app(svc["app_id"])
    app_nm = f"{app['emoji']} {app['name']}" if app and app.get("emoji") else (app['name'] if app else "")
    oid = db.create_order(call.from_user.id, svc["api_service_id"], svc["name"],
                          d["link"], qty, charge, pts, None, app_nm, site_id)
    clear_state(call.from_user.id)
    user = db.get_user(call.from_user.id)
    notify_order_channels(oid, dict(user), svc["name"], app_nm, d["link"], qty, pts)

    auto = db.get_config("auto_approve_orders", "0") == "1"
    if auto:
        db.approve_order(oid)
        threading.Thread(target=_execute_smm_order_after_approval, args=(oid,), daemon=True).start()
        edit(call,
            f"<b>✅ تم إرسال الطلب وجارٍ التنفيذ!</b>\n\n"
            f"<b></b>\n"
            f"رقم الطلب: <b>#{oid}</b>\n"
            f"القسم: {app_nm}\n"
            f"الخدمة: {svc['name']}\n"
            f"الكمية: {qty:,}\n"
            f"النقاط: {pts:,}\n"
            f"رصيدك المتبقي: {user['points']:,}\n"
            f"<b></b>\n\n"
            f"<i>سيصلك إشعار فور اكتمال الطلب</i>",
            kb.back())
    else:
        _notify_admin_approve_order(oid, dict(user), svc["name"], app_nm, d["link"], qty, pts, order_type="smm")
        edit(call,
            f"<b>⏳ تم إرسال طلبك بنجاح!</b>\n\n"
            f"<b></b>\n"
            f"رقم الطلب: <b>#{oid}</b>\n"
            f"القسم: {app_nm}\n"
            f"الخدمة: {svc['name']}\n"
            f"الكمية: {qty:,}\n"
            f"النقاط: {pts:,}\n"
            f"رصيدك المتبقي: {user['points']:,}\n"
            f"<b></b>\n\n"
            f"<i>طلبك قيد مراجعة الأدمن، سيصلك إشعار قريباً</i>",
            kb.back())


# ══════════════════════════════════════════════════════════════════
#   11. تمويل قناة / جروب
POINTS_PRICE_TABLE = (
    "💎 <b>جدول أسعار النقاط:</b>\n"
    "\n"
    "- 10,000 نقطة = <b>$1</b>\n"
    "- 20,000 نقطة = <b>$2</b>\n"
    "- 30,000 نقطة = <b>$3</b>\n"
    "- 40,000 نقطة = <b>$4</b>\n"
    "- 50,000 نقطة = <b>$5</b>\n"
    "- 100,000 نقطة = <b>$10</b>\n"
    "- 200,000 نقطة = <b>$20</b>\n"
    "- 500,000 نقطة = <b>$50</b>\n"
    "- 1,500,000 نقطة = <b>$150</b>\n"
    "\n"
    "✅ يمكنك شحن حتى <b>100M نقطة</b>"
)

# ── وسائل الشحن المتاحة (كل وسيلة لها مفتاح إعداد يحمل رقمها/بياناتها) ──
PAYMENT_METHODS = {
    "asia":     {"label": "أسيا",       "emoji": "💵", "cfg_key": "charge_asia_info"},
    "atheer":   {"label": "أثير",       "emoji": "📱", "cfg_key": "charge_atheer_info"},
    "zaincash": {"label": "زين كاش",    "emoji": "💚", "cfg_key": "charge_zaincash_info"},
    "master":   {"label": "ماستر كارد", "emoji": "💳", "cfg_key": "charge_master_info"},
}

# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "fund_start")
def cb_fund_start(call: CallbackQuery):
    rows = []
    for key, m in PAYMENT_METHODS.items():
        info = db.get_config(m["cfg_key"], "—")
        rows.append([_btn(f"{m['emoji']} {m['label']}  —  {info}", f"charge_method_{key}", color="green")])
    agent_user = db.get_config("agent_username", "ssusus").lstrip("@")
    rows.append([_btn("🧑‍💼 شحن عبر الوكيل", url=f"https://t.me/{agent_user}", color="blue")])
    rows.append([_btn("⭐ نجوم", "charge_stars", color="blue")])
    rows.append([_btn("◀️ رجوع", "back_main", color="red")])
    edit(call,
        f"<b>💳 شحن نقاط</b>\n\n"
        f"{POINTS_PRICE_TABLE}\n\n"
        f"اختر طريقة الشحن:",
        mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data.startswith("charge_method_"))
def cb_charge_method(call: CallbackQuery):
    key = call.data.replace("charge_method_", "")
    m = PAYMENT_METHODS.get(key)
    if not m:
        bot.answer_callback_query(call.id, "طريقة غير معروفة")
        return
    info = db.get_config(m["cfg_key"], "لم يتم ضبط الرقم بعد")
    set_state(call.from_user.id, "await_receipt", method=key)
    edit(call,
        f"<b>{m['emoji']} مرحباً بك في خانة الشحن {m['label']}</b>\n\n"
        f"{POINTS_PRICE_TABLE}\n\n"
        f"<b></b>\n"
        f"1️⃣ حوّل المبلغ على:\n"
        f"<b>{info}</b>\n\n"
        f"2️⃣ بعد التحويل أرسل <b>صورة الإيصال</b> هنا\n\n"
        f"<b></b>\n"
        f"<i>⚠️ الإيصالات الوهمية تؤدي لحظر الحساب</i>",
        kb.back("fund_start"))


@bot.message_handler(content_types=["photo"],
    func=lambda m: get_state(m.from_user.id).get("state") == "await_receipt")
def msg_charge_receipt(msg: Message):
    uid = msg.from_user.id
    d = get_state(uid).get("data", {})
    method_key = d.get("method", "asia")
    m = PAYMENT_METHODS.get(method_key, {"label": method_key})
    photo_id = msg.photo[-1].file_id
    rid = db.create_recharge_request(uid, method_key, photo_id)
    user = db.get_user(uid)
    clear_state(uid)

    send(msg.chat.id,
        f"<b>✅ تم استلام إيصالك!</b>\n\n"
        f"رقم الطلب: <b>#{rid}</b>\n\n"
        f"<i>سيتم مراجعته وشحن رصيدك قريباً</i>",
        kb.back("back_main"))

    # إشعار الأدمن
    caption = (
        f"<b>💵 طلب شحن جديد #{rid}</b>\n\n"
        f"المستخدم: {user['full_name']} (<code>{uid}</code>)\n"
        f"الطريقة: {m['label']}\n"
        f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    markup = mk(
        [_btn("✅ شحن النقاط", f"adm_recharge_approve_{rid}", color="green")],
        [_btn("❌ رفض الطلب",  f"adm_recharge_reject_{rid}",  color="red")],
    )
    all_admins = list(config.ADMIN_IDS) + [a["tg_id"] for a in db.get_extra_admins()]
    for aid in all_admins:
        try:
            bot.send_photo(aid, photo_id, caption=caption,
                           reply_markup=markup, parse_mode="HTML")
        except Exception as e:
            print(f"[recharge_notify] {aid}: {e}")


# ── الأدمن يختار عدد النقاط للشحن ──────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_recharge_approve_"))
def cb_adm_recharge_approve(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rid = int(call.data.split("_")[-1])
    r = db.get_recharge_request(rid)
    if not r:
        bot.answer_callback_query(call.id, "الطلب غير موجود")
        return
    if r["status"] != "pending":
        bot.answer_callback_query(call.id, "الطلب معالج مسبقاً!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return
    set_state(call.from_user.id, "adm_recharge_set_pts", rid=rid)
    user = db.get_user(r["user_id"])
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    except:
        pass
    send(call.message.chat.id,
        f"<b>💵 شحن طلب #{rid}</b>\n\n"
        f"المستخدم: {user['full_name'] if user else r['user_id']}\n"
        f"رصيده الحالي: <b>{user['points']:,}</b> نقطة\n\n"
        f"كم نقطة تريد شحنها؟\n"
        f"<i>(مثال: 100 أو 500 أو 1000)</i>")


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_recharge_reject_"))
def cb_adm_recharge_reject(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rid = int(call.data.split("_")[-1])
    r = db.reject_recharge(rid)
    if not r or r["status"] != "pending":
        bot.answer_callback_query(call.id, "الطلب معالج مسبقاً!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return
    bot.answer_callback_query(call.id, "❌ تم رفض الطلب")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.edit_message_caption(
            call.message.caption + f"\n\n<b>❌ رفضه: {call.from_user.first_name}</b>",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
    except:
        pass
    try:
        bot.send_message(r["user_id"],
            f"<b>❌ تم رفض طلب الشحن #{rid}</b>\n\n"
            f"<i>تواصل مع الدعم إذا كنت تعتقد أن هذا خطأ.</i>")
    except:
        pass

# ── قائمة الباقات المتاحة للشراء بالنجوم ──────────────────────
STARS_PACKAGES = [
    (50,   "باقة صغيرة"),
    (100,  "باقة متوسطة"),
    (250,  "باقة كبيرة"),
    (500,  "باقة ممتازة"),
    (1000, "باقة VIP"),
]


@bot.callback_query_handler(func=lambda c: c.data == "charge_stars")
def cb_charge_stars(call: CallbackQuery):
    spp = int(db.get_config("stars_per_point", "10"))
    rows = []
    for stars, label in STARS_PACKAGES:
        pts = stars * spp
        rows.append([_btn(
            f"⭐ {stars:,} نجمة  ←  {pts:,} نقطة  |  {label}",
            f"buy_stars_{stars}", color="blue"
        )])
    rows.append([_btn("◀️ رجوع", "back_main", color="red")])
    edit(call,
        f"<b>⭐ الشحن التلقائي بالنجوم</b>\n\n"
        f"<b></b>\n"
        f"نسبة التحويل: <b>1 نجمة = {spp} نقطة</b>\n"
        f"<b></b>\n\n"
        f"اختر الباقة وادفع مباشرة من تيليجرام ✅\n"
        f"<i>النقاط تُضاف فوراً بعد الدفع</i>",
        mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_stars_"))
def cb_buy_stars_package(call: CallbackQuery):
    try:
        stars = int(call.data.split("_")[-1])
    except:
        return
    spp = int(db.get_config("stars_per_point", "10"))
    pts = stars * spp
    label = next((l for s, l in STARS_PACKAGES if s == stars), f"{stars} نجمة")
    try:
        prices = [LabeledPrice(label=f"{pts:,} نقطة", amount=stars)]
        bot.send_invoice(
            chat_id=call.message.chat.id,
            title=f"⭐ {label}",
            description=f"شحن {pts:,} نقطة مقابل {stars:,} نجمة تيليجرام",
            invoice_payload=f"stars_{stars}_{call.from_user.id}",
            provider_token="",          # فارغ للنجوم
            currency="XTR",             # عملة النجوم
            prices=prices,
            start_parameter="stars_pay",
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        bot.answer_callback_query(call.id, f"خطأ: {e}", show_alert=True)


@bot.pre_checkout_query_handler(func=lambda q: True)
def pre_checkout(query):
    """الموافقة على الدفع تلقائياً"""
    bot.answer_pre_checkout_query(query.id, ok=True)


@bot.message_handler(content_types=["successful_payment"])
def successful_stars_payment(msg: Message):
    """استقبال الدفع الناجح وإضافة النقاط تلقائياً"""
    payment = msg.successful_payment
    payload = payment.invoice_payload  # "stars_{stars}_{uid}"

    if not payload.startswith("stars_"):
        return

    try:
        parts   = payload.split("_")
        stars   = int(parts[1])
        uid     = int(parts[2])
    except:
        return

    spp  = int(db.get_config("stars_per_point", "10"))
    pts  = stars * spp
    db.add_points(uid, pts)

    user = db.get_user(uid)
    send(msg.chat.id,
        f"<b>✅ تم الشحن التلقائي!</b>\n\n"
        f"<b></b>\n"
        f"النجوم المدفوعة: <b>⭐ {stars:,}</b>\n"
        f"النقاط المضافة: <b>+{pts:,} نقطة</b> 🎉\n"
        f"رصيدك الجديد: <b>{user['points']:,}</b> نقطة\n"
        f"<b></b>",
        kb.back("back_main"))

    # إشعار الأدمن
    all_admins = list(config.ADMIN_IDS) + [a["tg_id"] for a in db.get_extra_admins()]
    for aid in all_admins:
        try:
            bot.send_message(aid,
                f"<b>⭐ شحن نجوم تلقائي</b>\n\n"
                f"المستخدم: {user['full_name']} (<code>{uid}</code>)\n"
                f"النجوم: {stars:,} ⭐\n"
                f"النقاط: +{pts:,}\n"
                f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        except:
            pass


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "fund_link")
def msg_fund_link(msg: Message):
    link = (msg.text or "").strip()
    if not (link.startswith("http") or link.startswith("@") or "t.me" in link):
        send(msg.chat.id, "⚠️ الرابط غير صحيح!")
        return
    d = get_state(msg.from_user.id)["data"]
    set_state(msg.from_user.id, "fund_qty", **d, link=link)
    send(msg.chat.id,
        f"الرابط: <code>{link}</code>\n\n"
        f"<b>الخطوة 2:</b> أرسل عدد الأعضاء (من {d['svc_min']} إلى {d['svc_max']}):",
        kb.back())


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "fund_qty")
def msg_fund_qty(msg: Message):
    try:
        qty = int((msg.text or "").strip().replace(",", ""))
    except:
        send(msg.chat.id, "⚠️ أرسل رقماً!")
        return
    d = get_state(msg.from_user.id)["data"]
    mn = int(d.get("svc_min", 100))
    mx = int(d.get("svc_max", 100000))
    if qty < mn or qty > mx:
        send(msg.chat.id, f"⚠️ الكمية بين {mn:,} و {mx:,}!")
        return
    p1k = int(d.get("p1k", 10))
    pts = math.ceil(qty * p1k / 1000)
    user = db.get_user(msg.from_user.id)
    enough = user["points"] >= pts
    warn = "" if enough else f"\n\n<b>⚠️ نقاطك غير كافية!</b> ينقصك <b>{pts - user['points']:,}</b> نقطة."
    set_state(msg.from_user.id, "fund_confirm", **d, qty=qty, pts_needed=pts)
    send(msg.chat.id,
        f"<b>تأكيد الطلب</b>\n\n"
        f"<b></b>\n"
        f"الرابط: <code>{d['link']}</code>\n"
        f"الكمية: <b>{qty:,}</b> عضو\n"
        f"التكلفة: <b>{pts:,}</b> نقطة\n"
        f"رصيدك: <b>{user['points']:,}</b>\n"
        f"<b></b>{warn}",
        kb.confirm_keyboard() if enough else kb.back())


def _do_fund_order(call, d):
    pts = d["pts_needed"]
    qty = d["qty"]
    link = d["link"]
    svc_id = d["svc_id"]
    if not db.deduct_points(call.from_user.id, pts):
        bot.answer_callback_query(call.id, "نقاطك غير كافية!", show_alert=True)
        return
    rate = float(db.get_config("rate_per_1000", "0.5"))
    charge = round((qty / 1000) * rate, 5)
    svc_name = db.get_config("service_name", "تمويل")
    oid = db.create_order(call.from_user.id, svc_id, svc_name, link, qty,
                          charge, pts, None, "تمويل قناة")
    clear_state(call.from_user.id)
    user = db.get_user(call.from_user.id)
    notify_order_channels(oid, dict(user), svc_name, "تمويل قناة", link, qty, pts)

    auto = db.get_config("auto_approve_orders", "0") == "1"
    if auto:
        db.approve_order(oid)
        threading.Thread(target=_execute_smm_order_after_approval, args=(oid,), daemon=True).start()
        edit(call,
            f"<b>✅ تم إرسال الطلب وجارٍ التنفيذ!</b>\n\n"
            f"رقم الطلب: <b>#{oid}</b>\n"
            f"{qty:,} وحدة | {pts:,} نقطة\n"
            f"رصيدك: {user['points']:,}\n\n"
            f"<i>سيصلك إشعار عند الاكتمال</i>",
            kb.back())
    else:
        _notify_admin_approve_order(oid, dict(user), svc_name, "تمويل قناة", link, qty, pts, order_type="fund")
        edit(call,
            f"<b>⏳ تم إرسال طلبك!</b>\n\n"
            f"رقم الطلب: <b>#{oid}</b>\n"
            f"{qty:,} وحدة | {pts:,} نقطة\n"
            f"رصيدك: {user['points']:,}\n\n"
            f"<i>طلبك قيد مراجعة الأدمن، سيصلك إشعار قريباً</i>",
            kb.back())


# ══════════════════════════════════════════════════════════════════
#   12. لوحة الأدمن
# ══════════════════════════════════════════════════════════════════
@bot.message_handler(commands=["admin"])
def cmd_admin(msg: Message):
    if not is_admin(msg.from_user.id):
        send(msg.chat.id, "ليس لديك صلاحية.")
        return
    _show_admin(msg.chat.id)


def _show_admin(cid):
    total_u = db.get_users_count()
    total_o, today_o, rev, trev, tpts = db.get_orders_stats()
    bot.send_message(cid,
        f"<b>لوحة الأدمن — {config.BOT_NAME}</b>\n\n"
        f"<b></b>\n"
        f"المستخدمون: <b>{total_u}</b>\n"
        f"الطلبات: <b>{total_o}</b>  (اليوم: {today_o})\n"
        f"النقاط المستخدمة: <b>{tpts:,}</b>\n"
        f"الأرباح: <b>{rev:.2f}$</b>\n"
        f"<b></b>",
        reply_markup=kb.admin_main())


@bot.callback_query_handler(func=lambda c: c.data == "adm_back")
def cb_adm_back(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    clear_state(call.from_user.id)
    total_u = db.get_users_count()
    total_o, today_o, rev, trev, tpts = db.get_orders_stats()
    edit(call,
        f"<b>لوحة الأدمن</b>\n\n"
        f"المستخدمون: {total_u} | الطلبات: {total_o} (اليوم {today_o})\n"
        f"النقاط: {tpts:,} | الأرباح: {rev:.2f}$",
        kb.admin_main())


@bot.callback_query_handler(func=lambda c: c.data == "adm_close")
def cb_adm_close(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass


# ─── مواقع SMM ────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_smm_sites")
def cb_adm_smm_sites(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    sites = db.get_smm_sites()
    edit(call,
        f"<b>🌐 مواقع SMM المتعددة</b>\n\n"
        f"عدد المواقع: <b>{len(sites)}</b>\n\n"
        f"<i>يمكنك إضافة مواقع SMM مختلفة واستخدامها في الخدمات</i>",
        kb.admin_smm_sites(sites))


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_smm_site")
def cb_adm_add_smm_site(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_add_smm_site")
    edit(call,
        "<b>إضافة موقع SMM</b>\n\n"
        "أرسل بهذا الشكل:\n"
        "<code>الاسم|API_URL|API_KEY</code>\n\n"
        "أمثلة:\n"
        "<code>SMMParty|https://smmparty.com/api/v2|YOUR_KEY</code>\n"
        "<code>SMMKings|https://smmkings.com/api/v2|YOUR_KEY</code>\n"
        "<code>JustAnotherPanel|https://justanotherpanel.com/api/v2|YOUR_KEY</code>",
        kb.back("adm_smm_sites"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_smm_site_"))
def cb_adm_view_smm_site(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    site_id = int(call.data.split("_")[-1])
    site = db.get_smm_site(site_id)
    if not site:
        bot.answer_callback_query(call.id, "الموقع غير موجود")
        return
    # اختبار الرصيد
    bal = smm.get_balance(site_id)
    masked_key = site["api_key"][:6] + "****" + site["api_key"][-4:] if len(site["api_key"]) > 10 else "—"
    st = "✅ نشط" if site["is_active"] else "❌ معطّل"
    edit(call,
        f"<b>🌐 {site['name']}</b>\n\n"
        f"<b>الحالة:</b> {st}\n"
        f"<b>API URL:</b> <code>{site['api_url']}</code>\n"
        f"<b>API Key:</b> <code>{masked_key}</code>\n"
        f"<b>الرصيد:</b> <b>{bal:.2f}$</b>",
        mk(
            [_btn("✅/❌ تفعيل/تعطيل", f"adm_tog_smm_{site_id}", color="green")],
            [_btn("🗑️ حذف الموقع", f"adm_del_smm_{site_id}", color="red")],
            [_btn("◀️ رجوع", "adm_smm_sites", color="red")],
        ))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_tog_smm_"))
def cb_adm_tog_smm(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    site_id = int(call.data.split("_")[-1])
    db.toggle_smm_site(site_id)
    bot.answer_callback_query(call.id, "تم التبديل")
    call.data = f"adm_smm_site_{site_id}"
    cb_adm_view_smm_site(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_smm_"))
def cb_adm_del_smm(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    site_id = int(call.data.split("_")[-1])
    db.delete_smm_site(site_id)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_smm_sites(call)


# ─── قنوات الطلبات ────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_order_channels")
def cb_adm_order_channels(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    channels = db.get_order_channels()
    edit(call,
        f"<b>📣 قنوات الطلبات</b>\n\n"
        f"عدد: <b>{len(channels)}</b>\n\n"
        f"<i>عند تنفيذ أي طلب، تُرسل تفاصيله لهذه القنوات</i>",
        kb.admin_order_channels(channels))


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_orch")
def cb_adm_add_orch(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_add_orch")
    edit(call,
        "<b>إضافة قناة طلبات</b>\n\n"
        "أرسل بهذا الشكل:\n"
        "<code>channel_id|الاسم</code>\n\n"
        "مثال: <code>-1001234567890|قناة طلبات MCV</code>\n"
        "أو: <code>@mychannel|قناة الطلبات</code>\n\n"
        "<i>يجب أن يكون البوت أدمن في القناة وله صلاحية نشر الرسائل</i>",
        kb.back("adm_order_channels"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_orch_"))
def cb_adm_del_orch(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    ch_id = call.data.replace("adm_del_orch_", "")
    db.remove_order_channel(ch_id)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_order_channels(call)


# ─── قاعدة البيانات ──────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_database")
def cb_adm_database(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    conn = db.get_conn()
    users_c = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    orders_c = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    apps_c = conn.execute("SELECT COUNT(*) FROM apps").fetchone()[0]
    svcs_c = conn.execute("SELECT COUNT(*) FROM app_services").fetchone()[0]
    sites_c = conn.execute("SELECT COUNT(*) FROM smm_sites").fetchone()[0]
    conn.close()
    edit(call,
        f"<b>🗄️ قاعدة البيانات</b>\n\n"
        f"<b></b>\n"
        f"المستخدمون: <b>{users_c}</b>\n"
        f"الطلبات: <b>{orders_c}</b>\n"
        f"الأقسام: <b>{apps_c}</b>\n"
        f"الخدمات: <b>{svcs_c}</b>\n"
        f"مواقع SMM: <b>{sites_c}</b>\n"
        f"<b></b>\n\n"
        f"<i>يمكنك تصدير الإعدادات واستيرادها</i>",
        kb.admin_database())


@bot.callback_query_handler(func=lambda c: c.data == "adm_db_export")
def cb_adm_db_export(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        json_data = db.export_db_json()
        # إرسال كملف
        import io
        f = io.BytesIO(json_data.encode("utf-8"))
        f.name = f"mcv_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        bot.answer_callback_query(call.id, "جارٍ التصدير...")
        bot.send_document(call.message.chat.id, f,
            caption=f"<b>✅ نسخة احتياطية من قاعدة البيانات</b>\n"
                    f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    except Exception as e:
        bot.answer_callback_query(call.id, f"خطأ: {e}", show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data == "adm_db_import")
def cb_adm_db_import(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_db_import")
    edit(call,
        "<b>📥 استيراد قاعدة البيانات</b>\n\n"
        "أرسل ملف JSON الذي صدّرته سابقاً.\n\n"
        "<b>⚠️ تحذير:</b> سيتم استبدال بعض البيانات الحالية بالبيانات الجديدة.",
        kb.back("adm_database"))


@bot.callback_query_handler(func=lambda c: c.data == "adm_db_info")
def cb_adm_db_info(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cfg = db.get_all_config()
    text = "<b>إعدادات البوت الحالية:</b>\n\n"
    for row in cfg:
        k = row["key"]
        v = row["value"]
        if "key" in k.lower() and len(str(v)) > 8:
            v = str(v)[:6] + "****"
        text += f"<code>{k}</code>: {v}\n"
    # تقسيم النص إذا كان طويلاً
    if len(text) > 3500:
        text = text[:3500] + "\n..."
    edit(call, text, kb.back("adm_database"))


# ─── إدارة الأقسام والخدمات ──────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_apps")
def cb_adm_apps(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    apps = db.get_apps(only_active=False)
    edit(call,
        f"<b>إدارة الأقسام والخدمات</b>\n\nعدد الأقسام: <b>{len(apps)}</b>",
        kb.admin_apps_keyboard(apps))


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_app")
def cb_adm_add_app(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_add_app")
    edit(call,
        "<b>إضافة قسم جديد</b>\n\n"
        "أرسل: <code>الاسم|الإيموجي</code>\n\n"
        "مثال: <code>تيك توك|📱</code>\n"
        "أو: <code>انستجرام|📸</code>",
        kb.back("adm_apps"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_app_") and not c.data.startswith("adm_app_s"))
def cb_adm_view_app(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        app_id = int(call.data.split("_")[-1])
    except:
        return
    app = db.get_app(app_id)
    if not app:
        bot.answer_callback_query(call.id, "القسم غير موجود")
        return
    services = db.get_app_services(app_id, only_active=False)
    nm = f"{app['emoji']} {app['name']}" if app.get("emoji") else app['name']
    edit(call,
        f"<b>{nm}</b>\n\nعدد الخدمات: <b>{len(services)}</b>",
        kb.admin_app_view(app_id, services))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_app_"))
def cb_adm_del_app(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        db.delete_app(int(call.data.split("_")[-1]))
        bot.answer_callback_query(call.id, "تم الحذف")
        cb_adm_apps(call)
    except Exception as e:
        bot.answer_callback_query(call.id, f"خطأ: {e}")


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_add_svc_"))
def cb_adm_add_svc(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        app_id = int(call.data.split("_")[-1])
    except:
        return
    sites = db.get_smm_sites(only_active=True)
    sites_txt = "\n".join(f"  • ID={s['id']}: {s['name']}" for s in sites) or "  لا توجد مواقع مفعّلة"
    set_state(call.from_user.id, "adm_add_svc", app_id=app_id)
    edit(call,
        "<b>إضافة خدمة جديدة</b>\n\n"
        "المواقع المتاحة:\n" + sites_txt + "\n\n"
        "أرسل: <code>SERVICE_ID|نقاط_لكل_1000|SITE_ID</code>\n\n"
        "مثال: <code>1234|50|1</code>\n"
        "أو مع اسم مخصص: <code>1234|50|1|اسم_مخصص</code>\n\n"
        "<i>سيجلب البوت البيانات تلقائياً من الموقع المحدد</i>",
        kb.back(f"adm_app_{app_id}"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_svc_"))
def cb_adm_view_svc(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        sid = int(call.data.split("_")[-1])
    except:
        return
    svc = db.get_service(sid)
    if not svc:
        bot.answer_callback_query(call.id, "غير موجودة")
        return
    nm = f"{svc['emoji']} {svc['name']}" if svc.get("emoji") else svc['name']
    site_id = svc["site_id"] if "site_id" in svc.keys() else None
    site_name = "—"
    if site_id:
        site = db.get_smm_site(site_id)
        if site:
            site_name = site["name"]
    edit(call,
        f"<b>{nm}</b>\n\n"
        f"API ID: <code>{svc['api_service_id']}</code>\n"
        f"الموقع: {site_name}\n"
        f"السعر لكل 1000: <b>{svc['points_per_1000']:,}</b> نقطة\n"
        f"الحدود: {svc['min_qty']:,} — {svc['max_qty']:,}\n"
        f"سعر الموقع: {svc['rate_per_1000']}$/1000",
        kb.admin_svc_view(sid, svc["app_id"]))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_edit_app_"))
def cb_adm_edit_app(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        app_id = int(call.data.split("_")[-1])
    except:
        return
    set_state(call.from_user.id, "adm_edit_app", app_id=app_id)
    edit(call,
         "<b>تعديل اسم القسم</b>\n\nأرسل الاسم الجديد للقسم:",
         kb.back(f"adm_app_{app_id}"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_edit_svc_"))
def cb_adm_edit_svc(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        sid = int(call.data.split("_")[-1])
    except:
        return
    svc = db.get_service(sid)
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة")
        return
    set_state(call.from_user.id, "adm_edit_svc", svc_id=sid, app_id=svc["app_id"])
    edit(call,
         "<b>تعديل اسم الخدمة</b>\n\nأرسل الاسم الجديد للخدمة:",
         kb.back(f"adm_svc_{sid}"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_edit_svc_apiid_"))
def cb_adm_edit_svc_apiid(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    sid = int(call.data.split("_")[-1])
    svc = db.get_service(sid)
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة")
        return
    set_state(call.from_user.id, "adm_edit_svc_apiid", svc_id=sid, app_id=svc["app_id"])
    edit(call,
         f"<b>🔧 تعديل Service ID</b>\n\n"
         f"القيمة الحالية: <code>{svc['api_service_id']}</code>\n\n"
         f"أرسل الـ Service ID الجديد:",
         kb.back(f"adm_svc_{sid}"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_edit_svc_siteid_"))
def cb_adm_edit_svc_siteid(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    sid = int(call.data.split("_")[-1])
    svc = db.get_service(sid)
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة")
        return
    sites = db.get_smm_sites(only_active=False)
    current = svc["site_id"] if "site_id" in svc.keys() else None
    rows = []
    for s in sites:
        mark = " ✅" if s["id"] == current else ""
        rows.append([_btn(f"🌐 {s['name']}{mark}", f"adm_set_svc_site_{sid}_{s['id']}", color="blue")])
    rows.append([_btn("❌ بدون موقع", f"adm_set_svc_site_{sid}_0", color="red")])
    rows.append([_btn("◀️ رجوع", f"adm_svc_{sid}", color="red")])
    edit(call,
         f"<b>🌐 اختر الموقع للخدمة</b>\n\n"
         f"الموقع الحالي: <code>{current or 'افتراضي'}</code>",
         mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_set_svc_site_"))
def cb_adm_set_svc_site(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    sid = int(parts[-2])
    site_val = int(parts[-1])
    new_site = None if site_val == 0 else site_val
    db.update_service(sid, site_id=new_site)
    svc = db.get_service(sid)
    lbl = str(new_site) if new_site else "افتراضي"
    bot.answer_callback_query(call.id, f"✅ تم تغيير الموقع إلى: {lbl}")
    call.data = f"adm_svc_{sid}"
    cb_adm_view_svc(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_edit_free_apiid_"))
def cb_adm_edit_free_apiid(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    sid = int(call.data.split("_")[-1])
    svc = db.get_free_service(sid)
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة")
        return
    set_state(call.from_user.id, "adm_edit_free_apiid", svc_id=sid)
    edit(call,
         f"<b>🔧 تعديل Service ID — مجانية</b>\n\n"
         f"القيمة الحالية: <code>{svc['api_service_id']}</code>\n\n"
         f"أرسل الـ Service ID الجديد:",
         kb.back(f"adm_free_svc_{sid}"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_edit_free_siteid_"))
def cb_adm_edit_free_siteid(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    sid = int(call.data.split("_")[-1])
    svc = db.get_free_service(sid)
    if not svc:
        bot.answer_callback_query(call.id, "الخدمة غير موجودة")
        return
    sites = db.get_smm_sites(only_active=False)
    current = svc["site_id"] if "site_id" in svc.keys() else None
    rows = []
    for s in sites:
        mark = " ✅" if s["id"] == current else ""
        rows.append([_btn(f"🌐 {s['name']}{mark}", f"adm_set_free_site_{sid}_{s['id']}", color="blue")])
    rows.append([_btn("❌ بدون موقع", f"adm_set_free_site_{sid}_0", color="red")])
    rows.append([_btn("◀️ رجوع", f"adm_free_svc_{sid}", color="red")])
    edit(call,
         f"<b>🌐 اختر الموقع للخدمة المجانية</b>\n\n"
         f"الموقع الحالي: <code>{current or 'افتراضي'}</code>",
         mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_set_free_site_"))
def cb_adm_set_free_site(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    sid = int(parts[-2])
    site_val = int(parts[-1])
    new_site = None if site_val == 0 else site_val
    db.update_free_service(sid, site_id=new_site)
    lbl = str(new_site) if new_site else "افتراضي"
    bot.answer_callback_query(call.id, f"✅ تم تغيير الموقع إلى: {lbl}")
    call.data = f"adm_free_svc_{sid}"
    cb_adm_view_free(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_svc_"))
def cb_adm_del_svc(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        sid = int(call.data.split("_")[-1])
    except:
        return
    svc = db.get_service(sid)
    app_id = svc["app_id"] if svc else None
    db.delete_service(sid)
    bot.answer_callback_query(call.id, "تم الحذف")
    if app_id:
        call.data = f"adm_app_{app_id}"
        cb_adm_view_app(call)
    else:
        cb_adm_apps(call)


# ─── الإحصائيات ──────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_stats")
def cb_adm_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    total_u = db.get_users_count()
    total_o, today_o, rev, trev, tpts = db.get_orders_stats()
    ref_c = db.get_referral_log_count()
    sites = db.get_smm_sites(only_active=True)
    balances_txt = ""
    for s in sites:
        bal = smm.get_balance(s["id"])
        balances_txt += f"\n  {s['name']}: <b>{bal:.2f}$</b>"
    edit(call,
        f"<b>الإحصائيات</b>\n\n"
        f"<b></b>\n"
        f"المستخدمون: <b>{total_u}</b>\n"
        f"الطلبات: <b>{total_o}</b>  (اليوم: {today_o})\n"
        f"نقاط مستخدمة: <b>{tpts:,}</b>\n"
        f"الأرباح: <b>{rev:.2f}$</b>  (اليوم: {trev:.2f}$)\n"
        f"الدعوات: <b>{ref_c}</b>\n"
        f"<b></b>\n"
        f"أرصدة المواقع:{balances_txt if balances_txt else ' لا توجد مواقع'}\n"
        f"<b></b>",
        kb.back("adm_back"))


# ─── المستخدمون ──────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_users")
def cb_adm_users(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    edit(call, f"<b>إدارة المستخدمين</b>\n\nالإجمالي: <b>{db.get_users_count()}</b>",
         kb.admin_users_kb())


@bot.callback_query_handler(func=lambda c: c.data == "adm_search_user")
def cb_adm_search(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_search_user")
    edit(call, "أرسل ID المستخدم:", kb.back("adm_users"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_ban_") or c.data.startswith("adm_unban_"))
def cb_adm_ban(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    action = parts[1]
    uid = int(parts[2])
    db.update_user(uid, is_banned=1 if action == "ban" else 0)
    bot.answer_callback_query(call.id, "تم")


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_add_pts_") or c.data.startswith("adm_sub_pts_"))
def cb_adm_pts_action(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    action = parts[1]  # add or sub
    uid = int(parts[3])
    set_state(call.from_user.id, f"adm_{action}_points", target_id=uid)
    edit(call, f"أرسل عدد النقاط ({'إضافة' if action == 'add' else 'خصم'}) للمستخدم <code>{uid}</code>:",
         kb.back("adm_back"))


# ─── إذاعة ───────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_broadcast")
def cb_adm_broadcast(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_broadcast")
    edit(call,
        "<b>إذاعة جماعية</b>\n\n"
        "الإذاعة ستُرسل لجميع المستخدمين النشطين.\n\n"
        "أرسل الرسالة الآن (نص/صورة/فيديو):",
        kb.back("adm_back"))


# ─── شحن نقاط ────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_topup")
def cb_adm_topup(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_topup_id")
    edit(call, "أرسل ID المستخدم:", kb.back("adm_back"))


# ─── قنوات إجبارية ───────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_mandatory")
def cb_adm_mandatory(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    channels = db.get_mandatory_channels()
    txt = f"<b>قنوات الاشتراك الإجباري</b>\n\nعدد: <b>{len(channels)}</b>\n"
    rows = []
    for ch in channels:
        t = ch.get("target_members", 0)
        cm = ch.get("current_members", 0)
        lbl = ch['channel_name']
        if t > 0:
            lbl += f"  ({cm}/{t})"
        rows.append([_btn(f"🗑️ حذف  {lbl}", f"adm_del_mand_{ch['channel_id']}", color="red")])
    rows.append([_btn("➕ إضافة قناة", "adm_add_mand", color="green")])
    rows.append([_btn("◀️ رجوع", "adm_back")])
    edit(call, txt, mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_mand")
def cb_adm_add_mand(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_mand_step1")
    edit(call,
        "<b>إضافة قناة إجبارية — الخطوة 1/4</b>\n\n"
        "أرسل معرف القناة:\n"
        "مثال: <code>@mychannel</code> أو <code>-1001234567890</code>\n\n"
        "<i>يجب أن يكون البوت أدمن في القناة</i>",
        kb.back("adm_mandatory"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_mand_"))
def cb_adm_del_mand(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    ch_id = call.data.replace("adm_del_mand_", "")
    db.remove_mandatory_channel(ch_id)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_mandatory(call)


# ─── قنوات النقاط ────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_points_ch")
def cb_adm_pts_ch(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    channels = db.get_points_channels()
    rows = []
    for ch in channels:
        rows.append([_btn(f"🗑️ حذف  {ch['channel_name']} (+{ch['points_reward']})",
                          f"adm_del_ptch_{ch['channel_id']}")])
    rows.append([_btn("➕ إضافة قناة نقاط", "adm_add_ptch", color="green")])
    rows.append([_btn("◀️ رجوع", "adm_back")])
    edit(call, f"<b>قنوات النقاط</b>\n\nعدد: <b>{len(channels)}</b>", mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_ptch")
def cb_adm_add_ptch(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_add_ptch")
    edit(call,
        "<b>إضافة قناة نقاط</b>\n\n"
        "<code>channel_id|الاسم|https://t.me/channel|النقاط</code>\n\n"
        "مثال: <code>@mychannel|قناتي|https://t.me/mychannel|50</code>",
        kb.back("adm_points_ch"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_ptch_"))
def cb_adm_del_ptch(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    ch_id = call.data.replace("adm_del_ptch_", "")
    db.remove_points_channel(ch_id)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_pts_ch(call)


# ─── إعدادات الخدمة ──────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_service_cfg")
def cb_adm_service_cfg(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rows = [
        [_btn("🔧 تغيير Service ID", "adm_set_svc_id")],
        [_btn("💎 السعر لكل 1000 (نقاط)", "adm_set_p1k")],
        [_btn("📉 الحد الأدنى للكمية", "adm_set_svc_min")],
        [_btn("📈 الحد الأقصى للكمية", "adm_set_svc_max")],
        [_btn("◀️ رجوع", "adm_back")],
    ]
    edit(call,
        f"<b>إعدادات خدمة التمويل</b>\n\n"
        f"Service ID: <code>{db.get_config('service_id', '—')}</code>\n"
        f"السعر/1000: <b>{db.get_config('points_per_1000', '10')}</b> نقطة\n"
        f"الحد الأدنى: {db.get_config('service_min', '100')}\n"
        f"الحد الأقصى: {db.get_config('service_max', '100000')}",
        mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data == "adm_menu_labels")
def cb_adm_menu_labels(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rows = [
        [_btn("🎯 الخدمات", "adm_set_menu_services")],
        [_btn("💳 شحن نقاط", "adm_set_menu_fund")],
        [_btn("🎁 تجميع نقاط", "adm_set_menu_collect")],
        [_btn("📊 الحساب", "adm_set_menu_account")],
        [_btn("🔑 استخدام كود", "adm_set_menu_use_code")],
        [_btn("🌐 تحويل نقاط", "adm_set_menu_transfer")],
        [_btn("🔎 متابعه طلب", "adm_set_menu_track_order")],
        [_btn("📦 طلباتي", "adm_set_menu_my_orders")],
        [_btn("🔄 اكتمال الطلبات", "adm_set_menu_updates")],
        [_btn("🛍️ ⭐ نجوم 🚀 جوائز 🛍 رصيد أرقام", "adm_set_menu_store")],
        [_btn("📜 شروط الاستخدام", "adm_set_menu_terms")],
        [_btn("◀️ رجوع", "adm_bot_settings", color="red")],
    ]
    edit(call,
        "<b>تعديل عناوين القائمة الرئيسية</b>\n\n" \
        "اضغط على الزر لتغيير النص.",
        mk(*rows))


# ─── إعدادات النقاط ──────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_pts_settings")
def cb_adm_pts_settings(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rows = [
        [_btn("🌅 نقاط الهدية اليومية", "adm_set_daily_pts")],
        [_btn("🗓️ نقاط الهدية الأسبوعية", "adm_set_weekly_pts")],
        [_btn("🔗 نقاط الدعوة", "adm_set_ref_pts")],
        [_btn("👋 نقاط الترحيب", "adm_set_welcome_pts")],
        [_btn("⏱️ ساعات الانتظار للعجلة", "adm_set_wheel_hrs")],
        [_btn("🔒 حد الخدمات المجانية يومياً", "adm_set_free_limit")],
        [_btn("💳 معلومات شحن النقاط", "adm_set_points_charge_info")],
        [_btn("◀️ رجوع", "adm_back")],
    ]
    edit(call,
        f"<b>إعدادات النقاط</b>\n\n"
        f"الهدية اليومية: <b>{db.get_config('daily_gift_points', '5')}</b>\n"
        f"الهدية الأسبوعية: <b>{db.get_config('weekly_gift_points', '50')}</b>\n"
        f"نقاط الدعوة: <b>{db.get_config('referral_points', '50')}</b>\n"
        f"نقاط الترحيب: <b>{db.get_config('welcome_points', '10')}</b>\n"
        f"انتظار العجلة: <b>{db.get_config('wheel_cooldown_hrs', '6')}</b> ساعة\n"
        f"حد الخدمات المجانية يومياً: <b>{db.get_config('free_services_daily_limit', '3')}</b> مرة\n"
        f"معلومات شحن النقاط: {db.get_config('points_charge_info', 'لشحن النقاط تواصل مع الدعم')}",
        mk(*rows))


# ─── إعدادات البوت ───────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_bot_settings")
def cb_adm_bot_settings(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rows = [
        [_btn("📡 قناة التحديثات", "adm_set_updates_ch"),
         _btn("🛟 يوزر الدعم", "adm_set_support")],
        [_btn("⚡ إيقاف/تشغيل البوت", "adm_toggle_bot")],
        [_btn("💵 رقم أسيا", "adm_set_charge_asia"),
         _btn("📱 رقم أثير", "adm_set_charge_atheer")],
        [_btn("💚 رقم زين كاش", "adm_set_charge_zaincash"),
         _btn("💳 رقم ماستر", "adm_set_charge_master")],
        [_btn("🧑‍💼 يوزر الوكيل", "adm_set_agent_username"),
         _btn("⭐ نسبة النجوم", "adm_set_stars_per_point")],
        [_btn("✏️ تعديل أسماء القائمة", "adm_menu_labels", color="blue")],
        [_btn("📜 تعديل شروط الاستخدام", "adm_set_terms", color="red")],
        [_btn(
            f"🤖 التنفيذ: {'تلقائي ✅' if db.get_config('auto_approve_orders','0')=='1' else 'يدوي ⏳'}",
            "adm_toggle_auto_approve",
            color="green" if db.get_config("auto_approve_orders","0")=="1" else "red"
        )],
        [_btn("◀️ رجوع", "adm_back")],
    ]
    edit(call,
        f"<b>إعدادات البوت</b>\n\n"
        f"الحالة: {'✅ فعّال' if db.get_config('bot_active', '1') == '1' else '❌ متوقف'}\n"
        f"أسيا: {db.get_config('charge_asia_info', '—')}\n"
        f"أثير: {db.get_config('charge_atheer_info', '—')}\n"
        f"زين كاش: {db.get_config('charge_zaincash_info', '—')}\n"
        f"ماستر: {db.get_config('charge_master_info', '—')}\n"
        f"الوكيل: @{db.get_config('agent_username', 'ssusus')}\n"
        f"نجوم: {db.get_config('charge_stars_info', 'نجوم: تواصل مع @ssusus')}\n",
        mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data == "adm_toggle_bot")
def cb_toggle_bot(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cur = db.get_config("bot_active", "1")
    db.set_config("bot_active", "0" if cur == "1" else "1")
    bot.answer_callback_query(call.id, f"البوت {'متوقف' if cur == '1' else 'فعّال'} الآن")
    cb_adm_bot_settings(call)


@bot.callback_query_handler(func=lambda c: c.data == "adm_toggle_auto_approve")
def cb_toggle_auto_approve(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cur = db.get_config("auto_approve_orders", "0")
    new = "1" if cur == "0" else "0"
    db.set_config("auto_approve_orders", new)
    status = "تلقائي ✅" if new == "1" else "يدوي ⏳"
    bot.answer_callback_query(call.id, f"وضع التنفيذ: {status}", show_alert=True)
    cb_adm_bot_settings(call)


@bot.callback_query_handler(func=lambda c: c.data == "adm_set_terms")
def cb_adm_set_terms(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_set_terms")
    edit(call,
        "<b>📜 تعديل شروط الاستخدام والأحكام</b>\n\n"
        "أرسل نص شروط الاستخدام الجديد (يدعم HTML):",
        kb.back("adm_bot_settings"))


# ─── عجلة الحظ (أدمن) ────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_wheel")
def cb_adm_wheel(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    prizes = db.get_wheel_prizes(only_active=False)
    total_w = sum(float(p["weight"]) for p in prizes if p["is_active"])
    txt = (f"<b>إدارة عجلة الحظ</b>\n\n"
           f"عدد الجوائز: <b>{len(prizes)}</b>  |  "
           f"مجموع الأوزان: <b>{total_w:g}</b>\n\n"
           f"<b></b>\n")
    for p in prizes:
        st = "✅" if p["is_active"] else "❌"
        ch = (float(p["weight"]) / total_w * 100) if (p["is_active"] and total_w) else 0
        lbl = p.get("label") or ""
        em = p.get("emoji") or ""
        txt += f"  {st} {em} {p['points']} نقطة {lbl}  —  {ch:.1f}%\n"
    edit(call, txt, kb.admin_wheel(prizes))


@bot.callback_query_handler(func=lambda c: c.data == "adm_wheel_add")
def cb_adm_wheel_add(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_wheel_add")
    edit(call,
        "<b>إضافة جائزة للعجلة</b>\n\n"
        "<code>النقاط|الوزن|الإيموجي|التسمية</code>\n\n"
        "مثال: <code>100|5|🔵|جائزة رائعة</code>\n\n"
        "<i>الوزن = الاحتمالية. جوائز أكبر = وزن أقل.</i>",
        kb.back("adm_wheel"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_wheel_tog_"))
def cb_wheel_toggle(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    db.toggle_wheel_prize(int(call.data.split("_")[-1]))
    bot.answer_callback_query(call.id, "تم التبديل")
    cb_adm_wheel(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_wheel_del_"))
def cb_wheel_del(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    db.delete_wheel_prize(int(call.data.split("_")[-1]))
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_wheel(call)


# ─── الخدمات المجانية (أدمن) ─────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_free_svcs")
def cb_adm_free_svcs(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    svcs = db.get_free_services(only_active=False)
    edit(call, f"<b>الخدمات المجانية</b>\n\nعدد: <b>{len(svcs)}</b>", kb.admin_free_svcs(svcs))


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_free_svc")
def cb_adm_add_free_svc(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    sites = db.get_smm_sites(only_active=True)
    sites_txt = "\n".join(f"  • ID={s['id']}: {s['name']}" for s in sites) or "  لا توجد مواقع"
    set_state(call.from_user.id, "adm_add_free_svc")
    edit(call,
        "<b>إضافة خدمة مجانية</b>\n\n"
        "المواقع:\n" + sites_txt + "\n\n"
        "أرسل:\n<code>الاسم|SERVICE_ID|حد_يومي|حد_أدنى|حد_أقصى|SITE_ID|الوصف</code>\n\n"
        "مثال: <code>متابعين مجانية|1234|3|100|500|1|خدمة مجانية</code>",
        kb.back("adm_free_svcs"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_free_svc_"))
def cb_adm_view_free(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    try:
        sid = int(call.data.split("_")[-1])
    except:
        return
    svc = db.get_free_service(sid)
    if not svc:
        bot.answer_callback_query(call.id, "غير موجودة")
        return
    edit(call,
        f"<b>{svc['name']}</b>\n\n"
        f"API ID: <code>{svc['api_service_id']}</code>\n"

        f"الحدود: {svc['min_qty']:,} — {svc['max_qty']:,}\n"
        f"الوصف: {svc['description'] or '—'}",
        kb.admin_free_svc_view(sid))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_free_"))
def cb_adm_del_free(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    db.delete_free_service(int(call.data.split("_")[-1]))
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_free_svcs(call)


# ─── أكواد الدعوة ────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_invite_links")
def cb_adm_invites(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    links = db.get_invites()
    edit(call, f"<b>أكواد الدعوة</b>\n\nعدد: <b>{len(links)}</b>", kb.admin_invite_links(links))


@bot.callback_query_handler(func=lambda c: c.data == "adm_create_invite")
def cb_adm_create_invite(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_create_invite")
    edit(call,
        "<b>إنشاء كود دعوة</b>\n\n"
        "<code>الكود|النقاط|الحد_الأقصى</code>\n\n"
        "مثال: <code>SPECIAL2024|100|50</code>\n"
        "<i>الحد = 0 يعني بلا حد</i>",
        kb.back("adm_invite_links"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_invite_"))
def cb_adm_del_invite(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    code = call.data.replace("adm_del_invite_", "")
    db.delete_invite(code)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_invites(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_view_invite_"))
def cb_adm_view_invite(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    code = call.data.replace("adm_view_invite_", "")
    conn = db.get_conn()
    lnk = conn.execute("SELECT * FROM invite_links WHERE code=?", (code,)).fetchone()
    conn.close()
    if not lnk:
        bot.answer_callback_query(call.id, "الكود غير موجود")
        return
    bu = config.BOT_USERNAME.lstrip("@")
    url = f"https://t.me/{bu}?start=invite_{code}"
    uses = "∞" if lnk["max_uses"] == 0 else f"{lnk['current_uses']}/{lnk['max_uses']}"
    st = "✅ نشط" if lnk["is_active"] else "❌ متوقف"
    edit(call,
        f"<b>🎁 كود: {code}</b>\n\n"
        f"<b></b>\n"
        f"النقاط: <b>{lnk['points_reward']:,}</b> نقطة\n"
        f"الاستخدامات: <b>{uses}</b>\n"
        f"الحالة: {st}\n"
        f"<b></b>\n\n"
        f"🔗 رابط الهدية الجاهز:\n<code>{url}</code>",
        mk(
            [_btn("🗑️ حذف الكود", f"adm_del_invite_{code}", color="red")],
            [_btn("◀️ رجوع",       "adm_invite_links",        color="red")],
        ))


# ─── إدارة الأدمنية ──────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_admins")
def cb_adm_admins(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    admins = db.get_extra_admins()
    main_ids = ", ".join(str(i) for i in config.ADMIN_IDS)
    edit(call,
        f"<b>إدارة الأدمنية</b>\n\n"
        f"الأدمن الرئيسيون: <code>{main_ids}</code>\n"
        f"أدمنية إضافية: <b>{len(admins)}</b>",
        kb.admin_admins_kb(admins))


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_admin")
def cb_adm_add_admin(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_add_admin")
    edit(call, "أرسل ID المستخدم المراد رفعه أدمن:", kb.back("adm_admins"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_rem_admin_"))
def cb_rem_admin(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    uid = int(call.data.split("_")[-1])
    if uid in config.ADMIN_IDS:
        bot.answer_callback_query(call.id, "لا يمكن إزالة الأدمن الرئيسي!", show_alert=True)
        return
    db.remove_extra_admin(uid)
    bot.answer_callback_query(call.id, "تم الإزالة")
    cb_adm_admins(call)


# ── مُعالجات الإعدادات بالزر ──────────────────────────────────
_cfg_btn_map = {
    "adm_set_updates_ch":  ("updates_channel",      "adm_bot_settings"),
    "adm_set_support":     ("support_username",     "adm_bot_settings"),
    "adm_set_points_charge_info": ("points_charge_info", "adm_pts_settings"),
    "adm_set_charge_asia":        ("charge_asia_info", "adm_bot_settings"),
    "adm_set_charge_atheer":      ("charge_atheer_info", "adm_bot_settings"),
    "adm_set_charge_zaincash":    ("charge_zaincash_info", "adm_bot_settings"),
    "adm_set_charge_master":      ("charge_master_info", "adm_bot_settings"),
    "adm_set_agent_username":     ("agent_username", "adm_bot_settings"),
    "adm_set_charge_vodafone":    ("charge_vodafone_info", "adm_pts_settings"),
    "adm_set_charge_stars":       ("charge_stars_info", "adm_pts_settings"),
    "adm_set_stars_per_point":    ("stars_per_point",   "adm_bot_settings"),
    "adm_set_daily_pts":   ("daily_gift_points",    "adm_pts_settings"),
    "adm_set_weekly_pts":  ("weekly_gift_points",   "adm_pts_settings"),
    "adm_set_ref_pts":     ("referral_points",      "adm_pts_settings"),
    "adm_set_welcome_pts": ("welcome_points",       "adm_pts_settings"),
    "adm_set_wheel_hrs":   ("wheel_cooldown_hrs",   "adm_pts_settings"),
    "adm_set_free_limit":  ("free_services_daily_limit", "adm_pts_settings"),
    "adm_set_svc_id":      ("service_id",           "adm_service_cfg"),
    "adm_set_p1k":         ("points_per_1000",      "adm_service_cfg"),
    "adm_set_svc_min":     ("service_min",          "adm_service_cfg"),
    "adm_set_svc_max":     ("service_max",          "adm_service_cfg"),
    "adm_set_menu_services": ("menu_services_label", "adm_menu_labels"),
    "adm_set_menu_fund":     ("menu_fund_label", "adm_menu_labels"),
    "adm_set_menu_collect":  ("menu_collect_points_label", "adm_menu_labels"),
    "adm_set_menu_account":  ("menu_account_label", "adm_menu_labels"),
    "adm_set_menu_use_code": ("menu_use_code_label", "adm_menu_labels"),
    "adm_set_menu_transfer": ("menu_transfer_label", "adm_menu_labels"),
    "adm_set_menu_track_order": ("menu_track_order_label", "adm_menu_labels"),
    "adm_set_menu_my_orders": ("menu_my_orders_label", "adm_menu_labels"),
    "adm_set_menu_channels": ("menu_channels_label", "adm_menu_labels"),
    "adm_set_menu_updates":  ("menu_updates_label", "adm_menu_labels"),
    "adm_set_menu_store":    ("menu_store_label", "adm_menu_labels"),
    "adm_set_menu_terms":    ("menu_terms_label", "adm_menu_labels"),
}
_cfg_labels = {
    "adm_set_updates_ch":  "رابط قناة التحديثات",
    "adm_set_support":     "يوزر الدعم",
    "adm_set_points_charge_info": "معلومات شحن النقاط",
    "adm_set_charge_asia":     "رقم/بيانات أسيا",
    "adm_set_charge_atheer":   "رقم/بيانات أثير",
    "adm_set_charge_zaincash": "رقم/بيانات زين كاش",
    "adm_set_charge_master":   "رقم/بيانات ماستر كارد",
    "adm_set_agent_username":  "يوزر الوكيل (بدون @)",
    "adm_set_charge_vodafone": "بيانات اسيا",
    "adm_set_charge_stars":    "بيانات النجوم",
    "adm_set_stars_per_point": "نقاط لكل نجمة (مثال: 10)",
    "adm_set_daily_pts":   "نقاط الهدية اليومية",
    "adm_set_weekly_pts":  "نقاط الهدية الأسبوعية",
    "adm_set_ref_pts":     "نقاط الدعوة",
    "adm_set_welcome_pts": "نقاط الترحيب",
    "adm_set_wheel_hrs":   "ساعات انتظار العجلة",
    "adm_set_free_limit":  "حد الخدمات المجانية يومياً",
    "adm_set_svc_id":      "Service ID",
    "adm_set_p1k":         "السعر لكل 1000 (نقاط)",
    "adm_set_svc_min":     "الحد الأدنى للكمية",
    "adm_set_svc_max":     "الحد الأقصى للكمية",
    "adm_set_menu_services": "عنوان زر الخدمات",
    "adm_set_menu_fund":     "عنوان زر شحن نقاط",
    "adm_set_menu_collect":  "عنوان زر تجميع نقاط",
    "adm_set_menu_account":  "عنوان زر الحساب",
    "adm_set_menu_use_code": "عنوان زر استخدام كود",
    "adm_set_menu_transfer": "عنوان زر تحويل نقاط",
    "adm_set_menu_track_order": "عنوان زر فحص طلب",
    "adm_set_menu_my_orders": "عنوان زر طلباتي",
    "adm_set_menu_updates":  "عنوان زر اكتمال الطلبات",
    "adm_set_menu_store":    "عنوان زر ⭐ نجوم 🚀 جوائز 🛍 رصيد أرقام",
    "adm_set_menu_terms":    "عنوان زر شروط الاستخدام",
}


def _make_cfg_handler(ev):
    @bot.callback_query_handler(func=lambda c, e=ev: c.data == e)
    def _h(call: CallbackQuery, _ev=ev):
        if not is_admin(call.from_user.id):
            return
        set_state(call.from_user.id, _ev)
        lbl = _cfg_labels.get(_ev, "الإعداد")
        edit(call, f"أرسل القيمة الجديدة لـ <b>{lbl}</b>:", kb.back("adm_back"))


for _ev in _cfg_btn_map:
    _make_cfg_handler(_ev)


# ══════════════════════════════════════════════════════════════════
#   13. معالج الرسائل النصية (Router)
# ══════════════════════════════════════════════════════════════════
@bot.message_handler(func=lambda m: True, content_types=["text", "photo", "video", "document"])
def msg_router(msg: Message):
    uid = msg.from_user.id
    state = get_state(uid)
    s = state.get("state")
    d = state.get("data", {})

    if config.TRACK_MESSAGES and not is_admin(uid):
        # Forward message to admins for tracking
        for admin_id in config.ADMIN_IDS:
            try:
                if msg.content_type == "text":
                    bot.send_message(
                        admin_id, 
                        f"📩 من المستخدم: {msg.from_user.first_name or 'غير معروف'} (@{msg.from_user.username or 'لا يوجد'}) - ID: {uid}\n\n{msg.text}"
                    )
                else:
                    bot.copy_message(
                        admin_id, 
                        msg.chat.id, 
                        msg.message_id, 
                        caption=f"📩 من المستخدم: {msg.from_user.first_name or 'غير معروف'} (@{msg.from_user.username or 'لا يوجد'}) - ID: {uid}"
                    )
            except Exception:
                pass  # Ignore forwarding errors

    # ─── المستخدم: كود دعوة ──────────────────────────────────
    if s == "waiting_invite_code":
        code = (msg.text or "").strip().upper()
        ok, pts, err = db.claim_invite(uid, code)
        if ok:
            send(msg.chat.id, f"<b>✅ تم تفعيل الكود!</b>\n\nحصلت على <b>{pts}</b> نقطة!", kb.back())
        else:
            send(msg.chat.id, f"<b>❌ خطأ:</b> {err}", kb.back())
        clear_state(uid)
        return

    if not is_admin(uid):
        return

    # ═══════════════ الأدمن ══════════════════════════════════

    if s == "adm_edit_app":
        try:
            app_id = d.get("app_id")
            new_name = (msg.text or "").strip()
            if not new_name:
                raise ValueError("الاسم فارغ")
            db.update_app(app_id, name=new_name)
            send(msg.chat.id,
                 f"✅ تم تحديث اسم القسم إلى: {new_name}",
                 kb.admin_app_view(app_id, db.get_app_services(app_id, only_active=False)))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}")
        clear_state(uid)
        return

    if s == "adm_edit_svc":
        try:
            sid = d.get("svc_id")
            new_name = (msg.text or "").strip()
            if not new_name:
                raise ValueError("الاسم فارغ")
            db.update_service(sid, name=new_name)
            svc = db.get_service(sid)
            send(msg.chat.id,
                 f"✅ تم تحديث اسم الخدمة إلى: {new_name}",
                 kb.admin_svc_view(sid, svc["app_id"]))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}")
        clear_state(uid)
        return

    if s == "adm_edit_svc_apiid":
        try:
            sid = d.get("svc_id")
            new_val = (msg.text or "").strip()
            if not new_val:
                raise ValueError("القيمة فارغة")
            db.update_service(sid, api_service_id=new_val)
            svc = db.get_service(sid)
            send(msg.chat.id,
                 f"✅ تم تحديث Service ID إلى: <code>{new_val}</code>",
                 kb.admin_svc_view(sid, svc["app_id"]))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}")
        clear_state(uid)
        return

    if s == "adm_edit_free_apiid":
        try:
            sid = d.get("svc_id")
            new_val = (msg.text or "").strip()
            if not new_val:
                raise ValueError("القيمة فارغة")
            db.update_free_service(sid, api_service_id=new_val)
            send(msg.chat.id,
                 f"✅ تم تحديث Service ID إلى: <code>{new_val}</code>",
                 kb.admin_free_svc_view(sid))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}")
        clear_state(uid)
        return

    if s == "adm_add_app":
        try:
            parts = (msg.text or "").strip().split("|")
            name = parts[0].strip()
            emoji = parts[1].strip() if len(parts) > 1 else "📱"
            if not name:
                raise ValueError("الاسم فارغ")
            db.add_app(name, emoji)
            send(msg.chat.id, f"✅ تم إضافة القسم: {emoji} {name}",
                 kb.admin_apps_keyboard(db.get_apps(only_active=False)))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\nالشكل: <code>الاسم|الإيموجي</code>")
        clear_state(uid)
        return

    if s == "adm_add_svc":
        try:
            parts = [p.strip() for p in (msg.text or "").strip().split("|")]
            if len(parts) < 3:
                raise ValueError("لازم: SERVICE_ID|نقاط_لكل_1000|SITE_ID")
            api_id = parts[0]
            pts_1k = int(parts[1])
            site_id = int(parts[2])
            custom_name = parts[3] if len(parts) > 3 else None
            send(msg.chat.id, "⏳ جارٍ جلب بيانات الخدمة...")
            info = smm.get_service_info(api_id, site_id)
            if not info:
                # إضافة بدون بيانات الموقع
                name = custom_name or f"خدمة {api_id}"
                mn, mx, rate = 100, 100000, 0.5
            else:
                name = custom_name or info.get("name", f"خدمة {api_id}")
                try:
                    mn = int(info.get("min", 100))
                except:
                    mn = 100
                try:
                    mx = int(info.get("max", 100000))
                except:
                    mx = 100000
                try:
                    rate = float(info.get("rate", 0.5))
                except:
                    rate = 0.5
            app_id = d["app_id"]
            db.add_service(app_id, name, "", api_id, pts_1k, mn, mx, rate, site_id)
            send(msg.chat.id,
                f"<b>✅ تمت إضافة الخدمة!</b>\n\n"
                f"<b>{name}</b>\n"
                f"API: <code>{api_id}</code>\n"
                f"السعر: <b>{pts_1k:,}</b> نقطة / 1000\n"
                f"الحدود: {mn:,} — {mx:,}",
                kb.admin_app_view(app_id, db.get_app_services(app_id, only_active=False)))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\n\n<code>SERVICE_ID|نقاط_لكل_1000|SITE_ID</code>")
        clear_state(uid)
        return

    if s == "adm_add_smm_site":
        try:
            parts = [p.strip() for p in (msg.text or "").strip().split("|")]
            if len(parts) < 3:
                raise ValueError("لازم: الاسم|API_URL|API_KEY")
            name = parts[0]
            api_url = parts[1]
            api_key = parts[2]
            if not api_url.startswith("http"):
                raise ValueError("الـ URL يجب أن يبدأ بـ http")
            sid = db.add_smm_site(name, api_url, api_key)
            # اختبار الاتصال
            bal = smm.get_balance(sid)
            send(msg.chat.id,
                f"<b>✅ تمت إضافة الموقع!</b>\n\n"
                f"الاسم: {name}\n"
                f"URL: {api_url}\n"
                f"الرصيد الحالي: <b>{bal:.2f}$</b>",
                kb.back("adm_smm_sites"))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\n<code>الاسم|API_URL|API_KEY</code>")
        clear_state(uid)
        return

    if s == "adm_add_orch":
        try:
            parts = [p.strip() for p in (msg.text or "").strip().split("|")]
            if len(parts) < 2:
                raise ValueError("لازم: channel_id|الاسم")
            ch_id = parts[0]
            name = parts[1]
            ok = db.add_order_channel(ch_id, name)
            if ok:
                # اختبار الإرسال
                try:
                    bot.send_message(ch_id, "<b>✅ تم ربط قناة الطلبات بالبوت!</b>\n\nستظهر تفاصيل الطلبات هنا.")
                except Exception as test_e:
                    send(msg.chat.id, f"<b>⚠️ تمت الإضافة لكن فشل اختبار الإرسال!</b>\n\nتأكد أن البوت أدمن في القناة.\n\nخطأ: {test_e}")
                    clear_state(uid)
                    return
                send(msg.chat.id, f"<b>✅ تمت إضافة القناة!</b>\n{name}", kb.back("adm_order_channels"))
            else:
                send(msg.chat.id, "القناة موجودة مسبقاً!", kb.back("adm_order_channels"))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\n<code>channel_id|الاسم</code>")
        clear_state(uid)
        return

    if s == "adm_db_import":
        # استيراد من ملف JSON
        if msg.document:
            try:
                file_info = bot.get_file(msg.document.file_id)
                downloaded = bot.download_file(file_info.file_path)
                json_str = downloaded.decode("utf-8")
                ok, result_msg = db.import_db_json(json_str)
                send(msg.chat.id,
                    f"{'✅' if ok else '❌'} {result_msg}",
                    kb.back("adm_database"))
            except Exception as e:
                send(msg.chat.id, f"❌ خطأ في قراءة الملف: {e}", kb.back("adm_database"))
        elif msg.text:
            try:
                ok, result_msg = db.import_db_json(msg.text.strip())
                send(msg.chat.id,
                    f"{'✅' if ok else '❌'} {result_msg}",
                    kb.back("adm_database"))
            except Exception as e:
                send(msg.chat.id, f"❌ خطأ: {e}", kb.back("adm_database"))
        else:
            send(msg.chat.id, "أرسل ملف JSON أو انسخ محتواه.", kb.back("adm_database"))
        clear_state(uid)
        return

    if s == "adm_wheel_add":
        try:
            parts = [p.strip() for p in (msg.text or "").strip().split("|")]
            if len(parts) < 2:
                raise ValueError("لازم: النقاط|الوزن")
            pts = int(parts[0])
            weight = float(parts[1])
            emoji = parts[2] if len(parts) > 2 else ""
            label = parts[3] if len(parts) > 3 else ""
            if pts <= 0 or weight <= 0:
                raise ValueError("القيم لازم أكبر من صفر")
            db.add_wheel_prize(pts, weight, emoji, label)
            send(msg.chat.id,
                f"✅ تمت الإضافة: <b>{pts:,}</b> نقطة | وزن {weight:g} {emoji} {label}",
                kb.back("adm_wheel"))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\n<code>النقاط|الوزن|الإيموجي|التسمية</code>")
        clear_state(uid)
        return

    if s == "adm_add_free_svc":
        try:
            parts = [p.strip() for p in (msg.text or "").strip().split("|")]
            if len(parts) < 5:
                raise ValueError("لازم 5 حقول على الأقل")
            name = parts[0]
            api_id = parts[1]
            daily = int(parts[2])
            mn = int(parts[3])
            mx = int(parts[4])
            site_id = int(parts[5]) if len(parts) > 5 else None
            desc = parts[6] if len(parts) > 6 else ""
            db.add_free_service(name, desc, api_id, daily, mn, mx, site_id)
            send(msg.chat.id, f"✅ تمت إضافة الخدمة المجانية: {name}",
                 kb.admin_free_svcs(db.get_free_services(only_active=False)))
        except Exception as e:
            send(msg.chat.id,
                 f"❌ خطأ: {e}\n<code>الاسم|API_ID|حد_يومي|حد_أدنى|حد_أقصى|SITE_ID|الوصف</code>")
        clear_state(uid)
        return

    if s == "adm_mand_step1":
        set_state(uid, "adm_mand_step2", channel_id=(msg.text or "").strip())
        send(msg.chat.id,
             f"المعرف: <code>{(msg.text or '').strip()}</code>\n\n<b>الخطوة 2:</b> أرسل اسم القناة:",
             kb.back("adm_mandatory"))
        return

    if s == "adm_mand_step2":
        set_state(uid, "adm_mand_step3", channel_id=d["channel_id"], name=(msg.text or "").strip())
        send(msg.chat.id,
            f"الاسم: {(msg.text or '').strip()}\n\n<b>الخطوة 3:</b> أرسل رابط القناة (https://t.me/...):",
            kb.back("adm_mandatory"))
        return

    if s == "adm_mand_step3":
        set_state(uid, "adm_mand_step4", channel_id=d["channel_id"],
                  name=d["name"], url=(msg.text or "").strip())
        send(msg.chat.id,
            "<b>الخطوة 4:</b> أرسل عدد الأعضاء المطلوب\n"
            "<i>(0 = بدون حد)</i>",
            kb.back("adm_mandatory"))
        return

    if s == "adm_mand_step4":
        try:
            target = int((msg.text or "").strip())
            ok = db.add_mandatory_channel(d["channel_id"], d["name"], d["url"], target)
            if ok:
                send(msg.chat.id,
                    f"<b>✅ تمت الإضافة!</b>\n{d['name']}\n"
                    f"الهدف: {'بدون حد' if target == 0 else f'{target:,} عضو'}",
                    kb.admin_main())
            else:
                send(msg.chat.id, "القناة موجودة مسبقاً!", kb.admin_main())
        except ValueError:
            send(msg.chat.id, "أرسل رقماً!")
            return
        clear_state(uid)
        return

    if s == "adm_add_ptch":
        try:
            parts = (msg.text or "").strip().split("|")
            if len(parts) < 4:
                raise ValueError("لازم 4 حقول")
            ok = db.add_points_channel(parts[0].strip(), parts[1].strip(),
                                       parts[2].strip(), int(parts[3].strip()))
            send(msg.chat.id, "✅ تمت الإضافة!" if ok else "موجودة مسبقاً!", kb.admin_main())
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\n<code>channel_id|الاسم|https://t.me/ch|النقاط</code>")
        clear_state(uid)
        return

    if s == "adm_broadcast":
        users = db.get_all_users()
        ok_u = 0
        for u in users:
            try:
                bot.copy_message(u["tg_id"], msg.chat.id, msg.message_id)
                ok_u += 1
                time.sleep(0.04)
            except:
                pass

        channel_ids = set()
        for ch in db.get_order_channels():
            channel_ids.add(ch["channel_id"])
        for ch in db.get_points_channels():
            channel_ids.add(ch["channel_id"])
        for ch in db.get_mandatory_channels():
            channel_ids.add(ch["channel_id"])

        ok_ch = 0
        for ch_id in channel_ids:
            try:
                bot.copy_message(ch_id, msg.chat.id, msg.message_id)
                ok_ch += 1
                time.sleep(0.04)
            except:
                pass

        send(msg.chat.id,
            f"<b>✅ تمت الإذاعة</b>\n\n"
            f"تم الإرسال: {ok_u}/{len(users)} مستخدمين\n"
            f"إلى {ok_ch}/{len(channel_ids)} قناة/قناة مشتركة",
            kb.admin_main())
        clear_state(uid)
        return

    if s == "adm_topup_id":
        try:
            target = int((msg.text or "").strip())
            if not db.get_user(target):
                send(msg.chat.id, "❌ المستخدم غير موجود!")
                clear_state(uid)
                return
            set_state(uid, "adm_topup_amt", target_id=target)
            send(msg.chat.id, f"أرسل عدد النقاط لـ <code>{target}</code>:")
        except ValueError:
            send(msg.chat.id, "❌ ID غير صحيح")
            clear_state(uid)
        return

    if s == "adm_topup_amt":
        try:
            amt = int((msg.text or "").strip())
            target = d.get("target_id")
            db.add_points(target, amt)
            send(msg.chat.id, f"✅ تم شحن <b>{amt:,}</b> نقطة", kb.admin_main())
            try:
                bot.send_message(target, f"<b>🎁 تم شحن نقاطك!</b>\n\n+ <b>{amt:,}</b> نقطة")
            except:
                pass
        except ValueError:
            send(msg.chat.id, "❌ رقم غير صحيح")
        clear_state(uid)
        return

    if s == "adm_search_user":
        try:
            target = int((msg.text or "").strip())
            u = db.get_user(target)
            if not u:
                send(msg.chat.id, "❌ غير موجود!")
                clear_state(uid)
                return
            rc = db.get_referral_count(target)
            oc = db.get_user_orders_count(target)
            send(msg.chat.id,
                f"<b>بيانات المستخدم</b>\n\n"
                f"<b>المعرف:</b> <code>{target}</code>\n"
                f"<b>الاسم:</b> {u['full_name']}\n"
                f"<b>اليوزر:</b> @{u['username'] or '—'}\n"
                f"<b>النقاط:</b> {u['points']:,}\n"
                f"<b>الدعوات:</b> {rc}\n"
                f"<b>الطلبات:</b> {oc}\n"
                f"<b>محظور:</b> {'نعم' if u['is_banned'] else 'لا'}\n"
                f"<b>انضم:</b> {str(u['join_date'])[:10]}",
                kb.admin_user_view(target, bool(u["is_banned"])))
        except ValueError:
            send(msg.chat.id, "❌ ID غير صحيح")
        clear_state(uid)
        return

    if s in ("adm_add_points", "adm_sub_points"):
        try:
            amt = int((msg.text or "").strip())
            target = d.get("target_id")
            if s == "adm_add_points":
                db.add_points(target, amt)
                send(msg.chat.id, f"✅ تمت إضافة {amt:,} نقطة", kb.admin_main())
                try:
                    bot.send_message(target, f"<b>🎁 تمت إضافة {amt:,} نقطة لحسابك!</b>")
                except:
                    pass
            else:
                if db.deduct_points(target, amt):
                    send(msg.chat.id, f"✅ تم خصم {amt:,} نقطة", kb.admin_main())
                else:
                    send(msg.chat.id, "❌ نقاط غير كافية", kb.admin_main())
        except ValueError:
            send(msg.chat.id, "❌ رقم غير صحيح")
        clear_state(uid)
        return

    if s == "adm_set_terms":
        val = (msg.text or "").strip()
        db.set_config("terms_text", val)
        send(msg.chat.id, "✅ تم تحديث شروط الاستخدام والأحكام!", kb.back("adm_bot_settings"))
        clear_state(uid)
        return

    if s == "adm_add_coupon":
        try:
            parts = [p.strip() for p in (msg.text or "").strip().split("|")]
            code     = parts[0].upper()
            discount = int(parts[1])
            max_uses = int(parts[2]) if len(parts) > 2 else -1
            if not code or discount <= 0 or discount > 100:
                raise ValueError("خصم بين 1-100")
            ok = db.add_coupon(code, discount, max_uses)
            if ok:
                send(msg.chat.id,
                    f"<b>✅ تم إضافة الكوبون!</b>\n\n"
                    f"الكود: <code>{code}</code>\n"
                    f"الخصم: {discount}%\n"
                    f"الاستخدامات: {'غير محدود' if max_uses==-1 else max_uses}",
                    kb.back("adm_coupons"))
            else:
                send(msg.chat.id, "❌ الكود موجود مسبقاً، اختر كوداً آخر")
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\n<code>الكود|الخصم%|عدد الاستخدامات</code>")
        clear_state(uid)
        return

    if s == "adm_create_gift_link":
        try:
            parts = [p.strip() for p in (msg.text or "").strip().split("|")]
            points   = int(parts[0])
            max_uses = int(parts[1]) if len(parts) > 1 else -1
            note     = parts[2] if len(parts) > 2 else ""
            if points <= 0:
                raise ValueError("النقاط لازم أكبر من صفر")
            code = db.create_gift_link(points, max_uses, note)
            if code:
                link = f"https://t.me/{config.BOT_USERNAME.lstrip('@')}?start=gift_{code}"
                send(msg.chat.id,
                    f"<b>✅ تم إنشاء رابط الهدية!</b>\n\n"
                    f"النقاط: <b>{points:,}</b>\n"
                    f"الاستخدامات: {'غير محدود' if max_uses == -1 else max_uses}\n"
                    f"الملاحظة: {note or '—'}\n\n"
                    f"<b>الرابط:</b>\n<code>{link}</code>",
                    kb.back("adm_gift_links"))
            else:
                send(msg.chat.id, "❌ حدث خطأ، حاول مرة أخرى")
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\n<code>النقاط|عدد الاستخدامات|ملاحظة</code>")
        clear_state(uid)
        return

    if s == "adm_set_low_alert":
        try:
            val = int((msg.text or "").strip())
            if val < 0:
                raise ValueError
            db.set_config("low_points_alert", str(val))
            send(msg.chat.id,
                f"✅ تم التحديث!\nإشعار الرصيد المنخفض: <b>{val}</b> نقطة" +
                (" (معطّل)" if val == 0 else ""),
                kb.back("adm_alerts_settings"))
        except:
            send(msg.chat.id, "❌ أرسل رقم صحيح (0 للتعطيل)")
        clear_state(uid)
        return

    if s == "adm_recharge_set_pts":
        try:
            pts = int((msg.text or "").strip())
            if pts <= 0:
                raise ValueError
        except:
            send(msg.chat.id, "❌ أرسل رقم صحيح أكبر من صفر")
            return
        rid = get_state(uid)["data"]["rid"]
        r = db.approve_recharge(rid, pts)
        clear_state(uid)
        if not r:
            send(msg.chat.id, "❌ الطلب غير موجود أو معالج مسبقاً")
            return
        user = db.get_user(r["user_id"])
        send(msg.chat.id,
            f"<b>✅ تم شحن {pts:,} نقطة للمستخدم</b>\n\n"
            f"المستخدم: {user['full_name'] if user else r['user_id']}\n"
            f"رصيده الجديد: <b>{user['points']:,}</b> نقطة",
            kb.admin_main())
        try:
            bot.send_message(r["user_id"],
                f"<b>✅ تم شحن رصيدك!</b>\n\n"
                f"<b>+ {pts:,} نقطة</b> 🎉\n\n"
                f"رصيدك الحالي: <b>{user['points']:,}</b> نقطة")
        except:
            pass
        return

    if s == "adm_add_store_product":
        try:
            parts = [p.strip() for p in (msg.text or "").strip().split("|")]
            if len(parts) < 2:
                raise ValueError("لازم: الاسم|السعر")
            name  = parts[0]
            price = int(parts[1])
            emoji = parts[2] if len(parts) > 2 else "🛍️"
            desc  = parts[3] if len(parts) > 3 else ""
            stock = int(parts[4]) if len(parts) > 4 else -1
            if price <= 0:
                raise ValueError("السعر لازم أكبر من صفر")
            db.add_store_product(name, desc, emoji, price, stock)
            send(msg.chat.id,
                f"<b>✅ تمت إضافة المنتج!</b>\n\n"
                f"{emoji} <b>{name}</b>\n"
                f"السعر: <b>{price:,}</b> نقطة\n"
                f"المخزون: {'غير محدود' if stock == -1 else stock}",
                kb.back("adm_store"))
        except Exception as e:
            send(msg.chat.id,
                f"❌ خطأ: {e}\n<code>الاسم|السعر|الإيموجي|الوصف|المخزون</code>")
        clear_state(uid)
        return

    if s == "adm_create_invite":
        try:
            parts = (msg.text or "").strip().split("|")
            if len(parts) < 3:
                raise ValueError("لازم 3 حقول")
            code = parts[0].strip().upper()
            pts = int(parts[1])
            mx = int(parts[2])
            ok = db.create_invite(code, pts, mx)
            if ok:
                bu = config.BOT_USERNAME.lstrip("@")
                url = f"https://t.me/{bu}?start=invite_{code}"
                send(msg.chat.id,
                    f"<b>✅ تم الإنشاء!</b>\n\n"
                    f"الكود: <code>{code}</code>\n"
                    f"النقاط: {pts:,}\n"
                    f"الحد: {'∞' if mx == 0 else mx}\n\n"
                    f"الرابط:\n<code>{url}</code>",
                    kb.back("adm_invite_links"))
            else:
                send(msg.chat.id, "❌ الكود موجود مسبقاً!", kb.back("adm_invite_links"))
        except Exception as e:
            send(msg.chat.id, f"❌ خطأ: {e}\n<code>الكود|النقاط|الحد</code>")
        clear_state(uid)
        return

    if s == "adm_add_admin":
        try:
            target = int((msg.text or "").strip())
            u = db.get_user(target)
            name = u["full_name"] if u else str(target)
            if db.add_extra_admin(target, name):
                send(msg.chat.id, f"✅ تمت إضافة الأدمن: {name} ({target})", kb.admin_main())
                try:
                    bot.send_message(target, "<b>🎉 تمت ترقيتك إلى أدمن في البوت!</b>")
                except:
                    pass
            else:
                send(msg.chat.id, "المستخدم أدمن مسبقاً!")
        except ValueError:
            send(msg.chat.id, "❌ ID غير صحيح")
        clear_state(uid)
        return

    # ─── تغيير الإعدادات (نفس خريطة الأزرار _cfg_btn_map لتفادي أي تضارب) ───
    cfg_map = _cfg_btn_map
    if s in cfg_map:
        key, back_cb = cfg_map[s]
        val = (msg.text or "").strip()
        db.set_config(key, val)
        send(msg.chat.id, f"✅ تم التحديث: <b>{val}</b>", kb.back(back_cb))
        clear_state(uid)
        return


# ══════════════════════════════════════════════════════════════════
#   الموافقة على الطلبات — أدمن
# ══════════════════════════════════════════════════════════════════

def _execute_smm_order_after_approval(oid):
    """تنفيذ طلب SMM بعد موافقة الأدمن"""
    o = db.get_order(oid)
    if not o:
        return
    site_id = o["site_id"] if "site_id" in o.keys() else None
    result = smm.create_order(o["service_id"], o["link"], o["quantity"], site_id)
    api_id = str(result.get("order", ""))
    err = result.get("error")
    if err:
        # فشل التنفيذ — إرجاع النقاط
        db.add_points(o["user_id"], o["points_used"])
        db.update_order(oid, "canceled")
        try:
            bot.send_message(o["user_id"],
                f"<b>❌ فشل تنفيذ طلبك #{oid}</b>\n\n{err}\n\n<i>تم استرداد نقاطك.</i>")
        except:
            pass
    else:
        db.update_order(oid, "inprogress", api_id)
        try:
            bot.send_message(o["user_id"],
                f"<b>✅ تمت الموافقة على طلبك #{oid}!</b>\n\n"
                f"الخدمة: {o['service_name']}\n"
                f"الكمية: {o['quantity']:,}\n"
                f"رقم API: <code>{api_id}</code>\n\n"
                f"<i>سيصلك إشعار عند الاكتمال</i>")
        except:
            pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_approve_smm_") or c.data.startswith("adm_approve_fund_"))
def cb_adm_approve_smm(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    oid = int(parts[-1])
    o = db.get_order(oid)
    if not o or o["pending_approval"] == 0:
        bot.answer_callback_query(call.id, "الطلب معالج مسبقاً!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return
    db.approve_order(oid)
    bot.answer_callback_query(call.id, "✅ تمت الموافقة، جارٍ التنفيذ...")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.edit_message_text(
            call.message.text + f"\n\n<b>✅ وافق عليه: {call.from_user.first_name}</b>",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
    except:
        pass
    threading.Thread(target=_execute_smm_order_after_approval, args=(oid,), daemon=True).start()


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_reject_smm_") or c.data.startswith("adm_reject_fund_"))
def cb_adm_reject_smm(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    oid = int(parts[-1])
    o = db.reject_order(oid)
    if not o or o["pending_approval"] == 0:
        bot.answer_callback_query(call.id, "الطلب معالج مسبقاً!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return
    bot.answer_callback_query(call.id, "❌ تم الرفض واسترداد النقاط")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.edit_message_text(
            call.message.text + f"\n\n<b>❌ رفضه: {call.from_user.first_name}</b>",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
    except:
        pass
    try:
        bot.send_message(o["user_id"],
            f"<b>❌ تم رفض طلبك #{oid}</b>\n\n"
            f"الخدمة: {o['service_name']}\n"
            f"<i>تم استرداد {o['points_used']:,} نقطة لحسابك.</i>")
    except:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_approve_store_"))
def cb_adm_approve_store(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    oid = int(call.data.split("_")[-1])
    o = db.get_store_order(oid)
    if not o or o["pending_approval"] == 0:
        bot.answer_callback_query(call.id, "الطلب معالج مسبقاً!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return
    db.approve_store_order(oid)
    bot.answer_callback_query(call.id, "✅ تمت الموافقة! تواصل مع المستخدم لتسليم المنتج")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.edit_message_text(
            call.message.text + f"\n\n<b>✅ وافق عليه: {call.from_user.first_name}</b>",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
    except:
        pass
    try:
        bot.send_message(o["user_id"],
            f"<b>✅ تمت الموافقة على طلب المتجر #{oid}!</b>\n\n"
            f"المنتج: {o['product_name']}\n\n"
            f"<i>سيتواصل معك الأدمن قريباً لتسليمك المنتج.</i>")
    except:
        pass


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_reject_store_"))
def cb_adm_reject_store(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    oid = int(call.data.split("_")[-1])
    o = db.reject_store_order(oid)
    if not o or o["pending_approval"] == 0:
        bot.answer_callback_query(call.id, "الطلب معالج مسبقاً!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return
    bot.answer_callback_query(call.id, "❌ تم الرفض واسترداد النقاط")
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.edit_message_text(
            call.message.text + f"\n\n<b>❌ رفضه: {call.from_user.first_name}</b>",
            call.message.chat.id, call.message.message_id, parse_mode="HTML")
    except:
        pass
    try:
        bot.send_message(o["user_id"],
            f"<b>❌ تم رفض طلب المتجر #{oid}</b>\n\n"
            f"المنتج: {o['product_name']}\n"
            f"<i>تم استرداد {o['points_used']:,} نقطة لحسابك.</i>")
    except:
        pass


# ─── قائمة الطلبات المعلقة (للأدمن) ──────────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_pending_orders")
def cb_adm_pending_orders(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    smm_pending = db.get_pending_orders()
    store_pending = db.get_pending_store_orders()
    total = len(smm_pending) + len(store_pending)
    if total == 0:
        edit(call, "<b>📋 الطلبات المعلقة</b>\n\nلا توجد طلبات معلقة حالياً.", kb.back("adm_back"))
        return
    text = f"<b>📋 الطلبات المعلقة ({total})</b>\n\n<b></b>\n"
    if smm_pending:
        text += f"<b>طلبات الخدمات ({len(smm_pending)}):</b>\n"
        for o in smm_pending[:5]:
            text += f"  #{o['id']} — {o['service_name']} | {o['quantity']:,} وحدة\n"
    if store_pending:
        text += f"\n<b>طلبات المتجر ({len(store_pending)}):</b>\n"
        for o in store_pending[:5]:
            text += f"  #{o['id']} — {o['product_name']}\n"
    edit(call, text, kb.back("adm_back"))


# ══════════════════════════════════════════════════════════════════
#   المتجر المستقل — للمستخدم
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "store")
def cb_store(call: CallbackQuery):
    products = db.get_store_products()
    user = db.get_user(call.from_user.id)
    if not products:
        edit(call,
            "<b>⭐ نجوم 🚀 جوائز 🛍 رصيد أرقام</b>\n\n"
            "لا توجد منتجات متاحة في المتجر حالياً.",
            kb.back())
        return
    edit(call,
        f"<b>⭐ نجوم 🚀 جوائز 🛍 رصيد أرقام</b>\n\n"
        f"<b></b>\n"
        f"رصيدك: <b>{user['points']:,}</b> نقطة\n"
        f"<b></b>\n\n"
        f"اختر المنتج الذي تريد شراءه:",
        kb.store_products_keyboard(products))


@bot.callback_query_handler(func=lambda c: c.data.startswith("store_product_"))
def cb_store_product(call: CallbackQuery):
    try:
        pid = int(call.data.split("_")[-1])
    except:
        return
    product = db.get_store_product(pid)
    if not product:
        bot.answer_callback_query(call.id, "المنتج غير موجود")
        return
    user = db.get_user(call.from_user.id)
    enough = user["points"] >= product["price"]
    nm = f"{product['emoji']} {product['name']}"
    stock_txt = "∞ متاح" if product["stock"] == -1 else f"{product['stock']:,} متبقي"
    warn = "" if enough else f"\n\n<b>⚠️ نقاطك غير كافية!</b> ينقصك <b>{product['price'] - user['points']:,}</b> نقطة."
    edit(call,
        f"<b>{nm}</b>\n\n"
        f"<b></b>\n"
        f"الوصف: {product['description'] or '—'}\n"
        f"السعر: <b>{product['price']:,}</b> نقطة\n"
        f"المخزون: {stock_txt}\n"
        f"رصيدك: <b>{user['points']:,}</b> نقطة\n"
        f"<b></b>{warn}",
        mk(
            [_btn("🛒 شراء الآن", f"store_buy_{pid}", color="green")] if enough else [],
            [_btn("◀️ رجوع للمتجر", "store", color="red")],
        ) if enough else mk([_btn("◀️ رجوع للمتجر", "store", color="red")]))


@bot.callback_query_handler(func=lambda c: c.data.startswith("store_buy_"))
def cb_store_buy(call: CallbackQuery):
    try:
        pid = int(call.data.split("_")[-1])
    except:
        return
    product = db.get_store_product(pid)
    if not product:
        bot.answer_callback_query(call.id, "المنتج غير موجود")
        return
    user = db.get_user(call.from_user.id)
    if user["points"] < product["price"]:
        bot.answer_callback_query(call.id, "نقاطك غير كافية!", show_alert=True)
        return
    if not db.deduct_points(call.from_user.id, product["price"]):
        bot.answer_callback_query(call.id, "نقاطك غير كافية!", show_alert=True)
        return
    nm = f"{product['emoji']} {product['name']}"
    oid = db.create_store_order(call.from_user.id, pid, nm, product["price"])
    user = db.get_user(call.from_user.id)

    # إشعار الأدمن
    _notify_admin_approve_store_order(oid, dict(user), nm, product["price"])

    edit(call,
        f"<b>⏳ تم إرسال طلب الشراء!</b>\n\n"
        f"<b></b>\n"
        f"رقم الطلب: <b>#{oid}</b>\n"
        f"المنتج: {nm}\n"
        f"النقاط المدفوعة: {product['price']:,}\n"
        f"رصيدك المتبقي: {user['points']:,}\n"
        f"<b></b>\n\n"
        f"<i>سيتواصل معك الأدمن قريباً لتسليمك المنتج</i>",
        kb.back())


@bot.callback_query_handler(func=lambda c: c.data == "my_store_orders")
def cb_my_store_orders(call: CallbackQuery):
    orders = db.get_user_store_orders(call.from_user.id, limit=8)
    if not orders:
        edit(call, "<b>طلبات المتجر</b>\n\nلا توجد طلبات بعد.", kb.back())
        return
    icons = {"pending_approval": "⏳", "approved": "✅", "rejected": "❌"}
    text = "<b>طلبات المتجر</b>\n\n"
    for o in orders:
        ic = icons.get(o["status"], "•")
        text += f"{ic} <b>طلب #{o['id']}</b> — {o['product_name']}\n"
        text += f"    النقاط: {o['points_used']:,} | {str(o['created_at'])[:10]}\n\n"
    edit(call, text, kb.back())


# ══════════════════════════════════════════════════════════════════
#   إدارة المتجر — أدمن
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "adm_store")
def cb_adm_store(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    products = db.get_store_products(only_active=False)
    pending = db.get_pending_store_orders()
    edit(call,
        f"<b>🛍️ إدارة المتجر</b>\n\n"
        f"المنتجات: <b>{len(products)}</b>\n"
        f"طلبات معلقة: <b>{len(pending)}</b>",
        kb.admin_store_keyboard(products))


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_store_product")
def cb_adm_add_store_product(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_add_store_product")
    edit(call,
        "<b>➕ إضافة منتج للمتجر</b>\n\n"
        "أرسل بهذا الشكل:\n"
        "<code>الاسم|السعر بالنقاط|الإيموجي|الوصف|المخزون</code>\n\n"
        "أمثلة:\n"
        "<code>حساب نتفليكس|500|🎬|اشتراك شهري|10</code>\n"
        "<code>كارت شحن|1000|💳|كارت 10 جنيه|-1</code>\n\n"
        "<i>المخزون -1 = غير محدود</i>",
        kb.back("adm_store"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_store_product_"))
def cb_adm_store_product_view(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    pid = int(call.data.split("_")[-1])
    p = db.get_store_product(pid)
    if not p:
        bot.answer_callback_query(call.id, "المنتج غير موجود")
        return
    st = "✅ نشط" if p["is_active"] else "❌ متوقف"
    stock_txt = "∞ غير محدود" if p["stock"] == -1 else str(p["stock"])
    edit(call,
        f"<b>{p['emoji']} {p['name']}</b>\n\n"
        f"الحالة: {st}\n"
        f"السعر: <b>{p['price']:,}</b> نقطة\n"
        f"المخزون: {stock_txt}\n"
        f"الوصف: {p['description'] or '—'}",
        mk(
            [_btn("✅/❌ تفعيل/تعطيل", f"adm_tog_store_{pid}", color="green")],
            [_btn("🗑️ حذف المنتج", f"adm_del_store_{pid}", color="red")],
            [_btn("◀️ رجوع للمتجر", "adm_store", color="red")],
        ))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_tog_store_"))
def cb_adm_tog_store(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    pid = int(call.data.split("_")[-1])
    db.toggle_store_product(pid)
    bot.answer_callback_query(call.id, "تم التبديل")
    call.data = f"adm_store_product_{pid}"
    cb_adm_store_product_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_store_"))
def cb_adm_del_store(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    pid = int(call.data.split("_")[-1])
    db.delete_store_product(pid)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_store(call)


@bot.callback_query_handler(func=lambda c: c.data == "adm_pending_recharges")
def cb_adm_pending_recharges(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    reqs = db.get_pending_recharges()
    if not reqs:
        edit(call, "<b>💵 طلبات الشحن المعلقة</b>\n\nلا توجد طلبات معلقة.", kb.back("adm_back"))
        return
    text = f"<b>💵 طلبات الشحن المعلقة ({len(reqs)})</b>\n\n<b></b>\n"
    for r in reqs[:8]:
        user = db.get_user(r["user_id"])
        nm = user["full_name"] if user else str(r["user_id"])
        text += f"  #{r['id']} — {nm} | {r['method']} | {str(r['created_at'])[:10]}\n"
    text += "\n<i>ستوصلك صور الإيصالات مباشرة في المحادثة</i>"
    edit(call, text, kb.back("adm_back"))


# ══════════════════════════════════════════════════════════════════
#   كوبونات الخصم — مستخدم
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "use_coupon")
def cb_use_coupon(call: CallbackQuery):
    set_state(call.from_user.id, "enter_coupon")
    edit(call,
        "<b>🎟️ كوبون الخصم</b>\n\n"
        "أرسل كود الكوبون:",
        kb.back())


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "enter_coupon")
def msg_enter_coupon(msg: Message):
    uid = msg.from_user.id
    code = (msg.text or "").strip().upper()
    coupon = db.get_coupon(code)
    if not coupon:
        send(msg.chat.id, "❌ الكوبون غير موجود أو منتهي الصلاحية!")
        return
    if db.user_used_coupon(uid, coupon["id"]):
        send(msg.chat.id, "❌ لقد استخدمت هذا الكوبون من قبل!")
        return
    if coupon["max_uses"] != -1 and coupon["used_count"] >= coupon["max_uses"]:
        send(msg.chat.id, "❌ انتهت الاستخدامات المتاحة لهذا الكوبون!")
        return
    # احفظ الكوبون في الـ state
    d = get_state(uid).get("data", {})
    d["active_coupon_id"]       = coupon["id"]
    d["active_coupon_code"]     = code
    d["active_coupon_discount"] = coupon["discount"]
    set_state(uid, "coupon_active", d)
    clear_state(uid)
    send(msg.chat.id,
        f"<b>✅ تم تفعيل الكوبون!</b>\n\n"
        f"الكود: <code>{code}</code>\n"
        f"الخصم: <b>{coupon['discount']}%</b>\n\n"
        f"<i>الخصم سيطبق على طلبك القادم تلقائياً</i>",
        kb.back())
    # خزّن في session
    set_state(uid, "has_coupon", coupon_id=coupon["id"],
              code=code, discount=coupon["discount"])


# ══════════════════════════════════════════════════════════════════
#   ليدربورد
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "leaderboard")
def cb_leaderboard(call: CallbackQuery):
    top_pts   = db.get_leaderboard_points(10)
    top_orders = db.get_leaderboard_orders(10)
    medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7

    text = "<b>🏆 لوحة الصدارة</b>\n\n"
    text += "<b>💎 أكثر رصيداً:</b>\n"
    for i, u in enumerate(top_pts):
        nm = u["full_name"] or u["username"] or str(u["tg_id"])
        text += f"{medals[i]} {nm} — <b>{u['points']:,}</b> نقطة\n"

    text += "\n<b>📦 أكثر طلبات:</b>\n"
    for i, o in enumerate(top_orders):
        user = db.get_user(o["user_id"])
        nm = user["full_name"] if user else str(o["user_id"])
        text += f"{medals[i]} {nm} — <b>{o['cnt']:,}</b> طلب\n"

    edit(call, text, kb.back())


# ══════════════════════════════════════════════════════════════════
#   تتبع الطلب
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "track_order")
def cb_track_order(call: CallbackQuery):
    set_state(call.from_user.id, "track_order")
    edit(call,
        "<b>🔍 تتبع الطلب</b>\n\n"
        "أرسل رقم الطلب:",
        kb.back())


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "track_order")
def msg_track_order(msg: Message):
    uid = msg.from_user.id
    try:
        oid = int((msg.text or "").strip().lstrip("#"))
    except:
        send(msg.chat.id, "❌ رقم الطلب غير صحيح!")
        return
    o = db.get_order(oid)
    clear_state(uid)
    if not o or o["user_id"] != uid:
        send(msg.chat.id, "❌ لم يتم العثور على الطلب!")
        return
    status_map = {
        "pending":    "⏳ في الانتظار",
        "inprogress": "🔄 جارٍ التنفيذ",
        "completed":  "✅ مكتمل",
        "canceled":   "❌ ملغي",
        "partial":    "⚠️ مكتمل جزئي",
    }
    approval = "⏳ ينتظر موافقة الأدمن" if o["pending_approval"] == 1 else "✅ موافق عليه"
    st = status_map.get(o["status"], o["status"])
    send(msg.chat.id,
        f"<b>🔍 طلب #{oid}</b>\n\n"
        f"<b></b>\n"
        f"الخدمة: {o['service_name']}\n"
        f"القسم: {o['app_name'] or '—'}\n"
        f"الرابط: <code>{o['link']}</code>\n"
        f"الكمية: {o['quantity']:,}\n"
        f"النقاط: {o['points_used']:,}\n"
        f"الحالة: {st}\n"
        f"الموافقة: {approval}\n"
        f"التاريخ: {str(o['created_at'])[:16]}\n"
        f"<b></b>",
        kb.back())


# ══════════════════════════════════════════════════════════════════
#   إدارة روابط الهدايا — أدمن
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "adm_gift_links")
def cb_adm_gift_links(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    links = db.get_all_gift_links()
    text = f"<b>🎁 روابط الهدايا ({len(links)})</b>\n\n"
    rows = []
    for gl in links:
        st = "✅" if gl["is_active"] else "❌"
        uses = "∞" if gl["max_uses"] == -1 else f"{gl['used_count']}/{gl['max_uses']}"
        note_txt = f"  ({gl['note']})" if gl.get("note") else ""
        rows.append([_btn(
            f"{st} +{gl['points']} نقطة  ({uses}){note_txt}",
            f"adm_gift_link_{gl['id']}", color="green" if gl["is_active"] else "red")])
    rows.append([_btn("➕ إنشاء رابط هدية", "adm_create_gift_link", color="green")])
    rows.append([_btn("◀️ رجوع", "adm_back", color="red")])
    edit(call, text or "<b>🎁 لا توجد روابط هدايا</b>", mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data == "adm_create_gift_link")
def cb_adm_create_gift_link(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_create_gift_link")
    edit(call,
        "<b>➕ إنشاء رابط هدية جديد</b>\n\n"
        "أرسل بهذا الشكل:\n"
        "<code>النقاط|عدد الاستخدامات|ملاحظة (اختياري)</code>\n\n"
        "أمثلة:\n"
        "<code>100|50|هدية عيد الفطر</code>  — 100 نقطة لـ 50 شخص\n"
        "<code>500|-1</code>  — 500 نقطة غير محدودة",
        kb.back("adm_gift_links"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_gift_link_"))
def cb_adm_gift_link_view(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    gid = int(call.data.split("_")[-1])
    gl = db.get_conn().execute("SELECT * FROM gift_links WHERE id=?", (gid,)).fetchone()
    db.get_conn().close()
    if not gl:
        bot.answer_callback_query(call.id, "الرابط غير موجود")
        return
    # re-fetch properly
    conn = db.get_conn()
    gl = conn.execute("SELECT * FROM gift_links WHERE id=?", (gid,)).fetchone()
    conn.close()
    st = "✅ نشط" if gl["is_active"] else "❌ متوقف"
    uses = "غير محدود" if gl["max_uses"] == -1 else f"{gl['used_count']}/{gl['max_uses']}"
    bu = config.BOT_USERNAME.lstrip("@")
    link_https = f"https://t.me/{bu}?start=gift_{gl['code']}"
    edit(call,
        f"<b>🎁 رابط الهدية</b>\n\n"
        f"النقاط: <b>{gl['points']:,}</b>\n"
        f"الحالة: {st}\n"
        f"الاستخدامات: {uses}\n"
        f"الملاحظة: {gl.get('note') or '—'}\n\n"
        f"<b>انسخ الرابط:</b>\n<code>{link_https}</code>",
        mk(
            [_btn("🎁 افتح الهدية في البوت", url=link_https)],
            [_btn("📢 إرسال الهدية للقناة", f"adm_send_gift_{gid}", color="green")],
            [_btn("✅/❌ تفعيل/إيقاف", f"adm_tog_gift_{gid}", color="green")],
            [_btn("🗑️ حذف",            f"adm_del_gift_{gid}", color="red")],
            [_btn("◀️ رجوع",           "adm_gift_links",      color="red")],
        ))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_tog_gift_"))
def cb_adm_tog_gift(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    gid = int(call.data.split("_")[-1])
    db.toggle_gift_link(gid)
    bot.answer_callback_query(call.id, "تم التبديل")
    call.data = f"adm_gift_link_{gid}"
    cb_adm_gift_link_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_send_gift_"))
def cb_adm_send_gift(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    gid = int(call.data.split("_")[-1])
    conn = db.get_conn()
    gl = conn.execute("SELECT * FROM gift_links WHERE id=?", (gid,)).fetchone()
    conn.close()
    if not gl:
        bot.answer_callback_query(call.id, "الرابط غير موجود")
        return
    set_state(call.from_user.id, "adm_send_gift_to_channel", gid=gid)
    edit(call,
        "<b>📢 إرسال الهدية للقناة</b>\n\n"
        "أرسل <b>معرف القناة</b> أو <b>يوزرنيم القناة</b>:\n\n"
        "أمثلة:\n"
        "<code>@mychannel</code>\n"
        "<code>-1001234567890</code>",
        kb.back(f"adm_gift_link_{gid}"))


@bot.message_handler(func=lambda m: get_state(m.from_user.id).get("state") == "adm_send_gift_to_channel")
def msg_send_gift_to_channel(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    uid = msg.from_user.id
    channel = (msg.text or "").strip()
    d = get_state(uid).get("data", {})
    gid = d.get("gid")
    conn = db.get_conn()
    gl = conn.execute("SELECT * FROM gift_links WHERE id=?", (gid,)).fetchone()
    conn.close()
    if not gl:
        send(msg.chat.id, "❌ الرابط غير موجود!")
        clear_state(uid)
        return
    bu = config.BOT_USERNAME.lstrip("@")
    link_tg = f"https://t.me/{bu}?start=gift_{gl['code']}"
    note = gl.get("note") or "هدية مجانية"
    try:
        bot.send_message(
            channel,
            f"<b>🎁 {note}</b>\n\n"
            f"احصل على <b>{gl['points']:,}</b> نقطة مجاناً!\n"
            f"اضغط الزر بالأسفل لاستلام هديتك الآن 👇",
            reply_markup=mk([_btn("🎁 استلم هديتك الآن!", url=link_tg)]),
            parse_mode="HTML"
        )
        clear_state(uid)
        send(msg.chat.id, f"<b>✅ تم إرسال الهدية للقناة بنجاح!</b>",
             mk([_btn("◀️ رجوع", f"adm_gift_link_{gid}", color="red")]))
    except Exception as e:
        send(msg.chat.id,
            f"<b>❌ فشل الإرسال!</b>\n\n"
            f"تأكد إن البوت أدمن في القناة.\n"
            f"الخطأ: <code>{e}</code>",
            kb.back(f"adm_gift_link_{gid}"))
        clear_state(uid)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_gift_"))
def cb_adm_del_gift(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    gid = int(call.data.split("_")[-1])
    db.delete_gift_link(gid)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_gift_links(call)


# ══════════════════════════════════════════════════════════════════
#   إدارة الكوبونات — أدمن
# ══════════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "adm_coupons")
def cb_adm_coupons(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    coupons = db.get_all_coupons()
    text = f"<b>🎟️ الكوبونات ({len(coupons)})</b>\n\n"
    rows = []
    for c in coupons:
        st = "✅" if c["is_active"] else "❌"
        uses = "∞" if c["max_uses"] == -1 else f"{c['used_count']}/{c['max_uses']}"
        rows.append([_btn(f"{st} {c['code']}  —  {c['discount']}%  ({uses})",
                          f"adm_coupon_{c['id']}", color="blue" if c["is_active"] else "red")])
    rows.append([_btn("➕ إضافة كوبون", "adm_add_coupon", color="green")])
    rows.append([_btn("◀️ رجوع", "adm_back", color="red")])
    edit(call, text or "<b>🎟️ لا توجد كوبونات</b>", mk(*rows))


@bot.callback_query_handler(func=lambda c: c.data == "adm_add_coupon")
def cb_adm_add_coupon(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_add_coupon")
    edit(call,
        "<b>➕ إضافة كوبون جديد</b>\n\n"
        "أرسل بهذا الشكل:\n"
        "<code>الكود|نسبة الخصم%|عدد الاستخدامات</code>\n\n"
        "أمثلة:\n"
        "<code>SUMMER|20|100</code>  — خصم 20% لـ 100 شخص\n"
        "<code>VIP50|50|-1</code>  — خصم 50% غير محدود",
        kb.back("adm_coupons"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_coupon_"))
def cb_adm_coupon_view(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cid = int(call.data.split("_")[-1])
    c = db.get_coupon_by_id(cid)
    if not c:
        bot.answer_callback_query(call.id, "الكوبون غير موجود")
        return
    st = "✅ نشط" if c["is_active"] else "❌ متوقف"
    uses = "غير محدود" if c["max_uses"] == -1 else f"{c['used_count']}/{c['max_uses']}"
    edit(call,
        f"<b>🎟️ {c['code']}</b>\n\n"
        f"الخصم: <b>{c['discount']}%</b>\n"
        f"الحالة: {st}\n"
        f"الاستخدامات: {uses}",
        mk(
            [_btn("✅/❌ تفعيل/إيقاف", f"adm_tog_coupon_{cid}", color="green")],
            [_btn("🗑️ حذف",            f"adm_del_coupon_{cid}", color="red")],
            [_btn("◀️ رجوع",           "adm_coupons",           color="red")],
        ))


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_tog_coupon_"))
def cb_adm_tog_coupon(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cid = int(call.data.split("_")[-1])
    db.toggle_coupon(cid)
    bot.answer_callback_query(call.id, "تم التبديل")
    call.data = f"adm_coupon_{cid}"
    cb_adm_coupon_view(call)


@bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_coupon_"))
def cb_adm_del_coupon(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cid = int(call.data.split("_")[-1])
    db.delete_coupon(cid)
    bot.answer_callback_query(call.id, "تم الحذف")
    cb_adm_coupons(call)


# ── أدمن: إعدادات التقرير والتنبيهات ───────────────────────
@bot.callback_query_handler(func=lambda c: c.data == "adm_alerts_settings")
def cb_adm_alerts_settings(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    low = db.get_config("low_points_alert", "50")
    report = db.get_config("daily_report_enabled", "1")
    edit(call,
        f"<b>🔔 إعدادات التنبيهات والتقارير</b>\n\n"
        f"حد إشعار الرصيد المنخفض: <b>{low}</b> نقطة\n"
        f"التقرير اليومي: <b>{'✅ مفعّل' if report=='1' else '❌ متوقف'}</b>",
        mk(
            [_btn("✏️ تغيير حد الإشعار", "adm_set_low_alert",        color="blue")],
            [_btn(f"{'🔕 إيقاف' if report=='1' else '🔔 تفعيل'} التقرير اليومي",
                  "adm_toggle_daily_report", color="green" if report=="0" else "red")],
            [_btn("📊 إرسال تقرير الآن", "adm_send_report_now",       color="green")],
            [_btn("◀️ رجوع",             "adm_back",                  color="red")],
        ))


@bot.callback_query_handler(func=lambda c: c.data == "adm_toggle_daily_report")
def cb_adm_toggle_daily_report(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cur = db.get_config("daily_report_enabled", "1")
    db.set_config("daily_report_enabled", "0" if cur == "1" else "1")
    bot.answer_callback_query(call.id, "تم التبديل")
    cb_adm_alerts_settings(call)


@bot.callback_query_handler(func=lambda c: c.data == "adm_send_report_now")
def cb_adm_send_report_now(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    bot.answer_callback_query(call.id, "جارٍ الإرسال...")
    threading.Thread(target=send_daily_report, daemon=True).start()


@bot.callback_query_handler(func=lambda c: c.data == "adm_set_low_alert")
def cb_adm_set_low_alert(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    set_state(call.from_user.id, "adm_set_low_alert")
    edit(call,
        "<b>✏️ حد إشعار الرصيد المنخفض</b>\n\n"
        "أرسل الرقم (نقاط)، أو 0 لتعطيل الإشعار:",
        kb.back("adm_alerts_settings"))


def auto_update_orders():
    while True:
        time.sleep(180)
        try:
            conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
            conn.row_factory = _dict_row_factory
            orders = conn.execute(
                "SELECT * FROM orders WHERE status IN ('pending','inprogress') AND pending_approval=0 AND api_order_id IS NOT NULL AND api_order_id != ''"
            ).fetchall()
            conn.close()
            for o in orders:
                try:
                    site_id_val = o["site_id"] if "site_id" in o.keys() else None
                    r = smm.get_status(o["api_order_id"], site_id_val)
                    new_s = r.get("status", "").lower()
                    if not new_s or new_s == o["status"]:
                        continue
                    db.update_order(o["id"], new_s)
                    if new_s in ("completed", "partial", "canceled"):
                        notified = o["notified_done"] if "notified_done" in o.keys() else 0
                        if notified:
                            continue
                        try:
                            if new_s == "completed":
                                txt = (f"<b>✅ تم اكتمال طلبك بنجاح!</b>\n\n"
                                       f"طلب <b>#{o['id']}</b>\n"
                                       f"{o['service_name']}\n"
                                       f"الكمية: {o['quantity']:,}\n\n"
                                       f"<i>شكراً لاستخدامك {config.BOT_NAME}</i>")
                            elif new_s == "partial":
                                txt = (f"<b>⚠️ طلبك مكتمل جزئياً</b>\n\n"
                                       f"طلب #{o['id']} — {o['service_name']}")
                            else:
                                txt = (f"<b>❌ تم إلغاء طلبك</b>\n\n"
                                       f"طلب #{o['id']}\n<i>تواصل مع الدعم.</i>")
                            bot.send_message(o["user_id"], txt)
                            db.mark_notified(o["id"])
                        except Exception as notify_e:
                            print(f"[notify error] {notify_e}")
                except Exception as order_e:
                    print(f"[auto_update order error] {order_e}")
        except Exception as e:
            print(f"[auto_update error] {e}")


# ══════════════════════════════════════════════════════════════════
#   15. تشغيل
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print(f"🔥 {config.BOT_NAME} V6 يعمل الآن...")
    print("✨ ميزات: متجر مستقل | موافقة أدمن | كوبونات | ليدربورد | تقرير يومي | تنبيه رصيد")
    print("📌 يتطلب: pyTelegramBotAPI >= 4.32")
    threading.Thread(target=auto_update_orders, daemon=True).start()
    threading.Thread(target=daily_report_loop,  daemon=True).start()
    bot.infinity_polling(timeout=60, long_polling_timeout=30, allowed_updates=["message", "callback_query"])
