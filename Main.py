import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
import time

BOT_TOKEN = "8403988946:AAGqSXyIvMp6V0mBdR0yj19Fu_Wc4kiQngo"
REQUIRED_CHANNEL = "@leakvipsorgubot"                        
BOT_USERNAME = "@leakvipsorgubot"                            
VIP_CONTACT = "@talhajcx"                                    
REQ_REF_COUNT = 25                                           
ADMIN_PASSWORD = "123talhaleak" 

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "database.json"

DEFAULT_SORGU = {
    "sorgu_eokul": "🏫 E-okul Sorgu", 
    "sorgu_muayene": "🚗 Muayene Sorgu",
    "sorgu_sigorta": "🛡️ Sigorta Sorgu", 
    "sorgu_plaka": "🚘 Plaka Sorgu",
    "sorgu_fatura": "🧾 Fatura Sorgu", 
    "sorgu_tiktok": "🎵 Tiktok Sorgu",
    "sorgu_telegram": "✈️ Telegram Sorgu", 
    "sorgu_iban": "💳 IBAN Sorgu"
}

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for u_id in data.get("users", {}):
                    data["users"][u_id]["invitees"] = set(data["users"][u_id]["invitees"])
                live_logs = data.get("live_logs", True)
                sorgu_listesi = data.get("sorgu_listesi", DEFAULT_SORGU)
                
                if "sorgu_ayak" in sorgu_listesi:
                    del sorgu_listesi["sorgu_ayak"]
                    
                return data.get("users", {}), set(data.get("admins", [])), live_logs, sorgu_listesi
        except:
            return {}, set(), True, DEFAULT_SORGU.copy()
    return {}, set(), True, DEFAULT_SORGU.copy()

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
            json.dump({
                "users": serializable_users, 
                "admins": list(admins),
                "live_logs": live_logs_enabled,
                "sorgu_listesi": sorgu_listesi
            }, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Veritabanı kayıt hatası: {e}")

db, admins, live_logs_enabled, sorgu_listesi = load_db()
user_state = {}  
pending_actions = {} 

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

def main_menu():
    markup = InlineKeyboardMarkup()
    buttons = []
    for callback, baslik in sorgu_listesi.items():
        buttons.append(InlineKeyboardButton(baslik, callback_data=callback))
    
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.row(buttons[i], buttons[i+1])
        else:
            markup.row(buttons[i])
            
    markup.row(InlineKeyboardButton("👥 Davet Et", callback_data="menu_ref"))
    return markup

def admin_menu():
    global live_logs_enabled
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Toplu Duyuru Yap", callback_data="admin_broadcast"))
    markup.row(InlineKeyboardButton("👑 VIP Yönetimi (Ver/Al)", callback_data="admin_vip_toggle"))
    markup.row(InlineKeyboardButton("🚫 Kullanıcı Banla/Aç", callback_data="admin_ban_toggle"))
    markup.row(InlineKeyboardButton("📊 Kayıtlı Kullanıcıları Listele", callback_data="admin_list_users"))
    log_durum_metni = "🟢 Canlı Loglar: AÇIK" if live_logs_enabled else "🔴 Canlı Loglar: KAPALI"
    markup.row(InlineKeyboardButton(log_durum_metni, callback_data="admin_toggle_logs"))
    return markup

def confirmation_menu():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ Onaylıyorum", callback_data="confirm_yes"),
        InlineKeyboardButton("❌ İptal", callback_data="confirm_no")
    )
    return markup

@bot.message_handler(commands=['admin'])
def admin_login_request(message):
    user_id = str(message.from_user.id)
    if user_id in admins:
        bot.send_message(message.chat.id, "🤖 **Sistem Raporu:** Yönetim paneline zaten erişim sağladınız.", reply_markup=admin_menu())
        return
    
    user_state[user_id] = "waiting_password"
    bot.send_message(message.chat.id, "🤖 **Sistem Mesajı:** Yönetim erişimi için lütfen şifreyi giriniz:")

