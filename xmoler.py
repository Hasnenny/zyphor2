import logging
import asyncio
import os
import random
import string
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, 
    filters, ContextTypes
)
from telegram.error import Forbidden
from pyrogram import Client, filters as pyro_filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserNotParticipant, SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

SESSION_DIR = os.path.join(os.getcwd(), "sessions")
os.makedirs(SESSION_DIR, exist_ok=True)

DATA_FILE = "bot_data.json"

BOT_TOKEN = "8391310204:AAGDnpQAWV5hYNxdawU7Y_3XBk7MJJJQTVY"
OWNER_ID = 8412516908
DEVELOPER_USER = "@Y0YY22"
SOURCE_CHANNEL = "R_TREND1"

API_ID = 26485249
API_HASH = "4aa1d4242392856942c84ad91e81944f"

PM_CONVERSATIONS = {}

LANGUAGES = {
    "ar": {
        "start": "مرحباً بك",
        "home": "القائمة الرئيسية",
        "add_account": "➕ إضافة حساب",
        "groups": "📋 المجموعات",
        "accounts": "👤 الحسابات",
        "messages": "✉️ الرسائل",
        "free_sub": "🆓 اشتراك مجاني",
        "paid_sub": "💎 اشتراك مدفوع",
        "guide": "📖 دليل الاستخدام",
        "settings": "⚙️ الإعدادات",
        "language": "🌐 اللغة",
        "back": "🔙 رجوع",
        "admin_panel": "👑 لوحة التحكم",
        "statistics": "📊 الإحصائيات",
        "broadcast": "📢 إذاعة",
        "force_channels": "🔗 قنوات الاشتراك",
        "ban_user": "🚫 حظر مستخدم",
        "unban_user": "✅ فك حظر",
        "stop_bot": "⏸️ إيقاف البوت",
        "start_bot": "▶️ تشغيل البوت"
    },
    "en": {
        "start": "Welcome",
        "home": "Main Menu",
        "add_account": "➕ Add Account",
        "groups": "📋 Groups",
        "accounts": "👤 Accounts",
        "messages": "✉️ Messages",
        "free_sub": "🆓 Free Subscription",
        "paid_sub": "💎 Paid Subscription",
        "guide": "📖 User Guide",
        "settings": "⚙️ Settings",
        "language": "🌐 Language",
        "back": "🔙 Back",
        "admin_panel": "👑 Admin Panel",
        "statistics": "📊 Statistics",
        "broadcast": "📢 Broadcast",
        "force_channels": "🔗 Subscription Channels",
        "ban_user": "🚫 Ban User",
        "unban_user": "✅ Unban User",
        "stop_bot": "⏸️ Stop Bot",
        "start_bot": "▶️ Start Bot"
    },
    "zh": {
        "start": "欢迎",
        "home": "主菜单",
        "add_account": "➕ 添加账户",
        "groups": "📋 群组",
        "accounts": "👤 账户",
        "messages": "✉️ 消息",
        "free_sub": "🆓 免费订阅",
        "paid_sub": "💎 付费订阅",
        "guide": "📖 使用指南",
        "settings": "⚙️ 设置",
        "language": "🌐 语言",
        "back": "🔙 返回",
        "admin_panel": "👑 管理面板",
        "statistics": "📊 统计",
        "broadcast": "📢 广播",
        "force_channels": "🔗 订阅频道",
        "ban_user": "🚫 封禁用户",
        "unban_user": "✅ 解封用户",
        "stop_bot": "⏸️ 停止机器人",
        "start_bot": "▶️ 启动机器人"
    },
    "fr": {
        "start": "Bienvenue",
        "home": "Menu Principal",
        "add_account": "➕ Ajouter un Compte",
        "groups": "📋 Groupes",
        "accounts": "👤 Comptes",
        "messages": "✉️ Messages",
        "free_sub": "🆓 Abonnement Gratuit",
        "paid_sub": "💎 Abonnement Payant",
        "guide": "📖 Guide d'Utilisation",
        "settings": "⚙️ Paramètres",
        "language": "🌐 Langue",
        "back": "🔙 Retour",
        "admin_panel": "👑 Panneau d'Administration",
        "statistics": "📊 Statistiques",
        "broadcast": "📢 Diffusion",
        "force_channels": "🔗 Chaînes d'Abonnement",
        "ban_user": "🚫 Bannir Utilisateur",
        "unban_user": "✅ Débannir Utilisateur",
        "stop_bot": "⏸️ Arrêter le Bot",
        "start_bot": "▶️ Démarrer le Bot"
    }
}

GUIDE_TEXT = """📖 دليل الاستخدام 🆓

أهلاً بك في PostMaster! البوت مجاني بالكامل ومفتوح لجميع المستخدمين بدون أي قيود:
🔹 الحسابات: عدد غير محدود من الحسابات.
🔹 المجموعات: عدد غير محدود من المجموعات.
🔹 الرسائل: عدد غير محدود من الكلايش بأي طول.
🔹 النشر: غير محدود.

🚀 كيف تبدأ فوراً؟
1️⃣ أضف حسابك 👈 2️⃣ أضف مجموعتك 👈 3️⃣ أضف رسالتك 👈 4️⃣ اضغط (🟢 بدء النشر التلقائي)!"""

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                for uid, udata in data.get("users", {}).items():
                    udata.pop("sub_expire", None)
                    udata.pop("vip", None)
                    udata.pop("daily_posts", None)
                    udata.pop("daily_date", None)
                    if "texts" not in udata:
                        old_text = udata.get("text", "")
                        udata["texts"] = [old_text] if old_text else []
                    if "pm_reply_text" not in udata:
                        udata["pm_reply_text"] = "صاحب الحساب مشغول حالياً، أترك رسالتك وسيتم الرد عليك فور تفرغه."
                    if "pm_auto_reply_enabled" not in udata:
                        udata["pm_auto_reply_enabled"] = False
                    if "night_mode_enabled" not in udata:
                        udata["night_mode_enabled"] = False
                    if "night_start" not in udata:
                        udata["night_start"] = None
                    if "night_end" not in udata:
                        udata["night_end"] = None
                    if "lang" not in udata:
                        udata["lang"] = "ar"

                ready_groups = data.get("ready_groups", {"super": [], "exchange": [], "other": []})
                custom_start_msg = data.get("custom_start_msg", None)
                banned = data.get("banned_users", [])
                bot_running = data.get("bot_running", True)
                stop_message = data.get("stop_message", "")
                
                return (
                    data.get("users", {}), data.get("admins", [OWNER_ID]), 
                    data.get("channels", []), ready_groups, custom_start_msg, banned, bot_running, stop_message
                )
            except Exception as e:
                logging.error(f"Error loading data: {e}")
    return {}, [OWNER_ID], [], {"super": [], "exchange": [], "other": []}, None, [], True, ""

def save_data():
    data = {
        "users": USERS_DATA,
        "admins": ADMINS,
        "channels": REQUIRED_CHANNELS,
        "ready_groups": READY_GROUPS,
        "custom_start_msg": CUSTOM_START_MSG,
        "banned_users": BANNED_USERS,
        "bot_running": BOT_RUNNING,
        "stop_message": STOP_MESSAGE
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

(USERS_DATA, ADMINS, REQUIRED_CHANNELS, 
 READY_GROUPS, CUSTOM_START_MSG, BANNED_USERS, BOT_RUNNING, STOP_MESSAGE) = load_data()

if OWNER_ID not in ADMINS:
    ADMINS.append(OWNER_ID)
    save_data()

PYRO_SESSIONS = {}
ACTIVE_CLIENTS = {}
ADMIN_LINK_REQUESTS = {}

async def safe_send_message(context: ContextTypes.DEFAULT_TYPE, user_id: int, text: str, parse_mode: str = None, reply_markup=None):
    try:
        return await context.bot.send_message(chat_id=user_id, text=text, parse_mode=parse_mode, reply_markup=reply_markup)
    except Forbidden:
        return None
    except Exception as e:
        logging.error(f"Error sending message to {user_id}: {e}")
        return None

def get_lang(user_id):
    return USERS_DATA.get(str(user_id), {}).get("lang", "ar")

def L(user_id, key):
    lang = get_lang(user_id)
    return LANGUAGES.get(lang, LANGUAGES["ar"]).get(key, key)

async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id):
    if not REQUIRED_CHANNELS or int(user_id) in ADMINS:
        return True
    
    unsubscribed = []
    for ch in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status not in ['member', 'creator', 'administrator']:
                unsubscribed.append(ch)
        except Exception:
            unsubscribed.append(ch)
            
    if not unsubscribed:
        return True
        
    keyboard = []
    for idx, ch in enumerate(unsubscribed, start=1):
        clean_ch = ch.replace('https://t.me/', '').replace('t.me/', '').replace('@', '')
        keyboard.append([InlineKeyboardButton(f"« اشترك في القناة {idx} »", url=f"https://t.me/{clean_ch}")])
    keyboard.append([InlineKeyboardButton("« تحقق من الاشتراك »", callback_data="check_join")])
    
    msg = "**يجب عليك الاشتراك في قنوات البوت أولاً لاستخدامه!**"
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    return False

