import os
import requests
import asyncio
import subprocess
import telebot
import edge_tts

BOT_TOKEN = "8607617237:AAFKkeTjLhB7LVQPHBzmu7ERKe8_euMYTrY"
bot = telebot.TeleBot(BOT_TOKEN)

# رابط فيديو خلفية خفيف ومباشر ثابت
BG_URL = "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/head-pose-face-detection-female.mp4"

def get_free_ai_text(prompt):
    url = f"https://text.pollinations.ai/{requests.utils.quote(prompt)}"
    system_prompt = "أنت مساعد محتوى. أخرج حصراً بهذا الشكل:\n[VOICEOVER]\n(نص تعليق صوتي مشوق قصير)\n[CAPTION]\n(كابشن تيك توك مع هاشتاغات)"
    try:
        res = requests.get(f"{url}?system={requests.utils.quote(system_prompt)}", timeout=10)
        return res.text
    except:
        return f"[VOICEOVER]\nإليك معلومات سريعة ومهمة عن {prompt}.\n[CAPTION]\n#إكسبلور #{prompt}"

async def make_audio(text):
    tts = edge_tts.Communicate(text, voice="ar-EG-SalmaNeural")
    await tts.save("voice.mp3")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    status = bot.reply_to(message, "⏳ جاري إنشاء الفيديو...")
    try:
        # 1. الذكاء الاصطناعي
        text_data = get_free_ai_text(message.text)
        if "[VOICEOVER]" in text_data and "[CAPTION]" in text_data:
            voice_part = text_data.split("[VOICEOVER]")[1].split("[CAPTION]")[0].strip()
            caption_part = text_data.split("[CAPTION]")[1].strip()
        else:
            voice_part = text_data[:100]
            caption_part = text_data

        # 2. الصوت
        asyncio.run(make_audio(voice_part))

        # 3. تحميل فيديو خفيف جداً
        r = requests.get(BG_URL)
        with open("bg.mp4", "wb") as f:
            f.write(r.content)

        # 4. دمج سريع بأقل استهلاك للذاكرة
        cmd = "ffmpeg -y -i bg.mp4 -i voice.mp3 -c:v copy -c:a aac -shortest output.mp4"
        subprocess.run(cmd, shell=True, check=True)

        # 5. إرسال
        with open("output.mp4", "rb") as video:
            bot.send_video(message.chat.id, video, caption=caption_part)
            
        bot.delete_message(message.chat.id, status.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ: {str(e)}", message.chat.id, status.message_id)
    finally:
        for f in ["voice.mp3", "bg.mp4", "output.mp4"]:
            if os.path.exists(f):
                os.remove(f)

# تصفية التحديثات القديمة لمنع خطأ 409
bot.remove_webhook()
print("البوت يعمل بنجاح...")
bot.infinity_polling(skip_pending=True)
