import os
import logging
import telebot
import psycopg2
from flask import Flask, request

from config import *

# Налаштування з'єднання з базою даних PostgreSQL
DATABASE_URL = ''
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

# Налаштування журналювання
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Створення екземпляру бота
bot = telebot.TeleBot(TOKEN)

# Створення Flask-додатку
app = Flask(__name__)

# Обробник вхідних HTTP-запитів
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok', 200

# Функція обробник команди /start
@bot.message_handler(commands=['start'])
def start(message):
    username = message.from_user.username
    bot.reply_to(message,f'Здоров {username}')

# Функція обробник повідомлень з фото
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    photo = message.photo[-1]  # Отримуємо останнє надіслане фото
    caption = message.caption  # Отримуємо підпис до фото (опис речі)
    url = message.text  # Отримуємо посилання на сайт

    # Збереження фото, опису та посилання до бази даних
    cursor.execute("INSERT INTO items (photo_id, caption, url) VALUES (%s, %s, %s)", (photo.file_id, caption, url))
    conn.commit()

    bot.send_message(chat_id=message.chat.id, text="Річ успішно додана до магазину!")

# Функція обробник команди /shop
@bot.message_handler(commands=['shop'])
def shop(message):
    # Отримання всіх речей з бази даних
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()

    # Створення інлайн-кнопок для вибору речей
    buttons = []
    for item in items:
        buttons.append(telebot.types.InlineKeyboardButton(item[2], callback_data=str(item[0])))

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(*buttons)

    bot.send_message(chat_id=message.chat.id, text="Виберіть річ, яку бажаєте купити:", reply_markup=keyboard)

# Функція обробник натискання на кнопку
@bot.callback_query_handler(func=lambda call: True)
def button_click(call):
    item_id = call.data

    # Отримання інформації про річ за її ідентифікатором
    cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    item = cursor.fetchone()

    # Відправка користувача на сайт для покупки
    bot.send_message(chat_id=call.message.chat.id, text=f"Ви обрали річ: {item[2]}")
    bot.send_message(chat_id=call.message.chat.id, text="Для здійснення покупки перейдіть за посиланням:")
    bot.send_message(chat_id=call.message.chat.id, text=item[4])

# Функція обробник помилкових вказівок
@bot.message_handler(func=lambda message: True)
def error(message):
    logging.error(f"Update {message} caused error")

# Запуск Flask-додатку
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    server.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))