def get_lang_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    ], [
        InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh"),
        InlineKeyboardButton("🇫🇷 Français", callback_data="lang_fr")
    ]])

def get_main_keyboard(user_id):
    user = USERS_DATA.get(str(user_id), {})
    is_running = user.get('is_running', False)
    night_active = user.get('night_mode_enabled', False)

    keyboard = [
        [InlineKeyboardButton("« رد الكروبات »", callback_data="auto_reply_group_menu"),
         InlineKeyboardButton("« رد الخاص »", callback_data="auto_reply_pm_menu")],
        [InlineKeyboardButton("« إدارة الحسابات »", callback_data="manage_accs"),
         InlineKeyboardButton("« الإحصائيات »", callback_data="stats")],
        [InlineKeyboardButton("« تعديل الوقت »", callback_data="edit_time")],
        [InlineKeyboardButton("« إدارة الكلايش »", callback_data="manage_texts_menu")],
        [InlineKeyboardButton("« إدارة الكروبات »", callback_data="manage_groups_menu"),
         InlineKeyboardButton("« كروبات جاهزة »", callback_data="ready_groups_menu")],
        [InlineKeyboardButton("« بدء النشر »" if not is_running else "« النشر يعمل حالياً »", callback_data="start_post"),
         InlineKeyboardButton("« توقيف النشر »", callback_data="stop_post")],
        [InlineKeyboardButton("« وضع راحة الليلية 🌙 »" if not night_active else "« وضع الراحة (مُفعل) 🌙 »", callback_data="night_sleep_mode")],
        [InlineKeyboardButton("« دليل الاستخدام »", callback_data="userGuide")],
        [InlineKeyboardButton("« المطور »", url=f"https://t.me/{DEVELOPER_USER.replace('@','')}"),
         InlineKeyboardButton("« قناة السورس »", url=f"https://t.me/{SOURCE_CHANNEL.replace('@','')}")],
    ]
    if int(user_id) in ADMINS:
        keyboard.append([InlineKeyboardButton("« لوحة التحكم »", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)

def get_pm_reply_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("« تفعيل الرد الخاص »", callback_data="enable_pm_reply"),
         InlineKeyboardButton("« تعطيل الرد الخاص »", callback_data="disable_pm_reply")],
        [InlineKeyboardButton("« تعديل كليشة رد الخاص »", callback_data="edit_pm_reply_text")],
        [InlineKeyboardButton("« إذاعة في الخاص »", callback_data="user_pm_broadcast")],
        [InlineKeyboardButton("« رجوع لقائمة الرئيسية »", callback_data="back_main")]
    ])

def get_texts_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("« إضافة كليشة جديدة »", callback_data="add_text")],
        [InlineKeyboardButton("« عرض وتصدير الكلايش »", callback_data="view_texts")],
        [InlineKeyboardButton("« مسح جميع الكلايش »", callback_data="clear_all_texts")],
        [InlineKeyboardButton("« رجوع »", callback_data="back_main")]
    ])

def get_groups_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("« إضافة كروب يدوي »", callback_data="add_group_manual")],
        [InlineKeyboardButton("« جلب كروبات الحساب »", callback_data="list_account_groups_0")],
        [InlineKeyboardButton("« كروبات جاهزة »", callback_data="ready_groups_menu")],
        [InlineKeyboardButton("« عرض المجموعات المضافة »", callback_data="view_groups")],
        [InlineKeyboardButton("« مسح جميع المجموعات »", callback_data="clear_all_groups")],
        [InlineKeyboardButton("« رجوع »", callback_data="back_main")]
    ])

def get_ready_groups_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("« كروبات السوبر »", callback_data="view_ready_cat_super")],
        [InlineKeyboardButton("« كروبات التبادل »", callback_data="view_ready_cat_exchange")],
        [InlineKeyboardButton("« كروبات اخرى »", callback_data="view_ready_cat_other")],
        [InlineKeyboardButton("« رجوع »", callback_data="back_main")]
    ])

def get_admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="statics"), InlineKeyboardButton("📢 إذاعة", callback_data="broadcast")],
        [InlineKeyboardButton("🔗 قنوات الاشتراك", callback_data="channels")],
        [InlineKeyboardButton("🚫 حظر مستخدم", callback_data="banUser"), InlineKeyboardButton("✅ فك حظر", callback_data="unbanUser")],
        [InlineKeyboardButton("⏸️ إيقاف البوت", callback_data="stopBot"), InlineKeyboardButton("▶️ تشغيل البوت", callback_data="startBot")],
        [InlineKeyboardButton("➕ انضمام", callback_data="adm_join_accounts"), InlineKeyboardButton("📢 نشر في كروب", callback_data="adm_post_group")],
        [InlineKeyboardButton("📝 رسالة /start", callback_data="adm_start_msg_menu")],
        [InlineKeyboardButton("👥 الأدمنية", callback_data="adm_admins_menu")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ])

def get_admin_sub_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("« إضافة قناة »", callback_data="ch_add")],
        [InlineKeyboardButton("« حذف قناة »", callback_data="ch_del")],
        [InlineKeyboardButton("« عرض القنوات »", callback_data="ch_view")],
        [InlineKeyboardButton("« رجوع »", callback_data="admin_panel")]
    ])

def get_admin_manage_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("« إضافة أدمن »", callback_data="admin_add")],
        [InlineKeyboardButton("« مسح أدمن »", callback_data="admin_del")],
        [InlineKeyboardButton("« عرض الأدمنية »", callback_data="admin_view")],
        [InlineKeyboardButton("« رجوع »", callback_data="admin_panel")]
    ])

def register_session_reply_handler(client: Client, user_id: str):
    @client.on_message(pyro_filters.group & pyro_filters.reply)
    async def session_auto_reply_handler(bot_client: Client, message: Message):
        try:
            me = await bot_client.get_me()
            if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == me.id:
                user_data = USERS_DATA.get(str(user_id), {})
                auto_replies = user_data.get('auto_replies', {})
                msg_text = message.text.strip() if message.text else ""
                replied_post_text = message.reply_to_message.text or ""
                
                matched = False
                for key, data in auto_replies.items():
                    if msg_text == key or key == "*":
                        target_text_idx = data.get("text_index", "all")
                        if target_text_idx != "all":
                            try:
                                target_idx = int(target_text_idx)
                                user_texts = user_data.get('texts', [])
                                if 0 <= target_idx < len(user_texts):
                                    if user_texts[target_idx] not in replied_post_text:
                                        continue
                            except ValueError:
                                pass
                        
                        reply_content = data.get("reply", "")
                        if reply_content:
                            await message.reply_text(reply_content)
                            matched = True
                            break
                
                if not matched and "*" in auto_replies:
                    default_reply = auto_replies["*"].get("reply", "")
                    if default_reply:
                        await message.reply_text(default_reply)
        except Exception as e:
            logging.error(f"Error in group auto reply: {e}")

    @client.on_message(pyro_filters.private & ~pyro_filters.me)
    async def session_pm_auto_reply_handler(bot_client: Client, message: Message):
        try:
            if not message.from_user or message.from_user.is_bot:
                return

            user_data = USERS_DATA.get(str(user_id), {})
            if not user_data.get('pm_auto_reply_enabled', False):
                return
                
            pm_text = user_data.get('pm_reply_text', 'صاحب الحساب مشغول حالياً، أترك رسالتك وسيتم الرد عليك فور تفرغه.')
            target_user_id = message.from_user.id
            key = f"{user_id}_{target_user_id}"
            now = datetime.now()

            if key not in PM_CONVERSATIONS:
                if pm_text:
                    await message.reply_text(pm_text)
                PM_CONVERSATIONS[key] = {
                    'start_time': now,
                    'first_reply_sent': True,
                    'three_min_alert_sent': False
                }
            else:
                conv = PM_CONVERSATIONS[key]
                if not conv['three_min_alert_sent']:
                    if now - conv['start_time'] >= timedelta(minutes=3):
                        await message.reply_text("شكراً لاستمرار تواصلك، أرجو الانتظار سيتم الرد عليك قريباً من صاحب الحساب.")
                        conv['three_min_alert_sent'] = True
        except Exception as e:
            logging.error(f"Error in PM auto reply handler: {e}")

