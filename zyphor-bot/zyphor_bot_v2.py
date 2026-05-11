import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

BOT_TOKEN = "8668659853:AAHDbKhbDZOKaPaT0aOsSyIUyxVMD-CcAfY"
SITE_API  = "https://yoursite.com/api"  # ← غيّر هذا لرابط موقعك

bot = telebot.TeleBot(BOT_TOKEN)


# ══════════════════════════════════════════════════════════════
# Callback: زرا OTP
# ══════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_login_") or
                                            c.data.startswith("check_role_"))
def handle_otp_buttons(c):
    chat_id = str(c.from_user.id)
    data    = c.data

    # ── ✅ تأكيد تسجيل الدخول ─────────────────────────────────
    if data.startswith("confirm_login_"):
        bot.answer_callback_query(c.id, "✅ تم التحقق من هويتك")
        bot.edit_message_text(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            text=(
                "✅ <b>تم تأكيد تسجيل الدخول</b>\n\n"
                "أدخل الكود في الموقع لإكمال الدخول."
            ),
            parse_mode="HTML"
        )

    # ── 🔍 التحقق من الرتبة ───────────────────────────────────
    elif data.startswith("check_role_"):
        bot.answer_callback_query(c.id, "جاري التحقق...")

        try:
            # استعلام API الموقع عن رتبة المستخدم بالـ chat_id
            resp = requests.get(
                f"{SITE_API}/check-role/{chat_id}",
                timeout=5
            )
            if resp.status_code == 200:
                result = resp.json()
                username = result.get("username", "غير معروف")
                role     = result.get("role", "غير محدد")
                saldo    = result.get("saldo", 0)
                expires  = result.get("expiration_date", "—")

                # خريطة الرتب
                role_icons = {
                    "1": "👑 OWNER",
                    "2": "🛡️ ADMIN",
                    "3": "💼 RESELLER",
                }
                role_display = role_icons.get(str(role), f"رتبة {role}")

                msg = (
                    f"👤 <b>معلومات حسابك</b>\n\n"
                    f"• الاسم: <b>{username}</b>\n"
                    f"• الرتبة: <b>{role_display}</b>\n"
                    f"• الرصيد: <b>{saldo} 💎</b>\n"
                    f"• ينتهي: <b>{expires}</b>"
                )
            else:
                msg = "❌ لم يتم العثور على حسابك. تأكد أن الـ Telegram ID مسجل في الموقع."

        except Exception as e:
            msg = f"⚠️ خطأ في الاتصال بالموقع:\n<code>{e}</code>"

        bot.edit_message_text(
            chat_id=c.message.chat.id,
            message_id=c.message.message_id,
            text=msg,
            parse_mode="HTML"
        )


# ══════════════════════════════════════════════════════════════
# /start
# ══════════════════════════════════════════════════════════════
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        f"👋 مرحباً <b>{message.from_user.first_name}</b>!\n\n"
        f"🤖 بوت <b>Zyphor Server</b>\n\n"
        f"• Chat ID الخاص بك: <code>{message.chat.id}</code>\n"
        f"• ضع هذا الرقم في خانة Telegram Chat ID عند التسجيل في الموقع.",
        parse_mode="HTML"
    )


print("✅ Zyphor Bot Started...")
bot.infinity_polling()