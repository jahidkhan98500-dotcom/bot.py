import telebot
import os
import time
from flask import Flask
from threading import Thread
from telebot import types

# Web server for Render 24/7 uptime
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run).start()

# বটের কনফিগারেশন
BOT_TOKEN = "8517897909:AAEjONRGCHobp-4i6U_LI5Zi_2FCyCrP_kE"
bot = telebot.TeleBot(BOT_TOKEN)

OWNER_ID = 8811727356

# ডাটা সংরক্ষণের জন্য
scheduled_posts = []
TARGET_GROUP_ID = None

# ব্যাকগ্রাউন্ড শিডিউলার (টেক্সট, ছবি ও ভিডিও টাইম অনুযায়ী পাঠানোর জন্য)
def scheduler():
    global TARGET_GROUP_ID
    while True:
        current_time = time.time()
        for post in scheduled_posts[:]:
            if current_time >= post['post_time']:
                if TARGET_GROUP_ID:
                    try:
                        if post['type'] == 'text':
                            bot.send_message(TARGET_GROUP_ID, post['content'])
                        elif post['type'] == 'photo':
                            bot.send_photo(TARGET_GROUP_ID, post['content'], caption=post.get('caption', ''))
                        elif post['type'] == 'video':
                            bot.send_video(TARGET_GROUP_ID, post['content'], caption=post.get('caption', ''))
                    except Exception as e:
                        print(f"Error posting: {e}")
                scheduled_posts.remove(post)
        time.sleep(5)

Thread(target=scheduler, daemon=True).start()

# গ্রুপে কাজ করার হ্যান্ডলার
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
def handle_group(message):
    global TARGET_GROUP_ID
    TARGET_GROUP_ID = message.chat.id
    
    # ওনার গ্রুপে /say লিখলে কমান্ড ডিলিট করে মেসেজ পাঠাবে
    if message.from_user.id == OWNER_ID and message.text and message.text.startswith('/say'):
        text_to_send = message.text.replace('/say', '').strip()
        bot.send_message(message.chat.id, text_to_send)
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except Exception:
            pass

# ইনবক্সে ওনারের জন্য ইন্টারেক্টিভ এডমিন প্যানেল ও কমান্ড
@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.from_user.id == OWNER_ID)
def private_admin_panel(message):
    if message.text in ['/start', '/panel']:
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("📊 বট স্ট্যাটাস", callback_data="status")
        btn2 = types.InlineKeyboardButton("📋 পেন্ডিং লিস্ট", callback_data="list_posts")
        btn3 = types.InlineKeyboardButton("ℹ️ ব্যবহারের নিয়ম", callback_data="help")
        markup.add(btn1, btn2, btn3)
        
        bot.send_message(
            message.chat.id, 
            "👑 **বট এডমিন কন্ট্রোল প্যানেল**\n\nনিচের অপশনগুলোতে ক্লিক করে ম্যানেজ করুন অথবা সরাসরি কমান্ড দিন:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    elif message.text.startswith('/post'):
        try:
            parts = message.text.split(' ', 2)
            minutes = int(parts[1])
            post_text = parts[2]
            post_time = time.time() + (minutes * 60)
            
            scheduled_posts.append({
                'type': 'text',
                'content': post_text,
                'post_time': post_time
            })
            bot.reply_to(message, f"✅ টেক্সট সফলভাবে শিডিউল হয়েছে! {minutes} মিনিট পর গ্রুপে যাবে।")
        except Exception:
            bot.reply_to(message, "❌ ভুল ফরম্যাট! ব্যবহার করুন:\n`/post <মিনিট> <আপনার মেসেজ>`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "প্যানেল ওপেন করতে `/panel` লিখুন।")

# ছবি বা ভিডিও ইনবক্সে রিসিভ করে শিডিউল করার হ্যান্ডলার
@bot.message_handler(content_types=['photo', 'video'], func=lambda message: message.chat.type == 'private' and message.from_user.id == OWNER_ID)
def handle_media_post(message):
    caption = message.caption or ""
    if caption.startswith('/schedule'):
        try:
            parts = caption.split(' ', 1)
            minutes = int(parts[1])
            post_time = time.time() + (minutes * 60)
            
            if message.photo:
                file_id = message.photo[-1].file_id
                media_type = 'photo'
            else:
                file_id = message.video.file_id
                media_type = 'video'
            
            scheduled_posts.append({
                'type': media_type,
                'content': file_id,
                'caption': "",
                'post_time': post_time
            })
            bot.reply_to(message, f"✅ মিডিয়া ফাইল সফলভাবে শিডিউল হয়েছে! {minutes} মিনিট পর গ্রুপে যাবে।")
        except Exception:
            bot.reply_to(message, "❌ সঠিক নিয়মে ছবির ক্যাপশনে লিখুন: `/schedule <মিনিট>` (যেমন: `/schedule 10`)")
    else:
        bot.reply_to(message, "🖼️ ছবি বা ভিডিও শিডিউল করতে মিডিয়াটি পাঠিয়ে **ক্যাপশনে** লিখুন:\n`/schedule <মিনিট>`")

# ইনলাইন বাটন ক্লিকের কাজগুলো
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "status":
        group_status = f"`{TARGET_GROUP_ID}`" if TARGET_GROUP_ID else "সংযুক্ত হয়নি"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"📊 **বট স্ট্যাটাস:**\n\n• টার্গেট গ্রুপ আইডি: {group_status}\n• জমা থাকা পোস্ট: {len(scheduled_posts)}টি", parse_mode="Markdown")
    elif call.data == "list_posts":
        bot.answer_callback_query(call.id)
        if not scheduled_posts:
            bot.send_message(call.message.chat.id, "📭 বর্তমানে কোনো পোস্ট শিডিউল করা নেই।")
        else:
            text = "📋 **পেন্ডিং পোস্ট লিস্ট:**\n\n"
            for i, p in enumerate(scheduled_posts, 1):
                rem_min = max(1, int((p['post_time'] - time.time()) / 60))
                text += f"{i}. টাইপ: `{p['type']}` | প্রায় {rem_min} মিনিট পর যাবে\n"
            bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    elif call.data == "help":
        bot.answer_callback_query(call.id)
        help_msg = (
            "📖 **এডমিন গাইডলাইন:**\n\n"
            "1️⃣ **টেক্সট শিডিউল:**\n`/post <মিনিট> <মেসেজ>`\n\n"
            "2️⃣ **ছবি/ভিডিও শিডিউল:**\nইনবক্সে ছবি/ভিডিও পাঠিয়ে ক্যাপশনে লিখুন: `/schedule <মিনিট>`\n\n"
            "3️⃣ **ইনলাইন প্যানেল:**\nসবসময় মেনু দেখতে `/panel` লিখুন।"
        )
        bot.send_message(call.message.chat.id, help_msg, parse_mode="Markdown")

print("বট সফলভাবে চালু হয়েছে...")
bot.infinity_polling()
