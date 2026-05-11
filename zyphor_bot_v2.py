import telebot
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ══════════════════════════════════════════════════════════════
BOT_TOKEN = "8668659853:AAHDbKhbDZOKaPaT0aOsSyIUyxVMD-CcAfY"
SITE_URL  = "https://hasnen.infinityfreeapp.com"
API_KEY   = "ZYPHOR_SECRET_KEY"
HEADERS   = {"X-API-KEY": API_KEY}
# ══════════════════════════════════════════════════════════════

bot = telebot.TeleBot(BOT_TOKEN)

# انتظار إدخال من المستخدم
waiting = {}  # {chat_id: "action"}

# ─── API ──────────────────────────────────────────────────────
def api(method, path, data=None):
    url = f"{SITE_URL}{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=HEADERS, timeout=8)
        else:
            r = requests.post(url, headers=HEADERS, data=data, timeout=8)
        return r.json() if r.ok else None
    except:
        return None

def get_user(chat_id):
    return api("GET", f"/api/user/{chat_id}")

def role_name(level):
    return {"1": "👑 Owner", "2": "🛡️ Admin", "3": "💼 Reseller"}.get(str(level), "—")

# ─── أزرار اختيار الرتبة ──────────────────────────────────────
def role_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("👑  Owner",   callback_data="verify_1"),
        InlineKeyboardButton("🛡️  Admin",   callback_data="verify_2"),
        InlineKeyboardButton("💼  Reseller", callback_data="verify_3"),
    )
    return kb

# ─── لوحة Owner ───────────────────────────────────────────────
def owner_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("👥 المستخدمين",  callback_data="users_list"),
        InlineKeyboardButton("📊 الإحصائيات", callback_data="stats"),
        InlineKeyboardButton("💰 إضافة رصيد", callback_data="add_bal"),
        InlineKeyboardButton("➖ خصم رصيد",   callback_data="deduct_bal"),
        InlineKeyboardButton("🎟️ Referral",    callback_data="create_ref"),
        InlineKeyboardButton("🔑 الأكواد",     callback_data="keys"),
        InlineKeyboardButton("🗑️ حذف منتهية",  callback_data="del_expired"),
        InlineKeyboardButton("📢 بث",          callback_data="broadcast"),
    )
    kb.add(InlineKeyboardButton("🔄 تحديث", callback_data="refresh"))
    return kb

# ─── لوحة Admin ───────────────────────────────────────────────
def admin_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("👥 مستخدميّ",   callback_data="users_list"),
        InlineKeyboardButton("📊 إحصائياتي", callback_data="stats"),
        InlineKeyboardButton("💰 إضافة رصيد", callback_data="add_bal"),
        InlineKeyboardButton("🎟️ Referral",    callback_data="create_ref"),
        InlineKeyboardButton("🔑 الأكواد",     callback_data="keys"),
    )
    kb.add(InlineKeyboardButton("🔄 تحديث", callback_data="refresh"))
    return kb

# ─── لوحة Reseller ────────────────────────────────────────────
def reseller_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔑 أكوادي",      callback_data="keys"),
        InlineKeyboardButton("💎 رصيدي",       callback_data="my_bal"),
        InlineKeyboardButton("ℹ️ معلوماتي",    callback_data="my_info"),
        InlineKeyboardButton("🗑️ حذف منتهية",  callback_data="del_expired"),
    )
    kb.add(InlineKeyboardButton("🔄 تحديث", callback_data="refresh"))
    return kb

def back_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("◀️ رجوع", callback_data="refresh"))
    return kb

def panel_kb(level):
    return {"1": owner_kb, "2": admin_kb, "3": reseller_kb}.get(str(level), reseller_kb)()

# ══════════════════════════════════════════════════════════════
# /start
# ══════════════════════════════════════════════════════════════
@bot.message_handler(commands=["start"])
def start(msg):
    cid = str(msg.chat.id)
    res = get_user(cid)

    if res and res.get("user"):
        u = res["user"]
        send_panel(msg.chat.id, u)
    else:
        bot.send_message(
            msg.chat.id,
            f"👋 مرحباً!\n\nاختر رتبتك:",
            reply_markup=role_keyboard()
        )

