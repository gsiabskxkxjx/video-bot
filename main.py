import os
import requests
import asyncio
import subprocess
import telebot
import edge_tts
from flask import Flask
from threading import Thread

# تشغيل سيرفر وهمي لإرضاء Render ومنع إغلاق الخدمة
app = Flask('')

@app.route('/')
def home():
    return "Bot is running live!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run_flask).start()

# إعدادات البوت
BOT_TOKEN = "8607617237:AAFKkeTjLhB7LVQPHBzmu7ERKe8_euMYTrY"
bot = telebot.TeleBot(BOT_TOKEN)

BG_URL = "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/head-pose-face-detection-female.mp4"

def get_free_ai_text(prompt):
    try:
        url = f"https://text.pollinations.ai/{requests.utils.quote(prompt)}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200 and "Payment Required" not in res.text:
            return res.text
    except:
        pass
    return f"إليك معلومات سريعة ومهمة حول {prompt}. الصداقة والقيم الإنسانية هي أساس العلاقات الناجحة دائماً."

async def make_audio(text):
    tts = edge_tts.Communicate(text, voice="ar-EG-SalmaNeural")
    await tts.save("voice.mp3")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    status = bot.reply_to(message, "⏳ جاري إنشاء الفيديو...")
    try:
        voice_text = get_free_ai_text(message.text)
        caption_text = f"✨ {voice_text}\n\n#تيك_توك #إكسبلور"

        asyncio.run(make_audio(voice_text))

        r = requests.get(BG_URL)
        with open("bg.mp4", "wb") as f:
            f.write(r.content)

        cmd = "ffmpeg -y -i bg.mp4 -i voice.mp3 -c:v copy -c:a aac -shortest output.mp4"
        subprocess.run(cmd, shell=True, check=True)

        with open("output.mp4", "rb") as video:
            bot.send_video(message.chat.id, video, caption=caption_text)
            
        bot.delete_message(message.chat.id, status.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ: {str(e)}", message.chat.id, status.message_id)
    finally:
        for f in ["voice.mp3", "bg.mp4", "output.mp4"]:
            if os.path.exists(f):
                os.remove(f)

bot.remove_webhook()
print("البوت يعمل بنجاح...")
bot.infinity_polling(skip_pending=True)