async def start_user_clients(user_id: str):
    user = USERS_DATA.get(str(user_id), {})
    accounts = user.get('accounts', [])
    
    for acc in accounts:
        phone = str(acc['phone'])
        if phone not in ACTIVE_CLIENTS:
            session_path = os.path.join(SESSION_DIR, phone)
            client = Client(name=session_path, api_id=API_ID, api_hash=API_HASH)
            try:
                await client.start()
                register_session_reply_handler(client, str(user_id))
                ACTIVE_CLIENTS[phone] = client
            except Exception as e:
                logging.error(f"Error starting client for {phone}: {e}")

async def user_pm_broadcast_worker(user_id: str, broadcast_text: str, context: ContextTypes.DEFAULT_TYPE):
    user = USERS_DATA.get(str(user_id), {})
    accounts = user.get('accounts', [])
    
    if not accounts:
        await safe_send_message(context, int(user_id), "**لا توجد حسابات مضافة للقيام بالإذاعة في الخاص.**", parse_mode="Markdown")
        return

    await safe_send_message(context, int(user_id), "**جاري البدء بالإذاعة في المحادثات الخاصة للحسابات...**", parse_mode="Markdown")

    total_sent = 0
    total_failed = 0

    for acc in accounts:
        phone = str(acc['phone'])
        client = ACTIVE_CLIENTS.get(phone)
        
        if not client or not client.is_connected:
            session_path = os.path.join(SESSION_DIR, phone)
            client = Client(name=session_path, api_id=API_ID, api_hash=API_HASH)
            try:
                await client.start()
                register_session_reply_handler(client, str(user_id))
                ACTIVE_CLIENTS[phone] = client
            except Exception as e:
                logging.error(f"Failed to connect client {phone} for broadcast: {e}")
                continue

        try:
            async for dialog in client.get_dialogs():
                chat_type = str(dialog.chat.type).lower()
                if "private" in chat_type or "user" in chat_type:
                    if dialog.chat.is_self or dialog.chat.is_support:
                        continue
                    try:
                        await client.send_message(chat_id=dialog.chat.id, text=broadcast_text)
                        total_sent += 1
                        await asyncio.sleep(1.5)
                    except FloodWait as fw:
                        await asyncio.sleep(fw.value)
                        try:
                            await client.send_message(chat_id=dialog.chat.id, text=broadcast_text)
                            total_sent += 1
                        except:
                            total_failed += 1
                    except Exception:
                        total_failed += 1
        except Exception as e:
            logging.error(f"Broadcast error on account {phone}: {e}")

    await safe_send_message(
        context,
        int(user_id),
        f"**اكتمال الإذاعة في الخاص!**\n\n**الرسائل الناجحة:** `{total_sent}`\n**الرسائل الفاشلة:** `{total_failed}`",
        parse_mode="Markdown"
    )