def send_panel(chat_id, user):
    level = str(user.get("level", 3))
    name  = user.get("username", "—")
    saldo = user.get("saldo", 0)
    role  = role_name(level)

    bot.send_message(
        chat_id,
        f"✅ <b>{name}</b> | {role}\n💎 الرصيد: <b>{saldo}</b>",
        parse_mode="HTML",
        reply_markup=panel_kb(level)
    )

# ══════════════════════════════════════════════════════════════
# Callbacks
# ══════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    try:
        cid  = str(c.from_user.id)
        data = c.data
        mid  = c.message.message_id
        chat = c.message.chat.id

    # ── التحقق من الرتبة ──────────────────────────────────
    if data.startswith("verify_"):
        chosen_level = data.split("_")[1]
        res = get_user(cid)

        if not res or not res.get("user"):
            bot.answer_callback_query(c.id, "❌ Chat ID غير مسجل في الموقع.", show_alert=True)
            return

        user  = res["user"]
        level = str(user.get("level", 3))

        if level != chosen_level:
            labels = {"1": "Owner", "2": "Admin", "3": "Reseller"}
            bot.answer_callback_query(c.id, f"❌ رتبتك الفعلية: {labels.get(level,'—')}", show_alert=True)
            return

        bot.answer_callback_query(c.id, "✅ تم التحقق!")
        bot.edit_message_text(
            f"✅ <b>{user['username']}</b> | {role_name(level)}\n💎 الرصيد: <b>{user['saldo']}</b>",
            chat, mid,
            parse_mode="HTML",
            reply_markup=panel_kb(level)
        )
        return

    # ── جلب المستخدم الحالي ───────────────────────────────
    res = get_user(cid)
    if not res or not res.get("user"):
        bot.answer_callback_query(c.id, "❌ غير مسجل.", show_alert=True)
        return

    user  = res["user"]
    level = str(user.get("level", 3))
    name  = user.get("username", "—")
    saldo = user.get("saldo", 0)

    # ── تحديث / رجوع ──────────────────────────────────────
    if data == "refresh":
        bot.answer_callback_query(c.id)
        bot.edit_message_text(
            f"✅ <b>{name}</b> | {role_name(level)}\n💎 الرصيد: <b>{saldo}</b>",
            chat, mid,
            parse_mode="HTML",
            reply_markup=panel_kb(level)
        )
        return

    # ── معلوماتي ──────────────────────────────────────────
    if data == "my_info":
        bot.answer_callback_query(c.id)
        bot.edit_message_text(
            f"ℹ️ <b>معلوماتك</b>\n\n"
            f"👤 {user.get('username','—')}\n"
            f"🏷️ {role_name(level)}\n"
            f"💎 {saldo}\n"
            f"📅 {user.get('expiration_date','—')}",
            chat, mid, parse_mode="HTML", reply_markup=back_kb()
        )

    # ── رصيدي ─────────────────────────────────────────────
    elif data == "my_bal":
        bot.answer_callback_query(c.id)
        bot.edit_message_text(
            f"💎 رصيدك: <b>{saldo}</b>",
            chat, mid, parse_mode="HTML", reply_markup=back_kb()
        )

    # ── الإحصائيات ────────────────────────────────────────
    elif data == "stats":
        if level not in ("1", "2"):
            bot.answer_callback_query(c.id, "❌ ليس لديك صلاحية.", show_alert=True)
            return
        bot.answer_callback_query(c.id)
        r = api("GET", "/api/stats")
        if r and r.get("status"):
            txt = (
                f"📊 <b>الإحصائيات</b>\n\n"
                f"👥 المستخدمون: {r['total_users']}\n"
                f"👑 Owner: {r['owners']}\n"
                f"🛡️ Admin: {r['admins']}\n"
                f"💼 Reseller: {r['resellers']}\n"
                f"🔑 كل الأكواد: {r['total_keys']}\n"
                f"✅ فعّالة: {r['active_keys']}\n"
                f"❌ منتهية: {r['expired_keys']}"
            )
        else:
            txt = "⚠️ تعذّر جلب الإحصائيات."
        bot.edit_message_text(txt, chat, mid, parse_mode="HTML", reply_markup=back_kb())

    # ── قائمة المستخدمين ──────────────────────────────────
    elif data == "users_list":
        if level not in ("1", "2"):
            bot.answer_callback_query(c.id, "❌ ليس لديك صلاحية.", show_alert=True)
            return
        bot.answer_callback_query(c.id)
        params = "" if level == "1" else f"?uplink={name}"
        r = api("GET", f"/api/users{params}")
        if r and r.get("users"):
            lines = []
            for u in r["users"][:10]:
                lines.append(f"• <b>{u['username']}</b> {role_name(u['level'])} 💎{u['saldo']}")
            txt = "👥 <b>المستخدمون</b>\n\n" + "\n".join(lines)
        else:
            txt = "👥 لا يوجد مستخدمون."
        bot.edit_message_text(txt, chat, mid, parse_mode="HTML", reply_markup=back_kb())

    # ── الأكواد ───────────────────────────────────────────
    elif data == "keys":
        bot.answer_callback_query(c.id)
        r = api("GET", f"/api/keys?chat_id={cid}")
        if r and r.get("keys"):
            lines = []
            for k in r["keys"][:8]:
                status = "✅" if k.get("expired_date") and k["expired_date"] > str(__import__('datetime').datetime.now()) else "❌"
                lines.append(f"{status} <code>{k['user_key']}</code> | {k['duration']}h | {k['max_devices']}📱")
            txt = "🔑 <b>الأكواد</b>\n\n" + "\n".join(lines)
        else:
            txt = "🔑 لا توجد أكواد."
        bot.edit_message_text(txt, chat, mid, parse_mode="HTML", reply_markup=back_kb())

    # ── إضافة رصيد ────────────────────────────────────────
    elif data == "add_bal":
        if level not in ("1", "2"):
            bot.answer_callback_query(c.id, "❌ ليس لديك صلاحية.", show_alert=True)
            return
        bot.answer_callback_query(c.id)
        waiting[cid] = "add_bal"
        bot.edit_message_text(
            "💰 أرسل:\n<code>username المبلغ</code>\n\nمثال: <code>Ahmad 500</code>",
            chat, mid, parse_mode="HTML", reply_markup=back_kb()
        )

    # ── خصم رصيد ──────────────────────────────────────────
    elif data == "deduct_bal":
        if level != "1":
            bot.answer_callback_query(c.id, "❌ Owner فقط.", show_alert=True)
            return
        bot.answer_callback_query(c.id)
        waiting[cid] = "deduct_bal"
        bot.edit_message_text(
            "➖ أرسل:\n<code>username المبلغ</code>\n\nمثال: <code>Ahmad 200</code>",
            chat, mid, parse_mode="HTML", reply_markup=back_kb()
        )

    # ── إنشاء Referral ────────────────────────────────────
    elif data == "create_ref":
        if level not in ("1", "2"):
            bot.answer_callback_query(c.id, "❌ ليس لديك صلاحية.", show_alert=True)
            return
        bot.answer_callback_query(c.id)
        waiting[cid] = "create_ref"
        note = "الرتب: 2=Admin، 3=Reseller\n" if level == "1" else "سيتم إنشاؤه لـ Reseller تلقائياً\n"
        bot.edit_message_text(
            f"🎟️ أرسل:\n<code>رصيد أيام رتبة</code>\n\n{note}مثال: <code>1000 30 3</code>",
            chat, mid, parse_mode="HTML", reply_markup=back_kb()
        )

    # ── حذف الأكواد المنتهية ──────────────────────────────
    elif data == "del_expired":
        bot.answer_callback_query(c.id)
        r = api("POST", "/api/keys/delete-expired", {"chat_id": cid})
        if r and r.get("status"):
            txt = f"🗑️ تم حذف <b>{r['deleted']}</b> كود منتهي."
        else:
            txt = "⚠️ تعذّر الحذف."
        bot.edit_message_text(txt, chat, mid, parse_mode="HTML", reply_markup=back_kb())

    # ── بث ────────────────────────────────────────────────
    elif data == "broadcast":
        if level != "1":
            bot.answer_callback_query(c.id, "❌ Owner فقط.", show_alert=True)
            return
        bot.answer_callback_query(c.id)
        waiting[cid] = "broadcast"
        bot.edit_message_text(
            "📢 أرسل نص البث:",
            chat, mid, parse_mode="HTML", reply_markup=back_kb()
        )

