import telebot
import schedule
import time
import threading
from tradingview_ta import TA_Handler, Interval
   
# --- НАСТРОЙКИ ---
BOT_TOKEN = "7815302546:AAGFjoJ1NUfUvS2bAzRUwUWV8WDiFm_3Om8"
CHANNEL_ID = "-1002147764781" # Этот ID остается для отправки сигналов

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Глобальная переменная для хранения последней цены
previous_price = 0

# --- ЛОГИКА ПОЛУЧЕНИЯ ЦЕНЫ И ОТПРАВКИ СИГНАЛОВ (без изменений) ---

def get_gold_price_from_tradingview():
    """Получает текущую цену золота (XAUUSD) с TradingView."""
    try:
        gold = TA_Handler(
            symbol="XAUUSD",
            screener="cfd",
            exchange="FX_IDC",
            interval=Interval.INTERVAL_1_MINUTE
        )
        analysis = gold.get_analysis()
        current_price = analysis.indicators.get('close')
        if current_price:
            return round(current_price, 2)
        return None
    except Exception as e:
        print(f"Ошибка при получении данных с TradingView: {e}")
        return None

def send_signal():
    """Формирует и отправляет один сигнал в канал."""
    global previous_price
    print("Запрашиваю цену на золото...")
    current_price = get_gold_price_from_tradingview()

    if current_price is not None:
        if previous_price == 0:
            previous_price = current_price
            message = f"🪙 **Сигнал жіберудің бастамасы.**\nҚазіргі алтыннын бағасы: (XAU/USD): ${current_price}."
        elif current_price > previous_price:
            change = round(current_price - previous_price, 2)
            message = f"🔼 LONG\n\nАлтыннын бағасы өсті: **${current_price}** (+${change})"
        elif current_price < previous_price:
            change = round(previous_price - current_price, 2)
            message = f"🔽 SHORT\n\nАлтыннын бағасы түсті: **${current_price}** (-${change})"
        else:
            message = f"↔️ **Баға өзгермеді:** ${current_price}"

        try:
            bot.send_message(CHANNEL_ID, message, parse_mode='Markdown')
            print(f"Сигнал успешно отправлен.")
        except Exception as e:
            print(f"Не удалось отправить сообщение: {e}")

        previous_price = current_price

def start_signal_sequence():
    """Запускает последовательность из 5 сигналов."""
    global previous_price
    print("Время 21:00. Начинаю отправку 5 сигналов.")
    previous_price = 0
    for i in range(5):
        print(f"--- Отправка сигнала #{i+1}/5 ---")
        send_signal()
        if i < 4:
            print("Ожидаю 5 минут...")
            time.sleep(300)
    print("Все 5 сигналов отправлены. Ожидаю завтра.")

# --- ОБРАБОТЧИКИ КОМАНД ДЛЯ БОТА ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Ответ на команду /start."""
    bot.reply_to(message, 
        "Сәлем! Мен сигнал жіберетін ботпын.\n\n"
        "Командылар:\n"
        "/start_m - 21:00-де сигнал жіберуді бастайды.\n"
        "/stop_m - Сигнал жіберуді тоқтатады."
    )

@bot.message_handler(commands=['start_m'])
def start_monitoring(message):
    """Активирует ежедневную отправку сигналов."""
    # Очищаем старые задачи, чтобы не было дубликатов
    schedule.clear()
    # Ставим новую задачу
    schedule.every().day.at("21:00").do(start_signal_sequence)
    bot.reply_to(message, "✅ Мониторинг іске қосылды! Сигналдар күнде 21:00-де жіберіліп бастайды.")
    print("Задача на 21:00 установлена.")

@bot.message_handler(commands=['stop_m'])
def stop_monitoring(message):
    """Останавливает все запланированные задачи."""
    schedule.clear()
    bot.reply_to(message, "⏹️ Мониторинг тоқтатылды. Мен сигнал жібермеймін.")
    print("Все задачи удалены.")

# --- ФУНКЦИЯ ДЛЯ РАБОТЫ ПЛАНИРОВЩИКА В ОТДЕЛЬНОМ ПОТОКЕ ---

def run_scheduler():
    """Бесконечный цикл для проверки и запуска задач по расписанию."""
    while True:
        schedule.run_pending()
        time.sleep(1)

# --- ГЛАВНЫЙ БЛОК ЗАПУСКА ---
if __name__ == "__main__":
    print("Бот запускается...")
    # Запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
    
    print("Бот запущен и готов принимать команды.")
    # Запускаем прием сообщений от Telegram (этот процесс блокирующий)
    bot.polling(none_stop=True)