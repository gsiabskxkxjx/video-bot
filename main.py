import os
import requests
import asyncio
import subprocess
import telebot
import edge_tts

BOT_TOKEN = "8607617237:AAFKkeTjLhB7LVQPHBzmu7ERKe8_euMYTrY"
bot = telebot.TeleBot(BOT_TOKEN)

def get_free_ai_text(prompt):
    url = f"https://text.pollinations.ai/{requests.utils.quote(prompt)}"
    system_prompt = "أنت مساعد لتوليد محتوى الفيديوهات. أخرج النتيجة حصراً بهذا النسق بدون مقدمات:\n[VOICEOVER]\n(نص صوتي مشوق باللغة العربية للتعليق الصوتي)\n[CAPTION]\n(كابشن تيك توك مع هاشتاغات)"
    full_url = f"{url}?system={requests.utils.quote(system_prompt)}"
    try:
        res = requests.get(full_url, timeout=15)
        return res.text
    except:
        return f"[VOICEOVER]\nمعلومات وموضوع شيق جداً عن {prompt}، تابع الفيديو للتفاصيل.\n[CAPTION]\n{prompt} 🌟 #تيك_توك #إكسبلور"

async def make_audio(text):
    tts = edge_tts.Communicate(text, voice="ar-EG-SalmaNeural")
    await tts.save("voice.mp3")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    status_msg = bot.reply_to(message, "⏳ جاري توليد المحتوى بالذكاء الاصطناعي...")

    try:
        # 1. توليد النص
        ai_response = get_free_ai_text(message.text)
        if "[VOICEOVER]" in ai_response and "[CAPTION]" in ai_response:
            voice_part = ai_response.split("[VOICEOVER]")[1].split("[CAPTION]")[0].strip()
            caption_part = ai_response.split("[CAPTION]")[1].strip()
        else:
            voice_part = ai_response[:150]
            caption_part = ai_response

        # 2. إنشاء الصوت
        bot.edit_message_text("🎙️ جاري إنشاء التعليق الصوتي...", message.chat.id, status_msg.message_id)
        asyncio.run(make_audio(voice_part))

        # 3. دمج الصوت مع فيديو خلفية سينمائي يتم إنشاؤه تلقائياً بدون تحميل
        bot.edit_message_text("🎬 جاري إنشاء الفيديو والدمج...", message.chat.id, status_msg.message_id)
        
        # أمر FFmpeg يولد خلفية متدرجة متحركة بنمط تيك توك ومقاس عمودي 1080x1920 وبنفس طول الصوت
        cmd = (
            'ffmpeg -y -i voice.mp3 '
            '-f lavfi -i "cellauto=s=1080x1920:rule=30:rate=10,format=pix_fmts=yuv420p" '
            '-c:v libx264 -preset ultrafast -tune animation -c:a aac -b:a 128k -shortest output.mp4'
        )
        subprocess.run(cmd, shell=True, check=True)

        # 4. إرسال الفيديو النهائي
        bot.edit_message_text("📤 جاري رفع الفيديو إليك...", message.chat.id, status_msg.message_id)
        with open("output.mp4", "rb") as video_file:
            bot.send_video(message.chat.id, video_file, caption=caption_part)
            
        bot.delete_message(message.chat.id, status_msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ: {str(e)}", message.chat.id, status_msg.message_id)
    finally:
        for f in ["voice.mp3", "output.mp4"]:
            if os.path.exists(f):
                os.remove(f)

print("البوت السحابي يعمل الآن بنجاح...")
bot.infinity_polling()