# ══════════════════════════════════════════════════════════════
# معالجة الردود النصية
# ══════════════════════════════════════════════════════════════
@bot.message_handler(func=lambda m: True)
def handle_text(msg):
    cid    = str(msg.chat.id)
    text   = msg.text.strip()
    action = waiting.pop(cid, None)

    if not action:
        bot.send_message(msg.chat.id, "استخدم /start")
        return

    # ── إضافة رصيد ────────────────────────────────────────
    if action == "add_bal":
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            bot.send_message(msg.chat.id, "❌ الصيغة: username المبلغ")
            return
        r = api("POST", "/api/balance/add", {"username": parts[0], "amount": parts[1]})
        if r and r.get("status"):
            bot.send_message(msg.chat.id, f"✅ تم إضافة {parts[1]} 💎 لـ {parts[0]}\nالرصيد الجديد: {r['new_balance']}")
        else:
            bot.send_message(msg.chat.id, "❌ فشل — تحقق من اليوزر.")

    # ── خصم رصيد ──────────────────────────────────────────
    elif action == "deduct_bal":
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            bot.send_message(msg.chat.id, "❌ الصيغة: username المبلغ")
            return
        r = api("POST", "/api/balance/deduct", {"username": parts[0], "amount": parts[1]})
        if r and r.get("status"):
            bot.send_message(msg.chat.id, f"✅ تم خصم {parts[1]} 💎 من {parts[0]}\nالرصيد الجديد: {r['new_balance']}")
        else:
            bot.send_message(msg.chat.id, "❌ فشل — رصيد غير كافٍ أو اليوزر غير موجود.")

    # ── إنشاء Referral ────────────────────────────────────
    elif action == "create_ref":
        parts = text.split()
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            bot.send_message(msg.chat.id, "❌ الصيغة: رصيد أيام رتبة\nمثال: 1000 30 3")
            return
        r = api("POST", "/api/referral/create", {
            "chat_id": cid,
            "saldo":   parts[0],
            "days":    parts[1],
            "level":   parts[2],
        })
        if r and r.get("status"):
            bot.send_message(
                msg.chat.id,
                f"✅ <b>تم إنشاء الـ Referral</b>\n\n"
                f"🔑 الكود: <code>{r['code']}</code>\n"
                f"🏷️ الرتبة: {r['level']}\n"
                f"💎 الرصيد: {r['saldo']}\n"
                f"📅 ينتهي: {r['expires']}",
                parse_mode="HTML"
            )
        else:
            bot.send_message(msg.chat.id, "❌ فشل إنشاء الكود.")

    # ── بث ────────────────────────────────────────────────
    elif action == "broadcast":
        r = api("POST", "/api/broadcast", {"chat_id": cid, "text": text})
        if r and r.get("status"):
            bot.send_message(msg.chat.id, f"📢 تم الإرسال لـ {r['sent']} مستخدم.")
        else:
            bot.send_message(msg.chat.id, "❌ فشل الإرسال.")


print("✅ Zyphor Bot Started...")
bot.infinity_polling()
