import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# Налаштування змінних
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

CITIES = {
    "Київ": {"lat": 50.45, "lon": 30.52},
    "Гданськ": {"lat": 54.35, "lon": 18.64},
    "Аліканте": {"lat": 38.34, "lon": -0.48},
    "Тенеріфе": {"lat": 28.29, "lon": -16.63}
}

def get_weather_description(code):
    mapping = {
        0: "☀️ Ясно / Сонячно", 1: "🌤 Переважно ясно", 2: "⛅️ Мінлива хмарність", 3: "☁️ Похмуро",
        45: "🌫 Туман", 48: "🌫 Туман із памороззю", 51: "🌧 Мряка легка", 53: "🌧 Мряка помірна",
        55: "🌧 Мряка густа", 61: "🌧 Невеликий дощ", 63: "🌧 Помірний дощ", 65: "🌧 Сильний дощ",
        71: "❄️ Невеликий сніг", 73: "❄️ Помірний сніг", 75: "❄️ Сильний сніг",
        80: "🌧 Короткочасний дощ", 81: "🌧 Злива", 82: "🌧 Сильна злива",
        95: "⛈ Гроза", 96: "⛈ Гроза з легким градом", 99: "⛈ Гроза з сильним градом"
    }
    return mapping.get(code, "🤷 Наче нормальна погода")

def get_weather():
    weather_report = "🌤 **ПОГОДА НА ЗАВТРА** 🌤\n\n"
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    for city, coord in CITIES.items():
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coord['lat']}&longitude={coord['lon']}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code&timezone=auto"
        try:
            res = requests.get(url).json()
            dates = res["daily"]["time"]
            idx = dates.index(tomorrow) if tomorrow in dates else 1
                
            t_max = res["daily"]["temperature_2m_max"][idx]
            t_min = res["daily"]["temperature_2m_min"][idx]
            rain = res["daily"]["precipitation_sum"][idx]
            w_code = res["daily"]["weather_code"][idx]
            
            weather_desc = get_weather_description(w_code)
            weather_report += f"📍 **{city}**:\n{weather_desc}\n🌡 Від {t_min}°C до {t_max}°C\n🌧 Опади: {rain} мм\n\n"
        except Exception:
            weather_report += f"📍 **{city}**: Не вдалося завантажити дані\n\n"
    return weather_report

def get_currency():
    url = "https://api.monobank.ua/bank/currency"
    currency_report = "💵 **КУРС ВАЛЮТ** 💵\n\n"
    try:
        res = requests.get(url).json()
        usd_data = next(item for item in res if item["currencyCodeA"] == 840 and item["currencyCodeB"] == 980)
        eur_data = next(item for item in res if item["currencyCodeA"] == 978 and item["currencyCodeB"] == 980)
        
        usd_buy = usd_data.get("rateBuy", usd_data.get("rateCross"))
        usd_sell = usd_data.get("rateSell", usd_data.get("rateCross"))
        eur_buy = eur_data.get("rateBuy", eur_data.get("rateCross"))
        eur_sell = eur_data.get("rateSell", eur_data.get("rateCross"))
        
        currency_report += f"🇺🇸 **Долар (USD):**\n🔹 Купівля: {usd_buy:.2f} грн\n🔸 Продаж: {usd_sell:.2f} грн\n\n"
        currency_report += f"🇪🇺 **Євро (EUR):**\n🔹 Купівля: {eur_buy:.2f} грн\n🔸 Продаж: {eur_sell:.2f} грн\n\n"
    except Exception as e:
        print(f"Помилка валюти: {e}")
        currency_report += "Не вдалося завантажити курс валют\n\n"
    return currency_report

def get_ai_news():
    if not GEMINI_KEY:
        return ""
        
    news_report = "📰 **ГОЛОВНІ НОВИНИ (ШІ)** 📰\n\n"
    try:
        # Читаємо стрічку новин
        rss_url = "https://www.ukrinform.ua/rss/block-lastnews"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(rss_url, headers=headers)
        
        root = ET.fromstring(response.content)
        raw_news_list = []
        for item in root.findall(".//item")[:15]:
            title = item.find("title").text
            raw_news_list.append(f"- {title}")
            
        all_titles = "\n".join(raw_news_list)
        
        # ПРЯМИЙ СПОСІБ: робимо звичайний HTTP-запит до API Google без використання їхньої примхливої бібліотеки
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        
        prompt = (
            "Перед тобою список свіжих новин. Обери з них 3 найважливіші головні події в Україні чи світі "
            "(ігноруй дрібні регіональні чи суто побутові теми) та сформуй короткий аналітичний дайджест українською мовою. "
            "Кожну з 3 подій опиши рівно одним лаконічним і зрозумілим реченням, яке передає суть події. "
            "Починай кожну новину з нового рядка з відповідного тематичного емодзі. "
            "Пиши чітко, структуровано, без будь-яких привітань, вступів чи підсумкових слів від себе."
            f"\n\nСписок новин:\n{all_titles}"
        )
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        # Відправляємо запит
        ai_res = requests.post(gemini_url, json=payload).json()
        
        # Дістаємо згенерований текст відповіді
        ai_text = ai_res['candidates'][0]['content']['parts'][0]['text']
        news_report += ai_text + "\n"
        
    except Exception as e:
        print(f"Помилка ШІ: {e}")
        news_report += "Не вдалося сформувати дайджест новин через ШІ.\n\n"
    return news_report

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

if __name__ == "__main__":
    if not BOT_TOKEN or not CHAT_ID:
        print("Помилка токенів!")
        exit(1)
        
    message = get_currency() + get_weather() + get_ai_news()
    send_to_telegram(message)
    print("Повідомлення успішно надіслано!")