@bot.message_handler(commands=['exit'])
def admin_logout(message):
    user_id = str(message.from_user.id)
    if user_id in admins:
        admins.remove(user_id)
        save_db()
        
        u_name = message.from_user.first_name
        welcome_text = (
            f"👋 **Yönetici Çıkışı Yapıldı, {u_name}**\n"
            f"🆔 Kullanıcı ID: `{user_id}`\n\n"
            "Normal kullanıcı moduna geçtiniz. Sorgulama yapmak için aşağıdaki menüyü kullanabilirsiniz 👇"
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(), parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "🤖 **Sistem Mesajı:** Zaten yönetici modunda değilsiniz.")

@bot.message_handler(commands=['start'])
def user_start(message):
    try:
        user_id = str(message.from_user.id)
        u_name = message.from_user.first_name
        uname_log = f"@{message.from_user.username}" if message.from_user.username else u_name
        
        is_new = user_id not in db
        init_user(user_id, uname_log)
        
        if db[user_id]["is_banned"]:
            bot.send_message(message.chat.id, "Erişim izinleriniz kalıcı olarak askıya alınmıştır.")
            return

        if is_new and live_logs_enabled:
            for adm in admins:
                try: bot.send_message(adm, f"🤖 Yeni kullanıcı: {uname_log} (`{user_id}`)")
                except: pass

        args = message.text.split()
        if len(args) > 1:
            try:
                ref_id = str(args[1])
                if ref_id != user_id and db[user_id]["referred_by"] is None:
                    db[user_id]["referred_by"] = ref_id
                    init_user(ref_id)
                    db[ref_id]["invitees"].add(user_id)
                    save_db()
                    
                    bot.send_message(int(ref_id), f"🤖 Yeni bir davet sağlandı. Toplam referansınız: {len(db[ref_id]['invitees'])}")
                    
                    if live_logs_enabled:
                        for adm in admins:
                            try: bot.send_message(adm, f"🤖 Ref bağlantısı: `{ref_id}` -> {uname_log}")
                            except: pass
            except: pass

        welcome_text = (
            f"👋 **Hoş Geldiniz, {u_name}**\n"
            f"🆔 Kullanıcı ID: `{user_id}`\n\n"
            "Sorgulama yapmak için aşağıdaki menüden ilgili seçeneği tıklayınız 👇"
        )

        if not is_user_member(user_id):
            gate_markup = InlineKeyboardMarkup()
            gate_markup.row(InlineKeyboardButton("📢 Kanala Katıl", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}"))
            gate_markup.row(InlineKeyboardButton("✅ Katılımı Doğrula", callback_data="check_sub"))
            bot.send_message(message.chat.id, welcome_text, reply_markup=gate_markup, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(), parse_mode="Markdown")
    except: pass

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
            bot.send_message(message.chat.id, "🤖 **Erişim Onaylandı:** Yönetici kimliği doğrulandı.", reply_markup=admin_menu())
        else:
            user_state[user_id] = None
            bot.send_message(message.chat.id, "🤖 **Hata:** Geçersiz şifre girdiniz.")

    elif user_id in admins:
        if state == "waiting_broadcast":
            user_state[user_id] = None
            pending_actions[user_id] = {"type": "broadcast", "text": message.text}
            onizleme = f"📣 Duyuru\n━━━━━━━━━━━━━━━━━━\n\n{message.text}"
            bot.send_message(message.chat.id, f"🤖 **Onay Bekliyor:** Tüm kullanıcılara duyuru gönderilecektir.\n\n**Önizleme:**\n{onizleme}\n\nİşlemi onaylıyor musunuz, yoksa iptal mi?", reply_markup=confirmation_menu())

        elif state == "waiting_vip_id":
            target_id = message.text.strip()
            user_state[user_id] = None
            init_user(target_id)
            
            u_current_vip = db[target_id]["is_vip"]
            islem_adi = "ALMA (İptal Etme)" if u_current_vip else "VERME"
            
            pending_actions[user_id] = {"type": "vip_toggle", "target": target_id, "action_mode": not u_current_vip}
            bot.send_message(message.chat.id, f"🤖 **Onay Bekliyor:** `{target_id}` ID'li kullanıcıya VIP **{islem_adi}** işlemi uygulanacaktır. Onaylıyor musunuz?", reply_markup=confirmation_menu())

        elif state == "waiting_ban_id":
            target_id = message.text.strip()
            user_state[user_id] = None
            init_user(target_id)
            
            u_current_ban = db[target_id]["is_banned"]
            islem_adi = "YASAK KALDIRMA" if u_current_ban else "BANLAMA (Engelleme)"
            
            pending_actions[user_id] = {"type": "ban_toggle", "target": target_id, "action_mode": not u_current_ban}
            bot.send_message(message.chat.id, f"🤖 **Onay Bekliyor:** `{target_id}` ID'li kullanıcıya **{islem_adi}** işlemi uygulanacaktır. Onaylıyor musunuz?", reply_markup=confirmation_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    global live_logs_enabled, sorgu_listesi
    try:
        user_id = str(call.from_user.id)
        
        if db.get(user_id, {}).get("is_banned", False) and user_id not in admins:
            bot.answer_callback_query(call.id, "Erişim yetkiniz askıya alınmıştır.", show_alert=True)
            return

        if call.data == "confirm_yes" and user_id in admins:
            action = pending_actions.get(user_id)
            if not action:
                bot.send_message(int(user_id), "🤖 **Hata:** Aktif işlem bulunamadı.")
                return
            
            if action["type"] == "broadcast":
                basarili = 0
                duyuru_sablonu = f"📣 Duyuru\n━━━━━━━━━━━━━━━━━━\n\n{action['text']}"
                for u_id in list(db.keys()):
                    try:
                        bot.send_message(int(u_id), duyuru_sablonu)
                        basarili += 1
                    except: pass 
                bot.send_message(int(user_id), f"🤖 **İşlem Tamamlandı:** Duyuru {basarili} kişiye iletildi.")
            
            elif action["type"] == "vip_toggle":
                try:
                    t_id = action["target"]
                    db[t_id]["is_vip"] = action["action_mode"]
                    save_db()
                    durum = "AKTİF EDİLDİ 👑" if db[t_id]["is_vip"] else "ALINDI ❌"
                    bot.send_message(int(user_id), f"🤖 **İşlem Tamamlandı:** `{t_id}` kullanıcısının VIP yetkisi **{durum}**")
                except: bot.send_message(int(user_id), "🤖 **Hata:** İşlem gerçekleştirilemedi.")
                
            elif action["type"] == "ban_toggle":
                try:
                    t_id = action["target"]
                    db[t_id]["is_banned"] = action["action_mode"]
                    save_db()
                    durum = "ENGELLENDİ 🚫" if db[t_id]["is_banned"] else "ENGEL KALDIRILDI 🟢"
                    bot.send_message(int(user_id), f"🤖 **İşlem Tamamlandı:** `{t_id}` kullanıcısının ban durumu: **{durum}**")
                except: bot.send_message(int(user_id), "🤖 **Hata:** İşlem gerçekleştirilemedi.")

            pending_actions[user_id] = None
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id)
            return

        elif call.data == "confirm_no" and user_id in admins:
            pending_actions[user_id] = None
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(int(user_id), "🤖 **İptal Edildi:** Değişiklik talebi iptal edilmiştir.")
            bot.answer_callback_query(call.id)
            return

        if call.data == "check_sub":
            if is_user_member(user_id):
                try: bot.delete_message(call.message.chat.id, call.message.message_id)
                except: pass
                u_name = call.from_user.first_name
                welcome_text = (
                    f"👋 **Hoş Geldiniz, {u_name}**\n"
                    f"🆔 Kullanıcı ID: `{user_id}`\n\n"
                    "Sorgulama yapmak için aşağıdaki menüden ilgili seçeneği tıklayınız 👇"
                )
                bot.send_message(call.message.chat.id, welcome_text, reply_markup=main_menu(), parse_mode="Markdown")
            else:
                bot.answer_callback_query(call.id, "Üyelik doğrulanamadı. Lütfen önce kanala katılın.", show_alert=True)
                
        elif call.data == "menu_ref":
            ref_count = len(db.get(user_id, {}).get("invitees", set()))
            ref_link = f"https://t.me/{BOT_USERNAME[1:]}?start={user_id}"
            
            ref_panel = (
                "👥 **Davet & Referans Göstergesi**\n\n"
                f"🔗 Davet Linkiniz:\n`{ref_link}`\n\n"
                f"🎯 Hedef Referans: {REQ_REF_COUNT}\n"
                f"📊 Toplam Referans: {ref_count}"
            )
            bot.send_message(call.message.chat.id, ref_panel, parse_mode="Markdown")
            bot.answer_callback_query(call.id)
            
        elif call.data.startswith('sorgu_'):
            sorgu_adi = sorgu_listesi.get(call.data, "Bilinmeyen Sorgu")
            
            if live_logs_enabled:
                uname = f"@{call.from_user.username}" if call.from_user.username else call.from_user.first_name
                for adm in admins:
                    try: bot.send_message(adm, f"👤 {uname} | Seçeneğe Tıklandı ({sorgu_adi})")
                    except: pass
            
            ref_count = len(db.get(user_id, {}).get("invitees", set()))
            if db.get(user_id, {}).get("is_vip", False) or ref_count >= REQ_REF_COUNT or user_id in admins:
                bot.send_message(call.message.chat.id, f"🤖 **Erişim Başarılı:** {sorgu_adi} paneli açıldı.")
            else:
                vip_uyari_metni = (
                    "🔒 **VIP Erişim Gerekli**\n\n"
                    "Bu sorguyu kullanabilmek için VIP üyelik gereklidir.\n"
                    "💎 **VIP Avantajları**\n"
                    "• Tüm sorgulara sınırsız erişim\n"
                    f"📩 VIP satın almak için: {VIP_CONTACT}\n\n"
                    "🎁 **Ücretsiz VIP Fırsatı**\n"
                    f"{REQ_REF_COUNT} arkadaşını davet et, VIP erişimi ücretsiz kazan!\n"
                    f"(Mevcut Referansın: {ref_count}/{REQ_REF_COUNT})"
                )
                bot.send_message(call.message.chat.id, vip_uyari_metni, parse_mode="Markdown")
            bot.answer_callback_query(call.id)

        elif user_id in admins:
            if call.data == "admin_broadcast":
                user_state[user_id] = "waiting_broadcast"
                bot.send_message(int(user_id), "🤖 Gönderilecek toplu duyuru metnini iletiniz:")
                bot.answer_callback_query(call.id)
            elif call.data == "admin_vip_toggle":
                user_state[user_id] = "waiting_vip_id"
                bot.send_message(int(user_id), "🤖 VIP durumu değişecek (Verilecek/Alınacak) kullanıcının Telegram ID'sini iletiniz:")
                bot.answer_callback_query(call.id)
            elif call.data == "admin_ban_toggle":
                user_state[user_id] = "waiting_ban_id"
                bot.send_message(int(user_id), "🤖 Ban durumu değişecek (Banlanacak/Açılacak) kullanıcının Telegram ID'sini iletiniz:")
                bot.answer_callback_query(call.id)
            
            elif call.data == "admin_toggle_logs":
                live_logs_enabled = not live_logs_enabled
                save_db()
                durum_bilgisi = "aktif edildi" if live_logs_enabled else "kapatıldı"
                bot.edit_message_reply_markup(chat_id=int(user_id), message_id=call.message.message_id, reply_markup=admin_menu())
                bot.answer_callback_query(call.id, f"🤖 Canlı log bildirimleri {durum_bilgisi}.", show_alert=True)
            
            elif call.data == "admin_list_users":
                toplam_kullanici = len(db)
                mesaj = (
                    "📊 **SİSTEM İSTATİSTİKLERİ**\n"
                    "━━━━━━━━━━━━━━━━━━━\n\n"
                    f"🤖 **Toplam Kayıtlı Kullanıcı Sayısı:** `{toplam_kullanici}` üye."
                )
                bot.send_message(int(user_id), mesaj, parse_mode="Markdown")
                bot.answer_callback_query(call.id)
    except: pass

if __name__ == "__main__":
    try: bot.delete_webhook()
    except: pass
    
    while True:
        try:
            print("Bot başlatılıyor...")
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            print(f"Bağlantı koptu, 5 saniye sonra yeniden deneniyor: {e}")
            time.sleep(5)
            
