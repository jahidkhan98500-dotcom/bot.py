import telebot
import os
from flask import Flask
from threading import Thread

# Web server code for Render port
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run).start()

# আপনার দেওয়া বটের টোকেন
BOT_TOKEN = "8517897909:AAEjONRGCHobp-4i6U_LI5Zi_2FCyCrP_kE"
bot = telebot.TeleBot(BOT_TOKEN)

# আপনার আসল টেলিগ্রাম ইউজার আইডি
OWNER_ID = 8811727356

@bot.message_handler(func=lambda message: message.from_user.id == OWNER_ID)
def control_fake_user(message):
    if message.text.startswith('/say'):
        text_to_send = message.text.replace('/say', '').strip()
        bot.send_message(message.chat.id, text_to_send)

print("বট সফলভাবে চালু হয়েছে...")
bot.infinity_polling()

