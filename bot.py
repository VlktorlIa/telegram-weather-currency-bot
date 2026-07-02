import os
import requests
from datetime import datetime, timedelta

# Налаштування змінних
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Координати міст для погоди (Open-Meteo)
CITIES = {
    "Київ": {"lat": 50.45, "lon": 30.52},
    "Гданськ": {"lat": 54.35, "lon": 18.64},
    "Аліканте": {"lat": 38.34, "lon": -0.48},
    "Тенеріфе": {"lat": 28.29, "lon": -16.63}
}

# Функція для перетворення цифрового коду Open-Meteo у текстовий опис з емодзі
def get_weather_description(code):
    mapping = {
        0: "☀️ Ясно / Сонячно",
        1: "🌤 Переважно ясно",
        2: "⛅️ Мінлива хмарність",
        3: "☁️ Похмуро",
        45: "🌫 Туман", 48: "🌫 Туман із памороззю",
        51: "🌧 Мряка легка", 53: "🌧 Мряка помірна", 55: "🌧 Мряка густа",
        61: "🌧 Невеликий дощ", 63: "🌧 Помірний дощ", 65: "🌧 Сильний дощ",
        71: "❄️ Невеликий сніг", 73: "❄️ Помірний сніг", 75: "❄️ Сильний сніг",
        77: "❄️ Сніжна крупа",
        80: "🌧 Короткочасний дощ", 81: "🌧 Злива", 82: "🌧 Сильна злива",
        85: "❄️ Короткочасний сніг", 86: "❄️ Сильний снігопад",
        95: "⛈ Гроза", 96: "⛈ Гроза з легким градом", 99: "⛈ Гроза з сильним градом"
    }
    return mapping.get(code, "🤷 Наче нормальна погода")

def get_weather():
    weather_report = "🌤 **ПОГОДА НА ЗАВТРА** 🌤\n\n"
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    for city, coord in CITIES.items():
        # Додаємо параметр weather_code у запит до API
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coord['lat']}&longitude={coord['lon']}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code&timezone=auto"
        try:
            res = requests.get(url).json()
            dates = res["daily"]["time"]
            if tomorrow in dates:
                idx = dates.index(tomorrow)
            else:
                idx = 1
                
            t_max = res["daily"]["temperature_2m_max"][idx]
            t_min = res["daily"]["temperature_2m_min"][idx]
            rain = res["daily"]["precipitation_sum"][idx]
            w_code = res["daily"]["weather_code"][idx] # Отримуємо код погоди
            
            # Отримуємо гарний опис на основі коду
            weather_desc = get_weather_description(w_code)
            
            weather_report += f"📍 **{city}**:\n📝 Статус: {weather_desc}\n🌡 Від {t_min}°C до {t_max}°C\n🌧 Опади: {rain} мм\n\n"
        except Exception:
            weather_report += f"📍 **{city}**: Не вдалося завантажити дані\n\n"
    return weather_report

def get_currency():
    url = "https://api.monobank.ua/bank/currency"
    currency_report = "💵 **КУРС ВАЛЮТ** 💵\n"
    try:
        res = requests.get(url).json()
        usd_data = next(item for item in res if item["currencyCodeA"] == 840 and item["currencyCodeB"] == 980)
        eur_data = next(item for item in res if item["currencyCodeA"] == 978 and item["currencyCodeB"] == 980)
        
        usd_buy = usd_data.get("rateBuy", usd_data.get("rateCross"))
        usd_sell = usd_data.get("rateSell", usd_data.get("rateCross"))
        
        eur_buy = eur_data.get("rateBuy", eur_data.get("rateCross"))
        eur_sell = eur_data.get("rateSell", eur_data.get("rateCross"))
        
        currency_report += f"🇺🇸 Долар (USD):\n🔹 Купівля: {usd_buy:.2f} грн | 🔸 Продаж: {usd_sell:.2f} грн\n\n"
        currency_report += f"🇪🇺 Євро (EUR):\n🔹 Купівля: {eur_buy:.2f} грн | 🔸 Продаж: {eur_sell:.2f} грн\n\n"
    except Exception as e:
        print(f"Помилка валюти: {e}")
        currency_report += "Не вдалося завантажити курс валют\n\n"
    return currency_report

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    if not BOT_TOKEN or not CHAT_ID:
        print("Помилка: Не вказано токени бота або ID чату!")
        exit(1)
        
    message = get_currency() + get_weather()
    send_to_telegram(message)
    print("Повідомлення успішно надіслано!")
