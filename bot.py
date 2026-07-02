import os
import requests
from datetime import datetime, timedelta

# Налаштування змінних (в GitHub Actions ми передамо їх безпечно)
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Координати міст для погоди (Open-Meteo)
CITIES = {
    "Київ": {"lat": 50.45, "lon": 30.52},
    "Гданськ": {"lat": 54.35, "lon": 18.64},
    "Аліканте": {"lat": 38.34, "lon": -0.48},
    "Тенеріфе": {"lat": 28.29, "lon": -16.63}
}

def get_weather():
    weather_report = "🌤 **ПОГОДА НА ЗАВТРА** 🌤\n\n"
    # Нам потрібна погода на завтра, тому вираховуємо дату завтрашнього дня
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    for city, coord in CITIES.items():
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coord['lat']}&longitude={coord['lon']}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
        try:
            res = requests.get(url).json()
            # Шукаємо індекс завтрашнього дня у масиві дат
            dates = res["daily"]["time"]
            if tomorrow in dates:
                idx = dates.index(tomorrow)
            else:
                idx = 1 # якщо щось пішло не так, беремо просто другий елемент
                
            t_max = res["daily"]["temperature_2m_max"][idx]
            t_min = res["daily"]["temperature_2m_min"][idx]
            rain = res["daily"]["precipitation_sum"][idx]
            
            weather_report += f"📍 **{city}**:\n🌡 Від {t_min}°C до {t_max}°C\n🌧 Опади: {rain} мм\n\n"
        except Exception:
            weather_report += f"📍 **{city}**: Не вдалося завантажити дані\n\n"
    return weather_report

def get_currency():
    url = "https://api.monobank.ua/bank/currency"
    currency_report = "💵 **КУРС ВАЛЮТ** 💵\n"
    try:
        res = requests.get(url).json()
        
        # Коди валют ISO 4217: 840 - USD, 978 - EUR, 980 - UAH
        # Шукаємо пари USD/UAH та EUR/UAH
        usd_data = next(item for item in res if item["currencyCodeA"] == 840 and item["currencyCodeB"] == 980)
        eur_data = next(item for item in res if item["currencyCodeA"] == 978 and item["currencyCodeB"] == 980)
        
        # У Монобанку є курс купівлі (rateBuy) та продажу (rateSell)
        # Якщо їх немає (всі дані в одному полі), беремо rateCross
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