async def posting_worker(user_id, context: ContextTypes.DEFAULT_TYPE):
    str_user_id = str(user_id)
    
    while True:
        user = USERS_DATA.get(str_user_id)
        if not user or not user.get('is_running', False):
            break

        if user.get('night_mode_enabled', False):
            now_hour = datetime.now().hour
            start_h = user.get('night_start')
            end_h = user.get('night_end')
            
            if start_h is not None and end_h is not None:
                is_night = False
                if start_h > end_h:
                    if now_hour >= start_h or now_hour < end_h:
                        is_night = True
                else:
                    if start_h <= now_hour < end_h:
                        is_night = True
                        
                if is_night:
                    await asyncio.sleep(60)
                    continue

        accounts = user.get('accounts', [])
        groups = user.get('groups', [])
        texts = user.get('texts', [])
        interval = user.get('interval', 30)

        if not accounts or not groups or not texts:
            user['is_running'] = False
            save_data()
            await safe_send_message(context, int(user_id), "**تم إيقاف النشر تلقائياً بسبب نقص البيانات.**", parse_mode="Markdown")
            break

        for acc in list(accounts):
            if not user.get('is_running', False):
                break

            phone = str(acc['phone'])
            client = ACTIVE_CLIENTS.get(phone)
            
            if not client or not client.is_connected:
                session_path = os.path.join(SESSION_DIR, phone)
                client = Client(name=session_path, api_id=API_ID, api_hash=API_HASH)
                try:
                    await client.start()
                    register_session_reply_handler(client, str_user_id)
                    ACTIVE_CLIENTS[phone] = client
                except Exception as e:
                    logging.error(f"Client connection error for {phone}: {e}")
                    continue

            try:
                for group in list(groups):
                    if not user.get('is_running', False):
                        break

                    target_chat = str(group).strip()
                    
                    if "t.me/+" in target_chat or "t.me/joinchat/" in target_chat:
                        try:
                            chat_obj = await client.join_chat(target_chat)
                            target_chat = chat_obj.id
                        except Exception:
                            continue
                    elif "t.me/" in target_chat:
                        target_chat = "@" + target_chat.split("t.me/")[1].replace("/", "")
                    elif target_chat.lstrip('-').isdigit():
                        target_chat = int(target_chat)

                    for text_to_send in texts:
                        if not user.get('is_running', False):
                            break
                        try:
                            await client.send_message(chat_id=target_chat, text=text_to_send)
                            await asyncio.sleep(1)
                        except FloodWait as fw:
                            await asyncio.sleep(fw.value)
                        except UserNotParticipant:
                            try:
                                await client.join_chat(target_chat)
                                await client.send_message(chat_id=target_chat, text=text_to_send)
                            except Exception:
                                pass
                        except Exception:
                            pass

            except Exception as e:
                logging.error(f"Posting error for {phone}: {e}")

        for _ in range(int(interval)):
            if not USERS_DATA.get(str_user_id, {}).get('is_running', False):
                break
            await asyncio.sleep(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    first_name = update.effective_user.first_name
    
    if not BOT_RUNNING and int(user_id) not in ADMINS:
        msg = STOP_MESSAGE if STOP_MESSAGE else "⚠️ البوت متوقف حالياً للصيانة، يرجى المحاولة لاحقاً."
        await update.message.reply_text(msg)
        return
    
    if user_id in BANNED_USERS:
        await update.message.reply_text("🚫 أنت محظور من استخدام البوت.")
        return
    
    if not await check_force_join(update, context, int(user_id)): return

    if user_id not in USERS_DATA:
        USERS_DATA[user_id] = {
            'lang': 'ar',
            'accounts': [], 'groups': [], 'texts': [], 'interval': 600, 
            'is_running': False, 'auto_replies': {},
            'pm_reply_text': "صاحب الحساب مشغول حالياً، أترك رسالتك وسيتم الرد عليك فور تفرغه.",
            'pm_auto_reply_enabled': False,
            'night_mode_enabled': False,
            'night_start': None,
            'night_end': None,
        }
        save_data()
        await update.message.reply_text("**الرجاء اختيار اللغة / Language:**", parse_mode="Markdown", reply_markup=get_lang_keyboard())
    else:
        USERS_DATA[user_id]['is_running'] = False
        asyncio.create_task(start_user_clients(user_id))
        await show_appropriate_menu(update, context, int(user_id))

async def show_appropriate_menu(update, context, user_id):
    msg = CUSTOM_START_MSG if CUSTOM_START_MSG else "**قائمة التحكم الرئيسية:**"
    p_mode = "HTML" if CUSTOM_START_MSG else "Markdown"
    if update.message: await update.message.reply_text(msg, parse_mode=p_mode, reply_markup=get_main_keyboard(user_id))
    elif update.callback_query: await update.callback_query.message.reply_text(msg, parse_mode=p_mode, reply_markup=get_main_keyboard(user_id))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global DEVELOPER_USER, SOURCE_CHANNEL, CUSTOM_START_MSG, BOT_RUNNING, STOP_MESSAGE
    query = update.callback_query
    
    try: await query.answer()
    except Exception: pass

    user_id = str(query.from_user.id)
    data = query.data

    if data == "check_join":
        subscribed = await check_force_join(update, context, int(user_id))
        if subscribed:
            await query.answer("✅ تم التحقق بنجاح!", show_alert=True)
            try: await query.message.delete()
            except Exception: pass
            await show_appropriate_menu(update, context, int(user_id))
        else:
            await query.answer("❌ لم تشترك في جميع القنوات بعد.", show_alert=True)
        return

    user = USERS_DATA.setdefault(user_id, {
        'lang': 'ar',
        'accounts': [], 'groups': [], 'texts': [], 'interval': 600, 
        'is_running': False, 'auto_replies': {},
        'pm_reply_text': "صاحب الحساب مشغول حالياً، أترك رسالتك وسيتم الرد عليك فور تفرغه.", 
        'pm_auto_reply_enabled': False,
        'night_mode_enabled': False,
        'night_start': None,
        'night_end': None,
    })

    if data.startswith("lang_"):
        user['lang'] = data.split("_")[1]
        save_data()
        await query.message.delete()
        await show_appropriate_menu(update, context, int(user_id))
        return

    if data in ["back_to_welcome", "back_main"]:
        context.user_data['action'] = None
        await query.message.delete()
        await show_appropriate_menu(update, context, int(user_id))
    elif data == "userGuide":
        await query.edit_message_text(GUIDE_TEXT, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]]), disable_web_page_preview=True)

    elif data == "settingsMenu":
        current_lang = get_lang(user_id)
        lang_names = {"ar": "🇸🇦 العربية", "en": "🇬🇧 English", "zh": "🇨🇳 中文", "fr": "🇫🇷 Français"}
        await query.edit_message_text(f"⚙️ الإعدادات\n\nاللغة الحالية: {lang_names.get(current_lang, 'العربية')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 تغيير اللغة", callback_data="changeLang")], [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]]))

    elif data == "changeLang":
        await query.edit_message_text("🌐 اختر لغتك:", reply_markup=get_lang_keyboard())

    elif data == "night_sleep_mode":
        has_acc = len(user.get('accounts', [])) > 0
        start_h = user.get('night_start')
        end_h = user.get('night_end')
        has_time = (start_h is not None) and (end_h is not None)
        
        status_txt = "معطل ❌" if not user.get('night_mode_enabled', False) else "شغال ✅"
        time_txt = f"من الساعة {start_h}:00 الى {end_h}:00" if has_time else "غير محدد"
        
        msg = f"🌙 **وضع الراحة الليلية**\n\n**حالة القسم:** {status_txt}\n**وقت التوقيف واستئناف:** {time_txt}"
        kb = [
            [InlineKeyboardButton("« تحديد وقت توقيف النشر »", callback_data="night_set_start")],
            [InlineKeyboardButton("« الوقت الذي يعود فيه النشر »", callback_data="night_set_end")],
            [InlineKeyboardButton("« تفعيل »" if not user.get('night_mode_enabled') else "« تعطيل »", callback_data="night_toggle")],
            [InlineKeyboardButton("« رجوع »", callback_data="back_main")]
        ]
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif data in ["night_set_start", "night_set_end"]:
        target = "start" if data == "night_set_start" else "end"
        title = "تحديد وقت توقيف النشر (بالساعة 0-23):" if target == "start" else "تحديد الوقت الذي يعود فيه النشر (بالساعة 0-23):"
        buttons = [InlineKeyboardButton(f"{h:02d}:00", callback_data=f"night_save_{target}_{h}") for h in range(24)]
        kb_grid = [buttons[i:i + 4] for i in range(0, len(buttons), 4)]
        kb_grid.append([InlineKeyboardButton("« رجوع »", callback_data="night_sleep_mode")])
        await query.edit_message_text(f"**{title}**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb_grid))

    elif data.startswith("night_save_"):
        parts = data.split("_")
        target = parts[2]
        hour = int(parts[3])
        if target == "start": user['night_start'] = hour
        else: user['night_end'] = hour
        save_data()
        await query.answer("تم حفظ التوقيت بنجاح!")
        await button_click(update, context)

    elif data == "night_toggle":
        if not user.get('accounts'):
            await query.answer("❌ يجب عليك إضافة حساب أولاً!", show_alert=True)
            return
        if user.get('night_start') is None or user.get('night_end') is None:
            await query.answer("❌ يرجى تحديد وقت التوقيف ووقت الاستئناف أولاً!", show_alert=True)
            return
        user['night_mode_enabled'] = not user.get('night_mode_enabled', False)
        save_data()
        await query.answer("تم التغيير بنجاح!", show_alert=True)
        await button_click(update, context)

    elif data == "admin_panel" and int(user_id) in ADMINS:
        await query.edit_message_text("**لوحة التحكم:**", parse_mode="Markdown", reply_markup=get_admin_keyboard())

    elif data == "adm_join_accounts" and int(user_id) in ADMINS:
        context.user_data['action'] = 'adm_join_link'
        await query.edit_message_text(
            "**أرسل رابط القناة أو الكروب.**\n\nسيتم إرسال طلب موافقة لكل مستخدم لديه حسابات مضافة، وعند موافقته تنضم حساباته المضافة إلى الرابط.",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« إلغاء »", callback_data="admin_panel")]])
        )

    elif data == "adm_post_group" and int(user_id) in ADMINS:
        context.user_data['action'] = 'adm_post_group_link'
        await query.edit_message_text(
            "**أرسل رابط الكروب.**\n\nسيتم إرسال طلب موافقة لكل مستخدم لديه حسابات مضافة، وعند موافقته تنضم حساباته إلى الكروب ويُفعّل النشر التلقائي فيه حسب إعداداته.",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« إلغاء »", callback_data="admin_panel")]])
        )

    elif data.startswith("adlnk_"):
        parts = data.split("_", 2)
        approve = parts[1] == "yes"
        req_id = parts[2]
        req = ADMIN_LINK_REQUESTS.get(req_id)
        if not req:
            await query.edit_message_text("**انتهت صلاحية هذا الطلب أو تم التعامل معه مسبقاً.**", parse_mode="Markdown")
            return
        if not approve:
            await query.edit_message_text("**تم رفض الطلب ولن يتم اتخاذ أي إجراء على حساباتك.**", parse_mode="Markdown")
            return
        accounts = user.get('accounts', [])
        if not accounts:
            await query.edit_message_text("**لا توجد حسابات مضافة لديك.**", parse_mode="Markdown")
            return
        await query.edit_message_text("**جاري تنفيذ الطلب على حساباتك، الرجاء الانتظار...**", parse_mode="Markdown")
        link = req['link']
        mode = req['mode']
        success = 0
        joined_target = None
        for acc in accounts:
            phone = str(acc['phone'])
            client = ACTIVE_CLIENTS.get(phone)
            if not client or not client.is_connected:
                session_path = os.path.join(SESSION_DIR, phone)
                client = Client(name=session_path, api_id=API_ID, api_hash=API_HASH)
                try:
                    await client.start()
                    register_session_reply_handler(client, user_id)
                    ACTIVE_CLIENTS[phone] = client
                except Exception:
                    continue
            try:
                chat_obj = await client.join_chat(link)
                joined_target = f"@{chat_obj.username}" if chat_obj.username else str(chat_obj.id)
                success += 1
            except Exception:
                try:
                    fallback = link
                    if "t.me/" in fallback and not ("t.me/+" in fallback or "t.me/joinchat/" in fallback):
                        fallback = "@" + fallback.split("t.me/")[1].replace("/", "")
                    joined_target = joined_target or fallback
                    success += 1
                except Exception:
                    pass
        if mode == "post" and joined_target and joined_target not in user.get('groups', []):
            user.setdefault('groups', []).append(joined_target)
        save_data()
        if success == 0:
            await query.edit_message_text("**تعذّر انضمام حساباتك إلى الرابط. تأكد من صحة الرابط.**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))
        elif mode == "post":
            confirm_msg = f"✅ **تم اضافة كروب جديد**\n**رابط الكروب:** {link}\n\nتم تفعيل النشر التلقائي فيه حسب اعداداتك الحالية للوقت."
            await query.edit_message_text(confirm_msg, parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))
        else:
            await query.edit_message_text(f"✅ **تم انضمام حساباتك ({success}) إلى الرابط بنجاح:**\n{link}", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))

    elif data == "adm_start_msg_menu" and int(user_id) in ADMINS:
        curr_msg = CUSTOM_START_MSG if CUSTOM_START_MSG else "النص الافتراضي"
        kb = [[InlineKeyboardButton("« تعيين نص جديد لـ /start »", callback_data="adm_set_start_msg")], [InlineKeyboardButton("« إعادة النص الافتراضي »", callback_data="adm_reset_start_msg")], [InlineKeyboardButton("« رجوع »", callback_data="admin_panel")]]
        await query.edit_message_text(f"**إعدادات رسالة /start:**\n\n**النص الحالي:**\n{curr_msg}", parse_mode="HTML" if CUSTOM_START_MSG else "Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "adm_set_start_msg" and int(user_id) in ADMINS:
        await query.edit_message_text("**أرسل نص رسالة /start الجديد:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« إلغاء »", callback_data="adm_start_msg_menu")]]))
        context.user_data['action'] = 'adm_waiting_start_text'

    elif data == "adm_reset_start_msg" and int(user_id) in ADMINS:
        CUSTOM_START_MSG = None
        save_data()
        await query.answer("تم إعادة رسالة /start للوضع الافتراضي", show_alert=True)
        await query.edit_message_text("**تم ضبط النص الافتراضي بنجاح!**", parse_mode="Markdown", reply_markup=get_admin_keyboard())

    elif data == "broadcast" and int(user_id) in ADMINS:
        await query.edit_message_text("**أرسل النشرة المراد إرسالها لكافة المستخدمين:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« إلغاء »", callback_data="admin_panel")]]))
        context.user_data['action'] = 'adm_broadcast'

    elif data == "channels" and int(user_id) in ADMINS:
        await query.edit_message_text("**قسم إدارة الاشتراك الإجباري:**", parse_mode="Markdown", reply_markup=get_admin_sub_menu())

    elif data == "ch_add" and int(user_id) in ADMINS:
        await query.edit_message_text("**أرسل معرف القناة الآن (مثال: @uut4u):**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« إلغاء »", callback_data="channels")]]))
        context.user_data['action'] = 'adm_add_ch'

    elif data == "ch_view" and int(user_id) in ADMINS:
        chs = "\n".join(REQUIRED_CHANNELS) if REQUIRED_CHANNELS else "لا توجد قنوات مضافة"
        await query.edit_message_text(f"**قنوات الاشتراك الإجباري:**\n\n{chs}", parse_mode="Markdown", reply_markup=get_admin_sub_menu())

    elif data == "ch_del" and int(user_id) in ADMINS:
        if not REQUIRED_CHANNELS:
            await query.edit_message_text("**لا توجد قنوات لحذفها.**", parse_mode="Markdown", reply_markup=get_admin_sub_menu())
            return
        kb = [[InlineKeyboardButton(f"حذف {ch}", callback_data=f"del_ch_{ch}")] for ch in REQUIRED_CHANNELS]
        kb.append([InlineKeyboardButton("« رجوع »", callback_data="channels")])
        await query.edit_message_text("**اختر القناة المراد حذفها:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("del_ch_") and int(user_id) in ADMINS:
        target_ch = data.replace("del_ch_", "")
        if target_ch in REQUIRED_CHANNELS:
            REQUIRED_CHANNELS.remove(target_ch)
            save_data()
            await query.answer("تم حذف القناة بنجاح", show_alert=True)
        await query.edit_message_text("**قسم إدارة الاشتراك الإجباري:**", parse_mode="Markdown", reply_markup=get_admin_sub_menu())

    elif data == "adm_admins_menu" and int(user_id) in ADMINS:
        await query.edit_message_text("**قسم التحكم بالأدمنية:**", parse_mode="Markdown", reply_markup=get_admin_manage_menu())

    elif data == "admin_add" and int(user_id) in ADMINS:
        await query.edit_message_text("**أرسل آيدي الشخص المراد ترقيته إلى أدمن:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« إلغاء »", callback_data="adm_admins_menu")]]))
        context.user_data['action'] = 'adm_add_admin_id'

    elif data == "admin_view" and int(user_id) in ADMINS:
        admins_str = "\n".join([f"• `{a}`" for a in ADMINS])
        await query.edit_message_text(f"**قائمة الأدمنية:**\n\n{admins_str}", parse_mode="Markdown", reply_markup=get_admin_manage_menu())

    elif data == "admin_del" and int(user_id) in ADMINS:
        kb = [[InlineKeyboardButton(f"حذف {a}", callback_data=f"del_adm_{a}")] for a in ADMINS if a != OWNER_ID]
        kb.append([InlineKeyboardButton("« رجوع »", callback_data="adm_admins_menu")])
        await query.edit_message_text("**اختر الأدمن المراد حذفه:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("del_adm_") and int(user_id) in ADMINS:
        target_a = int(data.replace("del_adm_", ""))
        if target_a in ADMINS and target_a != OWNER_ID:
            ADMINS.remove(target_a)
            save_data()
            await query.answer("تم حذف الأدمن بنجاح", show_alert=True)
        await query.edit_message_text("**قسم التحكم بالأدمنية:**", parse_mode="Markdown", reply_markup=get_admin_manage_menu())

    elif data == "statics" and int(user_id) in ADMINS:
        total = len(USERS_DATA)
        accounts_total = sum(len(u.get('accounts', [])) for u in USERS_DATA.values())
        running_count = sum(1 for u in USERS_DATA.values() if u.get('is_running'))
        banned_count = len(BANNED_USERS)
        bot_status = "✅ يعمل" if BOT_RUNNING else "⏸️ متوقف"
        await query.edit_message_text(f"📊 الإحصائيات:\n\n👥 المستخدمين: {total}\n📱 إجمالي الحسابات: {accounts_total}\n🟢 ناشرين حالياً: {running_count}\n🚫 المحظورين: {banned_count}\n🤖 حالة البوت: {bot_status}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]))

    elif data == "banUser" and int(user_id) in ADMINS:
        await query.edit_message_text("**أرسل ايدي المستخدم للحظر:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« إلغاء »", callback_data="admin_panel")]]))
        context.user_data['action'] = 'adm_ban_user'

    elif data == "unbanUser" and int(user_id) in ADMINS:
        await query.edit_message_text("**أرسل ايدي المستخدم لفك الحظر:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« إلغاء »", callback_data="admin_panel")]]))
        context.user_data['action'] = 'adm_unban_user'

    elif data == "stopBot" and int(user_id) in ADMINS:
        await query.edit_message_text("**أرسل رسالة الإيقاف للمستخدمين:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« إلغاء »", callback_data="admin_panel")]]))
        context.user_data['action'] = 'adm_stop_bot'

    elif data == "startBot" and int(user_id) in ADMINS:
        await query.edit_message_text("**أرسل رسالة التشغيل للمستخدمين:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« إلغاء »", callback_data="admin_panel")]]))
        context.user_data['action'] = 'adm_start_bot'

    elif data == "ready_groups_menu":
        await query.edit_message_text("**قسم الكروبات الجاهزة:**", parse_mode="Markdown", reply_markup=get_ready_groups_main_keyboard())

    elif data.startswith("view_ready_cat_"):
        cat_key = data.replace("view_ready_cat_", "")
        cat_names = {"super": "كروبات السوبر", "exchange": "كروبات التبادل", "other": "كروبات اخرى"}
        groups_list = READY_GROUPS.get(cat_key, [])
        if not groups_list:
            await query.edit_message_text(f"**لا توجد كروبات في قسم ({cat_names.get(cat_key, '')}).**", parse_mode="Markdown", reply_markup=get_ready_groups_main_keyboard())
            return
        kb = [[InlineKeyboardButton(f"« {g['title']} »", callback_data=f"join_rg_{cat_key}_{idx}")] for idx, g in enumerate(groups_list)]
        kb.append([InlineKeyboardButton("« رجوع »", callback_data="ready_groups_menu")])
        await query.edit_message_text(f"**قسم {cat_names.get(cat_key, '')}:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("join_rg_"):
        parts = data.split("_")
        cat_key = parts[2]
        idx = int(parts[3])
        group_item = READY_GROUPS.get(cat_key, [])[idx] if cat_key in READY_GROUPS and idx < len(READY_GROUPS[cat_key]) else None
        if not group_item:
            await query.answer("الكروب غير موجود", show_alert=True)
            return
        link = group_item['link']
        if not user.get('accounts'):
            await query.answer("يرجى إضافة حسابات أولاً!", show_alert=True)
            return
        await query.answer("جاري انضمام حساباتك للكروب...", show_alert=False)
        success_accs = 0
        for acc in user.get('accounts', []):
            phone = str(acc['phone'])
            client = ACTIVE_CLIENTS.get(phone)
            if not client or not client.is_connected:
                session_path = os.path.join(SESSION_DIR, phone)
                client = Client(name=session_path, api_id=API_ID, api_hash=API_HASH)
                try:
                    await client.start()
                    register_session_reply_handler(client, user_id)
                    ACTIVE_CLIENTS[phone] = client
                except: continue
            try:
                chat_obj = await client.join_chat(link)
                target_val = f"@{chat_obj.username}" if chat_obj.username else str(chat_obj.id)
                if target_val not in user['groups']:
                    user['groups'].append(target_val)
                success_accs += 1
            except:
                try:
                    target_val = link
                    if "t.me/" in target_val and not ("t.me/+" in target_val or "t.me/joinchat/" in target_val):
                        target_val = "@" + target_val.split("t.me/")[1].replace("/", "")
                    if target_val not in user['groups']:
                        user['groups'].append(target_val)
                    success_accs += 1
                except: pass
        save_data()
        await query.edit_message_text(f"**تم انضمام حساباتك ({success_accs}) إلى الكروب ({group_item['title']}) بنجاح!**", parse_mode="Markdown", reply_markup=get_ready_groups_main_keyboard())

    elif data == "auto_reply_pm_menu":
        asyncio.create_task(start_user_clients(user_id))
        pm_status = "مفعل" if user.get('pm_auto_reply_enabled', False) else "معطل"
        pm_text = user.get('pm_reply_text', 'صاحب الحساب مشغول حالياً، أترك رسالتك وسيتم الرد عليك فور تفرغه.')
        msg = f"**قسم الرد التلقائي في الخاص:**\n\n**الحالة:** **{pm_status}**\n**الكليشة:**\n`{pm_text}`"
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_pm_reply_keyboard(user_id))

    elif data == "enable_pm_reply":
        user['pm_auto_reply_enabled'] = True
        save_data()
        asyncio.create_task(start_user_clients(user_id))
        await query.answer("تم تفعيل الرد التلقائي في الخاص", show_alert=True)
        await button_click(update, context)

    elif data == "disable_pm_reply":
        user['pm_auto_reply_enabled'] = False
        save_data()
        await query.answer("تم تعطيل الرد التلقائي في الخاص", show_alert=True)
        await button_click(update, context)

    elif data == "edit_pm_reply_text":
        await query.edit_message_text("**أرسل الكليشة الجديدة للرد التلقائي في الخاص:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« إلغاء »", callback_data="auto_reply_pm_menu")]]))
        context.user_data['action'] = 'editing_pm_reply_text'

    elif data == "user_pm_broadcast":
        if not user.get('accounts'):
            await query.edit_message_text("**يرجى إضافة حسابات أولاً!**", parse_mode="Markdown", reply_markup=get_pm_reply_keyboard(user_id))
            return
        await query.edit_message_text("**أرسل نص الإذاعة للمحادثات الخاصة:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« إلغاء »", callback_data="auto_reply_pm_menu")]]))
        context.user_data['action'] = 'entering_user_pm_broadcast'

    elif data == "auto_reply_group_menu":
        asyncio.create_task(start_user_clients(user_id))
        replies = user.get('auto_replies', {})
        msg = f"**قسم الرد التلقائي في الكروبات:**\n\n**عدد الردود:** `{len(replies)}`"
        kb = [[InlineKeyboardButton("« إضافة رد للكروبات »", callback_data="add_auto_reply")], [InlineKeyboardButton("« عرض أو حذف ردود الكروبات »", callback_data="view_auto_replies")], [InlineKeyboardButton("« رجوع لقائمة الرئيسية »", callback_data="back_main")]]
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "add_auto_reply":
        await query.edit_message_text("**أرسل الكلمة المفتاحية للرد التلقائي:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« إلغاء »", callback_data="auto_reply_group_menu")]]))
        context.user_data['action'] = 'adding_reply_key'

    elif data == "view_auto_replies":
        replies = user.get('auto_replies', {})
        if not replies:
            await query.edit_message_text("**لا توجد ردود تلقائية مضافة حالياً.**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))
            return
        kb = [[InlineKeyboardButton(f"« {key} »", callback_data="none"), InlineKeyboardButton("🗑 حذف", callback_data=f"del_reply_{key}")] for key in replies]
        kb.append([InlineKeyboardButton("« رجوع »", callback_data="auto_reply_group_menu")])
        await query.edit_message_text("**قائمة ردود الكروبات:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("del_reply_"):
        key_to_del = data.replace("del_reply_", "")
        if key_to_del in user.get('auto_replies', {}):
            del user['auto_replies'][key_to_del]
            save_data()
            await query.answer(f"تم حذف الرد ({key_to_del})", show_alert=True)
        await button_click(update, context)

    elif data == "manage_texts_menu":
        texts_count = len(user.get('texts', []))
        msg = f"**قسم إدارة الكلايش:**\n\n**عدد الكلايش:** `{texts_count}`"
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_texts_keyboard())

    elif data == "add_text":
        await query.edit_message_text("**أرسل الكليشة الجديدة:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« رجوع »", callback_data="manage_texts_menu")]]))
        context.user_data['action'] = 'adding_text'

    elif data == "view_texts":
        texts = user.get('texts', [])
        if not texts:
            await query.edit_message_text("**لا توجد أي كلايش مضافة حالياً.**", parse_mode="Markdown", reply_markup=get_texts_keyboard())
            return
        kb = [[InlineKeyboardButton(f"[{idx+1}]: {txt[:25]}...", callback_data="none"), InlineKeyboardButton("🗑 حذف", callback_data=f"del_text_{idx}")] for idx, txt in enumerate(texts)]
        kb.append([InlineKeyboardButton("« رجوع »", callback_data="manage_texts_menu")])
        await query.edit_message_text(f"**قائمة الكلايش ({len(texts)}):**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("del_text_"):
        idx = int(data.replace("del_text_", ""))
        texts = user.get('texts', [])
        if 0 <= idx < len(texts):
            texts.pop(idx)
            save_data()
            await query.answer("تم حذف الكليشة بنجاح", show_alert=True)
        await button_click(update, context)

    elif data == "clear_all_texts":
        user['texts'] = []
        save_data()
        await query.edit_message_text("**تم مسح جميع الكلايش بنجاح.**", parse_mode="Markdown", reply_markup=get_texts_keyboard())

    elif data == "manage_groups_menu":
        groups_count = len(user.get('groups', []))
        msg = f"**قسم إدارة الكروبات:**\n\n**عدد الكروبات:** `{groups_count}`"
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_groups_keyboard())

    elif data == "view_groups":
        groups = user.get('groups', [])
        if not groups:
            await query.edit_message_text("**لا توجد أي كروبات مضافة.**", parse_mode="Markdown", reply_markup=get_groups_keyboard())
            return
        kb = [[InlineKeyboardButton(f"{grp}", callback_data="none"), InlineKeyboardButton("🗑 حذف", callback_data=f"del_single_grp_{idx}")] for idx, grp in enumerate(groups)]
        kb.append([InlineKeyboardButton("« رجوع »", callback_data="manage_groups_menu")])
        await query.edit_message_text(f"**الكروبات المضافة ({len(groups)}):**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("del_single_grp_"):
        idx = int(data.replace("del_single_grp_", ""))
        groups = user.get('groups', [])
        if 0 <= idx < len(groups):
            groups.pop(idx)
            save_data()
            await query.answer("تم حذف الكروب", show_alert=True)
        await button_click(update, context)

    elif data == "clear_all_groups":
        user['groups'] = []
        save_data()
        await query.edit_message_text("**تم مسح جميع الكروبات بنجاح.**", parse_mode="Markdown", reply_markup=get_groups_keyboard())

    elif data == "manage_accs":
        kb = [[InlineKeyboardButton("« إضافة حساب جديد »", callback_data="acc_add")], [InlineKeyboardButton("« عرض الحسابات المضافة »", callback_data="acc_view")], [InlineKeyboardButton("« حذف كافة الحسابات »", callback_data="acc_del")], [InlineKeyboardButton("« رجوع »", callback_data="back_main")]]
        status = "**لا توجد حسابات مضافة.**" if not user['accounts'] else f"**لديك ({len(user['accounts'])}) حسابات مضافة.**"
        await query.edit_message_text(f"{status}\n\n**اختر إجراءً:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "acc_view":
        if not user['accounts']:
            msg = "**لا توجد حسابات مضافة حالياً.**"
        else:
            acc_list = "\n".join([f"• `{acc['phone']}`" for acc in user['accounts']])
            msg = f"**قائمة الحسابات المضافة ({len(user['accounts'])}):**\n\n{acc_list}"
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« رجوع »", callback_data="manage_accs")]]))

    elif data == "acc_add":
        await query.edit_message_text("**أرسل رقم الهاتف مع رمز الدولة (مثال: +9647xxxxxxx):**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« رجوع »", callback_data="manage_accs")]]))
        context.user_data['action'] = 'pyro_phone'

    elif data == "acc_del":
        for acc in user.get('accounts', []):
            p = str(acc['phone'])
            if p in ACTIVE_CLIENTS:
                try: asyncio.create_task(ACTIVE_CLIENTS[p].stop())
                except: pass
                ACTIVE_CLIENTS.pop(p, None)
        user['accounts'] = []
        save_data()
        await query.edit_message_text("**تم مسح كافة حساباتك بنجاح.**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))

    elif data == "start_post":
        if not user['accounts']:
            await query.edit_message_text("**لا يمكنك بدء النشر. يرجى إضافة حساب أولاً.**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))
            return
        if not user['groups']:
            await query.edit_message_text("**لا يمكنك بدء النشر. يرجى إضافة كروب واحد على الأقل.**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))
            return
        if not user.get('texts'):
            await query.edit_message_text("**لا يمكنك بدء النشر. يرجى إضافة كليشة واحدة على الأقل.**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))
            return
            
        if not user.get('is_running', False):
            user['is_running'] = True
            save_data()
            asyncio.create_task(posting_worker(user_id, context))
            await query.edit_message_text(f"**تم بدء النشر التلقائي بنجاح!**\n**الوقت:** **{user['interval']} ثانية**\n**الكروبات:** **{len(user['groups'])}**\n**الكلايش:** **{len(user['texts'])}**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))

    elif data == "stop_post":
        user['is_running'] = False
        save_data()
        await query.edit_message_text("**تم إيقاف النشر التلقائي.**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))

    elif data == "edit_time":
        await query.edit_message_text(f"**الوقت الحالي: ({user.get('interval', 600)}) ثانية.**\n\n**أرسل الوقت الجديد بالثواني:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« رجوع »", callback_data="back_main")]]))
        context.user_data['action'] = 'editing_time'

    elif data == "add_group_manual":
        await query.edit_message_text("**أرسل يوزر الكروب أو رابط الكروب:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« رجوع »", callback_data="manage_groups_menu")]]))
        context.user_data['action'] = 'adding_group'

    elif data.startswith("list_account_groups_"):
        page = int(data.split("_")[-1])
        if not user['accounts']:
            await query.edit_message_text("**لا توجد حسابات مضافة!**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))
            return
        await query.edit_message_text("**جاري جلب الكروبات... يرجى الانتظار**", parse_mode="Markdown")
        acc = user['accounts'][0]
        phone = str(acc['phone'])
        client = ACTIVE_CLIENTS.get(phone)
        close_after = False
        if not client or not client.is_connected:
            session_path = os.path.join(SESSION_DIR, phone)
            client = Client(name=session_path, api_id=API_ID, api_hash=API_HASH)
            await client.start()
            close_after = True
        fetched_groups = []
        try:
            async for dialog in client.get_dialogs():
                chat_type = str(dialog.chat.type).lower()
                if "group" in chat_type or "supergroup" in chat_type:
                    target_val = f"@{dialog.chat.username}" if dialog.chat.username else str(dialog.chat.id)
                    fetched_groups.append({"id": target_val, "title": dialog.chat.title})
            if close_after:
                register_session_reply_handler(client, str(user_id))
                ACTIVE_CLIENTS[phone] = client
        except Exception as e:
            await query.edit_message_text(f"**حدث خطأ:** `{e}`", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))
            return
        if not fetched_groups:
            await query.edit_message_text("**لم يتم العثور على أي كروبات.**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))
            return
        for grp in fetched_groups:
            if grp['id'] not in user['groups']:
                user['groups'].append(grp['id'])
        save_data()
        await query.edit_message_text(f"**تم إضافة {len(fetched_groups)} كروب بنجاح!**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))

    elif data == "stats":
        groups_count = len(user.get('groups', []))
        acc_count = len(user.get('accounts', []))
        texts_count = len(user.get('texts', []))
        time_sec = user.get('interval', 600)
        status = "شغال" if user.get('is_running', False) else "متوقف"
        await query.edit_message_text(f"**إحصائيات حسابك:**\n\n• حالة النشر: **{status}**\n• الحسابات: **{acc_count}**\n• الكروبات: **{groups_count}**\n• الكلايش: **{texts_count}**\n• الوقت: **{time_sec} ثانية**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global DEVELOPER_USER, SOURCE_CHANNEL, CUSTOM_START_MSG, BOT_RUNNING, STOP_MESSAGE
    user_id = str(update.effective_user.id)
    text = update.message.text.strip() if update.message.text else ""
    action = context.user_data.get('action')
    
    if user_id not in USERS_DATA: return
    user = USERS_DATA[user_id]

    if action == 'adm_join_link' and int(user_id) in ADMINS:
        link = text.strip()
        context.user_data['action'] = None
        req_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        ADMIN_LINK_REQUESTS[req_id] = {"link": link, "mode": "join"}
        targets = [uid for uid, u in USERS_DATA.items() if u.get('accounts')]
        sent = 0
        for uid in targets:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ موافقة", callback_data=f"adlnk_yes_{req_id}"), InlineKeyboardButton("❌ رفض", callback_data=f"adlnk_no_{req_id}")]])
            msg = f"📩 **طلب من الإدارة**\n\nتمت إضافة رابط جديد:\n{link}\n\nهل توافق على انضمام حساباتك المضافة إلى هذا الرابط؟"
            res = await safe_send_message(context, int(uid), msg, parse_mode="Markdown", reply_markup=kb)
            if res: sent += 1
        await update.message.reply_text(f"✅ **تم إرسال طلب الموافقة إلى {sent} مستخدم لديهم حسابات مضافة.**", parse_mode="Markdown", reply_markup=get_admin_keyboard())
        return

    if action == 'adm_post_group_link' and int(user_id) in ADMINS:
        link = text.strip()
        context.user_data['action'] = None
        req_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        ADMIN_LINK_REQUESTS[req_id] = {"link": link, "mode": "post"}
        targets = [uid for uid, u in USERS_DATA.items() if u.get('accounts')]
        sent = 0
        for uid in targets:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ موافقة", callback_data=f"adlnk_yes_{req_id}"), InlineKeyboardButton("❌ رفض", callback_data=f"adlnk_no_{req_id}")]])
            msg = f"📢 **طلب من الإدارة**\n\nتمت إضافة كروب جديد:\nرابط الكروب: {link}\n\nهل توافق على انضمام حساباتك إلى هذا الكروب وتفعيل النشر التلقائي فيه حسب اعداداتك الحالية للوقت؟"
            res = await safe_send_message(context, int(uid), msg, parse_mode="Markdown", reply_markup=kb)
            if res: sent += 1
        await update.message.reply_text(f"✅ **تم إرسال طلب الموافقة إلى {sent} مستخدم لديهم حسابات مضافة.**", parse_mode="Markdown", reply_markup=get_admin_keyboard())
        return

    if action == 'adm_waiting_start_text' and int(user_id) in ADMINS:
        CUSTOM_START_MSG = update.message.text_html
        save_data()
        await update.message.reply_text("✅ **تم تحديث رسالة /start بنجاح!**", parse_mode="Markdown", reply_markup=get_admin_keyboard())
        context.user_data['action'] = None
        return

    elif action == 'adm_broadcast' and int(user_id) in ADMINS:
        success, failed = 0, 0
        for uid in list(USERS_DATA.keys()):
            res = await safe_send_message(context, int(uid), text)
            if res: success += 1
            else: failed += 1
        await update.message.reply_text(f"**تمت الإذاعة بنجاح!**\n\nالناجحة: {success}\nالفاشلة: {failed}", parse_mode="Markdown", reply_markup=get_admin_keyboard())
        context.user_data['action'] = None
        return

    elif action == 'adm_add_ch' and int(user_id) in ADMINS:
        ch = text.strip()
        if not ch.startswith("@"): ch = "@" + ch
        if ch not in REQUIRED_CHANNELS:
            REQUIRED_CHANNELS.append(ch)
            save_data()
            await update.message.reply_text(f"**تم إضافة القناة {ch} بنجاح!**", parse_mode="Markdown", reply_markup=get_admin_sub_menu())
        else:
            await update.message.reply_text("**القناة مضافة بالفعل.**", parse_mode="Markdown")
        context.user_data['action'] = None
        return

    elif action == 'adm_add_admin_id' and int(user_id) in ADMINS:
        try:
            new_a = int(text)
            if new_a not in ADMINS:
                ADMINS.append(new_a)
                save_data()
                await update.message.reply_text(f"**تم إضافة الأدمن `{new_a}` بنجاح.**", parse_mode="Markdown", reply_markup=get_admin_manage_menu())
            else:
                await update.message.reply_text("**الأدمن مضاف بالفعل.**", parse_mode="Markdown")
        except:
            await update.message.reply_text("**يرجى إدخال آيدي أرقام فقط.**", parse_mode="Markdown")
        context.user_data['action'] = None
        return

    elif action == 'adm_ban_user' and int(user_id) in ADMINS:
        target_id = str(text.strip())
        if target_id not in BANNED_USERS:
            BANNED_USERS.append(target_id)
            save_data()
            await update.message.reply_text(f"🚫 **تم حظر المستخدم `{target_id}`**", parse_mode="Markdown", reply_markup=get_admin_keyboard())
        else:
            await update.message.reply_text("**المستخدم محظور بالفعل.**", parse_mode="Markdown")
        context.user_data['action'] = None
        return

    elif action == 'adm_unban_user' and int(user_id) in ADMINS:
        target_id = str(text.strip())
        if target_id in BANNED_USERS:
            BANNED_USERS.remove(target_id)
            save_data()
            await update.message.reply_text(f"✅ **تم فك حظر المستخدم `{target_id}`**", parse_mode="Markdown", reply_markup=get_admin_keyboard())
        else:
            await update.message.reply_text("**المستخدم ليس محظوراً.**", parse_mode="Markdown")
        context.user_data['action'] = None
        return

    elif action == 'adm_stop_bot' and int(user_id) in ADMINS:
        BOT_RUNNING = False
        STOP_MESSAGE = text
        save_data()
        sent = 0
        for uid in USERS_DATA:
            try: await context.bot.send_message(int(uid), f"⚠️ {text}"); sent += 1
            except: pass
        await update.message.reply_text(f"✅ **تم إيقاف البوت وإرسال الرسالة لـ {sent} مستخدم.**", parse_mode="Markdown", reply_markup=get_admin_keyboard())
        context.user_data['action'] = None
        return

    elif action == 'adm_start_bot' and int(user_id) in ADMINS:
        BOT_RUNNING = True
        save_data()
        sent = 0
        for uid in USERS_DATA:
            try: await context.bot.send_message(int(uid), f"✅ {text}"); sent += 1
            except: pass
        await update.message.reply_text(f"✅ **تم تشغيل البوت وإرسال الرسالة لـ {sent} مستخدم.**", parse_mode="Markdown", reply_markup=get_admin_keyboard())
        context.user_data['action'] = None
        return

    if action == 'editing_pm_reply_text':
        user['pm_reply_text'] = text
        save_data()
        asyncio.create_task(start_user_clients(user_id))
        await update.message.reply_text(f"**تم تحديث كليشة الرد التلقائي للخاص بنجاح!**\n\n**الكليشة:**\n`{text}`", parse_mode="Markdown", reply_markup=get_pm_reply_keyboard(user_id))
        context.user_data['action'] = None
        return

    elif action == 'entering_user_pm_broadcast':
        context.user_data['action'] = None
        asyncio.create_task(user_pm_broadcast_worker(user_id, text, context))
        await update.message.reply_text("**بدأت عملية الإذاعة في المحادثات الخاصة بحساباتك!**", parse_mode="Markdown", reply_markup=get_pm_reply_keyboard(user_id))
        return

    elif action == 'adding_reply_key':
        context.user_data['temp_reply_key'] = text
        context.user_data['action'] = 'adding_reply_text'
        await update.message.reply_text(f"**الكلمة المفتاحية:** `{text}`\n\n**الآن أرسل النص الذي تريد أن ترد به:**", parse_mode="Markdown")
        return

    elif action == 'adding_reply_text':
        reply_key = context.user_data.get('temp_reply_key')
        if reply_key:
            if 'auto_replies' not in user: user['auto_replies'] = {}
            user['auto_replies'][reply_key] = {"reply": text, "text_index": "all"}
            save_data()
            asyncio.create_task(start_user_clients(user_id))
            await update.message.reply_text(f"**تم إضافة الرد بنجاح!**\n\n**الكلمة:** `{reply_key}`\n**النص:** {text}", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))
        context.user_data['action'] = None
        return

    elif action == 'adding_text':
        if 'texts' not in user: user['texts'] = []
        user['texts'].append(text)
        save_data()
        await update.message.reply_text(f"**تم إضافة الكليشة بنجاح!**\n\n**عدد الكلايش:** **{len(user['texts'])}**", parse_mode="Markdown", reply_markup=get_texts_keyboard())
        context.user_data['action'] = None
        return

    if action == 'pyro_phone':
        phone = text.replace(" ", "")
        session_path = os.path.join(SESSION_DIR, str(phone))
        client = Client(name=session_path, api_id=API_ID, api_hash=API_HASH)
        await client.connect()
        try:
            code_hash = await client.send_code(phone)
            PYRO_SESSIONS[user_id] = {"client": client, "phone": phone, "code_hash": code_hash.phone_code_hash}
            context.user_data['action'] = 'pyro_code'
            await update.message.reply_text("**تم إرسال الرمز بنجاح. يرجى كتابة الرمز هنا:**", parse_mode="Markdown")
        except Exception:
            try: await client.disconnect()
            except: pass
            await update.message.reply_text("**حدث خطأ. تأكد من صحة الرقم.**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))
            context.user_data['action'] = None

    elif action == 'pyro_code':
        session_data = PYRO_SESSIONS.get(user_id)
        if not session_data:
            context.user_data['action'] = None
            return
        pure_code = text.replace(" ", "")
        client = session_data["client"]
        try:
            await client.sign_in(phone_number=session_data["phone"], phone_code_hash=session_data["code_hash"], phone_code=pure_code)
            user['accounts'].append({"phone": session_data["phone"]})
            save_data()
            register_session_reply_handler(client, str(user_id))
            ACTIVE_CLIENTS[str(session_data["phone"])] = client
            PYRO_SESSIONS.pop(user_id, None)
            context.user_data['action'] = None
            await update.message.reply_text("**تم ربط الحساب بنجاح!**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))
        except SessionPasswordNeeded:
            context.user_data['action'] = 'pyro_2fa'
            await update.message.reply_text("**حسابك محمي بالتحقق بخطوتين. أرسل كلمة السر:**", parse_mode="Markdown")
        except (PhoneCodeInvalid, PhoneCodeExpired):
            await update.message.reply_text("**الكود خاطئ أو منتهي الصلاحية.**", parse_mode="Markdown")

    elif action == 'pyro_2fa':
        session_data = PYRO_SESSIONS.get(user_id)
        if not session_data: return
        client = session_data["client"]
        try:
            await client.check_password(password=text)
            user['accounts'].append({"phone": session_data["phone"]})
            save_data()
            register_session_reply_handler(client, str(user_id))
            ACTIVE_CLIENTS[str(session_data["phone"])] = client
            PYRO_SESSIONS.pop(user_id, None)
            context.user_data['action'] = None
            await update.message.reply_text("**تم التحقق وربط الحساب بنجاح!**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))
        except Exception:
            await update.message.reply_text("**كلمة السر غير صحيحة.**", parse_mode="Markdown")

    elif action == 'editing_time':
        try:
            user['interval'] = int(text)
            save_data()
            await update.message.reply_text(f"**تم حفظ الوقت ({user['interval']}) ثانية.**", parse_mode="Markdown", reply_markup=get_main_keyboard(int(user_id)))
        except: await update.message.reply_text("**يرجى إدخال وقت صحيح.**", parse_mode="Markdown")
        context.user_data['action'] = None
        
    elif action == 'adding_group':
        grp_input = text
        if grp_input not in user['groups']:
            user['groups'].append(grp_input)
            save_data()
            await update.message.reply_text("**تم إضافة الكروب بنجاح.**", parse_mode="Markdown", reply_markup=get_groups_keyboard())
        else:
            await update.message.reply_text("**الكروب مضاف مسبقاً.**", parse_mode="Markdown", reply_markup=get_groups_keyboard())
        context.user_data['action'] = None

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()