import telebot
from telebot import types
import requests

# توکن رباتت
TOKEN = "8403027857:AAEHINZ5ATTnm1ZNqlIjWEBpbzKPtkHRSOI"
bot = telebot.TeleBot(TOKEN)

# آیدی عددی کانالت
CHANNEL_ID = -1001514472310  

# --- تابع چک عضویت ---
def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# --- سرچ در TMDb ---
TMDB_API_KEY = "69de55af"   # API که دادی
def tmdb_search(query):
    url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&language=en-US&query={query}"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        data = r.json()
        results = []
        for it in data.get("results", []):
            media_type = it.get("media_type")
            if media_type in ["movie", "tv"]:
                results.append({
                    "id": it["id"],
                    "title": it.get("title") or it.get("name"),
                    "year": (it.get("release_date") or it.get("first_air_date") or "")[:4],
                    "media_type": media_type
                })
        return results
    return []

# --- سرچ در Internet Archive ---
def find_archive_mp4(title):
    url = f"https://archive.org/advancedsearch.php?q=title:({title}) AND mediatype:(movies)&output=json"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        data = r.json()
        docs = data.get("response", {}).get("docs", [])
        if docs:
            first = docs[0]
            identifier = first.get("identifier")
            if identifier:
                return {"download_url": f"https://archive.org/download/{identifier}/{identifier}.mp4"}
    return None

# --- هندلر پیام‌ها ---
@bot.message_handler(func=lambda m: True)
def handle_query(m):
    uid = m.from_user.id
    if not is_member(uid):
        join_link = "https://t.me/MOOVVIE"  # لینک مستقیم کانالت
        bot.send_message(uid, f"لطفاً ابتدا عضو کانال شوید:\n{join_link}")
        return

    query = m.text.strip()
    bot.send_message(uid, "⏳ در حال جستجو...")
    results = tmdb_search(query)
    if not results:
        bot.send_message(uid, "نتیجه‌ای در TMDb پیدا نشد. سعی کنید اسم رو دقیق‌تر وارد کنید.")
        return

    markup = types.InlineKeyboardMarkup()
    for it in results:
        label = f"{it['title']}" + (f" ({it['year']})" if it.get('year') else "")
        cb = f"select|{it['media_type']}|{it['id']}|{it['title']}"
        markup.add(types.InlineKeyboardButton(label, callback_data=cb))
    bot.send_message(uid, "نتایج پیدا شد — یکی را انتخاب کن:", reply_markup=markup)

# --- هندلر انتخاب ---
@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("select|"))
def callback_select(call):
    uid = call.from_user.id
    parts = call.data.split("|", 3)
    if len(parts) < 4:
        bot.send_message(uid, "خطا در دیتا.")
        return
    media_type, tmdb_id, tmdb_title = parts[1], parts[2], parts[3]

    if TMDB_API_KEY:
        details_url = f"https://api.themoviedb.org/3/{'movie' if media_type=='movie' else 'tv'}/{tmdb_id}?api_key={TMDB_API_KEY}&language=en-US"
        r = requests.get(details_url, timeout=10)
        if r.status_code == 200:
            movie = r.json()
            title = movie.get('title') or movie.get('name') or tmdb_title
            overview = movie.get('overview', 'توضیحی وجود ندارد.')
            poster = movie.get('poster_path')
            poster_url = f"https://image.tmdb.org/t/p/w500{poster}" if poster else None
            if poster_url:
                bot.send_photo(uid, poster_url, caption=f"🎬 {title}\n\n{overview}")
            else:
                bot.send_message(uid, f"🎬 {title}\n\n{overview}")
        else:
            bot.send_message(uid, f"🎬 {tmdb_title}")
    else:
        bot.send_message(uid, f"🎬 {tmdb_title}")

    bot.send_message(uid, "🔎 دنبال نسخه‌های رایگان قانونی در Internet Archive می‌گردم...")
    found = find_archive_mp4(tmdb_title)
    if found:
        bot.send_message(uid, f"✅ لینک دانلود قانونی:\n{found['download_url']}\n\n(از این لینک می‌تونید مستقیم دانلود کنید.)")
    else:
        bot.send_message(uid, "متأسفم — نسخه قانونی رایگان در Internet Archive پیدا نشد. می‌تونید نام دیگه‌ای امتحان کنید یا از کانال پیگیری کنید.")

# --- اجرا ---
print("Bot started...")
bot.infinity_polling()
