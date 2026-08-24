import os
import requests
import asyncio
import subprocess
import telebot
import edge_tts
from flask import Flask
from threading import Thread

# 1. تشغيل سيرفر وهمي لإرضاء Render
app = Flask('')

@app.route('/')
def home():
    return "Bot is running live!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_flask, daemon=True).start()

# 2. إعدادات البوت
BOT_TOKEN = "8607617237:AAFKkeTjLhB7LVQPHBzmu7ERKe8_euMYTrY"
bot = telebot.TeleBot(BOT_TOKEN)

BG_URL = "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/head-pose-face-detection-female.mp4"

def generate_ai_script(prompt):
    """توليد كابشن وتعليق صوتي خالي من أخطاء الـ API"""
    clean_prompt = prompt.strip()
    
    # نص تعليق صوتي غني ومشوق يناسب طلب المستخدم
    voice_over = (
        f"هل تساءلت يوماً عن أهمية {clean_prompt}؟ "
        f"إن الحديث عن {clean_prompt} يعكس جوانب عميقة ومهمة في حياتنا اليومية. "
        f"التفاصيل الصغيرة هي التي تصنع الفرق دائماً."
    )
    
    caption = (
        f"✨ فيديو حول: {clean_prompt}\n\n"
        f"💬 {voice_over}\n\n"
        f"#تيك_توك #إكسبلور #{clean_prompt.replace(' ', '_')}"
    )
    
    return voice_over, caption

async def make_audio(text):
    tts = edge_tts.Communicate(text, voice="ar-EG-SalmaNeural")
    await tts.save("voice.mp3")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    status = bot.reply_to(message, "⏳ جاري توليد المحتوى والتصميم...")
    try:
        # 1. توليد النصوص
        voice_part, caption_part = generate_ai_script(message.text)

        # 2. إنشاء الصوت
        asyncio.run(make_audio(voice_part))

        # 3. تحميل فيديو الخلفية
        r = requests.get(BG_URL, timeout=15)
        with open("bg.mp4", "wb") as f:
            f.write(r.content)

        # 4. الدمج السريع بواسطة FFmpeg
        cmd = "ffmpeg -y -i bg.mp4 -i voice.mp3 -c:v copy -c:a aac -shortest output.mp4"
        subprocess.run(cmd, shell=True, check=True)

        # 5. إرسال الفيديو النهائي
        with open("output.mp4", "rb") as video:
            bot.send_video(message.chat.id, video, caption=caption_part)
            
        bot.delete_message(message.chat.id, status.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ أثناء المعالجة: {str(e)}", message.chat.id, status.message_id)
    finally:
        for f in ["voice.mp3", "bg.mp4", "output.mp4"]:
            if os.path.exists(f):
                os.remove(f)

bot.remove_webhook()
print("البوت يعمل بنجاح...")
bot.infinity_polling(skip_pending=True)
