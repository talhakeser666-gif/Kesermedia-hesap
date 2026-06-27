import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

# ========================================================
# ⚙️ TEK BOT YAPILANDIRMASI
# ========================================================
BOT_TOKEN = "8403988946:AAGqSXyIvMp6V0mBdR0yj19Fu_Wc4kiQngo"
REQUIRED_CHANNEL = "@leakvipsorgubot"                        
BOT_USERNAME = "@leakvipsorgubot"                            
VIP_CONTACT = "@talhajcx"                                    
REQ_REF_COUNT = 25                                           
ADMIN_PASSWORD = "123talhaleak" 

bot = telebot.TeleBot(BOT_TOKEN)

# Dosya Tabanlı Kalıcı Veritabanı Ayarları 💾
DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for u_id in data.get("users", {}):
                    data["users"][u_id]["invitees"] = set(data["users"][u_id]["invitees"])
                return data.get("users", {}), set(data.get("admins", []))
        except:
            return {}, set()
    return {}, set()

def save_db():
    try:
        serializable_users = {}
        for u_id, u_data in db.items():
            serializable_users[u_id] = {
                "username": u_data["username"],
                "referred_by": u_data["referred_by"],
                "invitees": list(u_data["invitees"]),
                "is_vip": u_data["is_vip"],
                "is_banned": u_data["is_banned"]
            }
        
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump({"users": serializable_users, "admins": list(admins)}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Veritabanı kaydetme hatası: {e}")

# Hafızayı Dosyadan Yükle
db, admins = load_db()
user_state = {}  

def init_user(user_id, username="Bilinmiyor"):
    user_id = str(user_id)
    if user_id not in db:
        db[user_id] = {
            "username": username,
            "referred_by": None,
            "invitees": set(),
            "is_vip": False,
            "is_banned": False
        }
        save_db()

def is_user_member(user_id):
    if str(user_id) in admins: 
        return True
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return True

# --- MENÜLER ---
def main_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🏫 E-okul Sorgu", callback_data="sorgu_eokul"), InlineKeyboardButton("🚗 Muayene Sorgu", callback_data="sorgu_muayene"))
    markup.row(InlineKeyboardButton("🛡️ Sigorta Sorgu", callback_data="sorgu_sigorta"), InlineKeyboardButton("🚘 Plaka Sorgu", callback_data="sorgu_plaka"))
    markup.row(InlineKeyboardButton("🧾 Fatura Sorgu", callback_data="sorgu_fatura"), InlineKeyboardButton("🎵 Tiktok Sorgu", callback_data="sorgu_tiktok"))
    markup.row(InlineKeyboardButton("✈️ Telegram Sorgu", callback_data="sorgu_telegram"), InlineKeyboardButton("💳 IBAN Sorgu", callback_data="sorgu_iban"))
    markup.row(InlineKeyboardButton("👥 Davet & Referans Paneli", callback_data="menu_ref"))
    return markup

def admin_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Toplu Duyuru Yap", callback_data="admin_broadcast"))
    markup.row(InlineKeyboardButton("👑 VIP Yönetimi (Ver/Al)", callback_data="admin_vip_toggle"))
    markup.row(InlineKeyboardButton("🚫 Kullanıcı Banla/Aç", callback_data="admin_ban_toggle"))
    markup.row(InlineKeyboardButton("📊 Kayıtlı Kullanıcıları Listele", callback_data="admin_list_users"))
    return markup

# ========================================================
# 🔑 GİZLİ ADMİN GİRİŞ SİSTEMİ
# ========================================================
@bot.message_handler(commands=['admin'])
def admin_login_request(message):
    user_id = str(message.from_user.id)
    if user_id in admins:
        bot.send_message(message.chat.id, "🛠️ **Yönetim Paneline Zaten Giriş Yapmışsınız:**", reply_markup=admin_menu(), parse_mode="Markdown")
        return
    
    user_state[user_id] = "waiting_password"
    bot.send_message(message.chat.id, "🔒 **Gizli Yönetim Alanı.**\nLütfen erişim şifresini giriniz:")

# ========================================================
# 👋 KULLANICI BAŞLANGIÇ KOMUTLARI
# ========================================================
@bot.message_handler(commands=['start'])
def user_start(message):
    try:
        user_id = str(message.from_user.id)
        uname = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        
        is_new = user_id not in db
        init_user(user_id, uname)
        
        if db[user_id]["is_banned"]:
            bot.send_message(message.chat.id, "🚫 **Sistemden kalıcı olarak banlandınız.**")
            return

        if is_new:
            for adm in admins:
                try: bot.send_message(adm, f"📥 **Yeni Üye:** {uname} (`{user_id}`) botu başlattı.")
                except: pass

        # Referans Sistemi Kontrolü
        args = message.text.split()
        if len(args) > 1:
            try:
                ref_id = str(args[1])
                if ref_id != user_id and db[user_id]["referred_by"] is None:
                    db[user_id]["referred_by"] = ref_id
                    init_user(ref_id)
                    db[ref_id]["invitees"].add(user_id)
                    save_db()
                    
                    bot.send_message(int(ref_id), f"🎉 Botumuza yeni bir üye davet ettiniz! Toplam referansınız: {len(db[ref_id]['invitees'])}")
                    
                    for adm in admins:
                        try: bot.send_message(adm, f"👥 **Ref Raporu:** `{ref_id}` -> {uname} üyesini davet etti.")
                        except: pass
            except: pass

        if not is_user_member(user_id):
            gate_markup = InlineKeyboardMarkup()
            gate_markup.row(InlineKeyboardButton("📢 Kanala Katıl", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}"))
            gate_markup.row(InlineKeyboardButton("✅ Katıldım, Kontrol Et", callback_data="check_sub"))
            bot.send_message(message.chat.id, f"👋 **Merhaba {message.from_user.first_name}!**\n\nBotu kullanabilmek için {REQUIRED_CHANNEL} kanalına katılmanız zorunludur.\n\n🆔 **ID:** `{user_id}`", reply_markup=gate_markup, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"👋 **Hoş Geldiniz {message.from_user.first_name}!**\n\nİşlem yapmak istediğiniz sorgu türünü seçebilirsiniz 👇", reply_markup=main_menu(), parse_mode="Markdown")
    except: pass

# ========================================================
# 📥 METİN GİRDİLERİ
# ========================================================
@bot.message_handler(func=lambda message: True)
def handle_text_inputs(message):
    user_id = str(message.from_user.id)
    state = user_state.get(user_id)
    if not state: return

    if state == "waiting_password":
        if message.text == ADMIN_PASSWORD:
            admins.add(user_id)
            user_state[user_id] = None
            save_db()
            bot.send_message(message.chat.id, "✅ **Şifre Doğru!**\nSistem yöneticisi oldunuz. Paneliniz hazır:", reply_markup=admin_menu(), parse_mode="Markdown")
        else:
            user_state[user_id] = None
            bot.send_message(message.chat.id, "❌ **Hatalı Şifre!**")

    elif user_id in admins:
        if state == "waiting_broadcast":
            user_state[user_id] = None
            basarili = 0
            duyuru_sablonu = f"📢 **DUYURU**\n--------------------\n\n{message.text}"
            for u_id in list(db.keys()):
                try:
                    bot.send_message(int(u_id), duyuru_sablonu, parse_mode="Markdown")
                    basarili += 1
                except: pass 
            bot.send_message(message.chat.id, f"✅ Duyuru bitti. Ulaşılan: {basarili} kişi.")

        elif state == "waiting_vip_id":
            user_state[user_id] = None
            try:
                target_id = str(int(message.text))
                init_user(target_id)
                db[target_id]["is_vip"] = not db[target_id]["is_vip"]
                save_db()
                durum = "VIP YAPILDI 👑" if db[target_id]["is_vip"] else "VIP İPTAL EDİLDİ ❌"
                bot.send_message(message.chat.id, f"👤 `{target_id}` durumu: {durum}")
            except: bot.send_message(message.chat.id, "❌ Geçersiz ID.")

        elif state == "waiting_ban_id":
            user_state[user_id] = None
            try:
                target_id = str(int(message.text))
                init_user(target_id)
                db[target_id]["is_banned"] = not db[target_id]["is_banned"]
                save_db()
                durum = "BANLANDI 🚫" if db[target_id]["is_banned"] else "BANI KALDIRILDI ✅"
                bot.send_message(message.chat.id, f"👤 `{target_id}` durumu: {durum}")
            except: bot.send_message(message.chat.id, "❌ Geçersiz ID.")

# ========================================================
# 🔘 BUTON TIKLAMALARI
# ========================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    try:
        user_id = str(call.from_user.id)
        
        if db.get(user_id, {}).get("is_banned", False) and user_id not in admins:
            bot.answer_callback_query(call.id, "Sistemden banlandınız!", show_alert=True)
            return

        if call.data == "check_sub":
            if is_user_member(user_id):
                try: bot.delete_message(call.message.chat.id, call.message.message_id)
                except: pass
                bot.send_message(call.message.chat.id, "✅ Doğrulama Başarılı! Sorgu menüsü:", reply_markup=main_menu())
            else:
                bot.answer_callback_query(call.id, "❌ Henüz katılım sağlanmamış!", show_alert=True)
                
        elif call.data == "menu_ref":
            ref_count = len(db.get(user_id, {}).get("invitees", set()))
            ref_link = f"https://t.me/{BOT_USERNAME[1:]}?start={user_id}"
            bot.send_message(call.message.chat.id, f"👥 **Referans Durum Paneli**\n\n🔗 Linkiniz:\n`{ref_link}`\n\n📊 Toplam Davet: {ref_count}/{REQ_REF_COUNT}", parse_mode="Markdown")
            bot.answer_callback_query(call.id)
            
        elif call.data.startswith('sorgu_'):
            sorgu_tipleri = {
                "sorgu_eokul": "E-okul Sorgu", "sorgu_muayene": "Muayene Sorgu",
                "sorgu_sigorta": "Sigorta Sorgu", "sorgu_plaka": "Plaka Sorgu",
                "sorgu_fatura": "Fatura Sorgu", "sorgu_tiktok": "Tiktok Sorgu",
                "sorgu_telegram": "Telegram Sorgu", "sorgu_iban": "IBAN Sorgu"
            }
            sorgu_adi = sorgu_tipleri.get(call.data, "Bilinmeyen")
            
            # Canlı Takip Raporu
            uname = f"@{call.from_user.username}" if call.from_user.username else call.from_user.first_name
            for adm in admins:
                try: bot.send_message(adm, f"🔍 **Log:** {uname} (`{user_id}`) -> {sorgu_adi} tıkladı.")
                except: pass
            
            ref_count = len(db.get(user_id, {}).get("invitees", set()))
            if db.get(user_id, {}).get("is_vip", False) or ref_count >= REQ_REF_COUNT or user_id in admins:
                bot.send_message(call.message.chat.id, f"✅ **Erişim Başarılı!**\n**{sorgu_adi}** ekranı açıldı.")
            else:
                bot.send_message(call.message.chat.id, f"⚠️ **Erişim Engellendi!**\n\n📊 Ref: {ref_count} / {REQ_REF_COUNT}\n💰 VIP Alım: {VIP_CONTACT}")
            bot.answer_callback_query(call.id)

        # Admin Buton İşlemleri
        elif user_id in admins:
            if call.data == "admin_broadcast":
                user_state[user_id] = "waiting_broadcast"
                bot.send_message(int(user_id), "📢 Herkese gidecek duyuru mesajını yazın:")
                bot.answer_callback_query(call.id)
            elif call.data == "admin_vip_toggle":
                user_state[user_id] = "waiting_vip_id"
                bot.send_message(int(user_id), "👑 VIP durumu değişecek kişinin Telegram ID'sini yazın:")
                bot.answer_callback_query(call.id)
            elif call.data == "admin_ban_toggle":
                user_state[user_id] = "waiting_ban_id"
                bot.send_message(int(user_id), "🚫 Ban durumu değişecek kişinin Telegram ID'sini yazın:")
                bot.answer_callback_query(call.id)
            elif call.data == "admin_list_users":
                if not db:
                    bot.send_message(int(user_id), "📭 Kayıtlı kimse yok.")
                    return
                
                # 🔢 Başına rakam eklenen numaralı ve toplam sayıyı gösteren liste
                rapor = f"📊 **KULLANICI LİSTESİ** (Toplam: {len(db)} Kişi)\n\n"
                for sira, (u_id, data) in enumerate(db.items(), start=1):
                    rapor += f"{sira}. 👤 {data['username']} | ID: `{u_id}` | Ref: {len(data['invitees'])} | VIP: {data['is_vip']} | Ban: {data['is_banned']}\n"
                
                bot.send_message(int(user_id), rapor, parse_mode="Markdown")
                bot.answer_callback_query(call.id)
    except: pass

if __name__ == "__main__":
    try: bot.delete_webhook()
    except: pass
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
