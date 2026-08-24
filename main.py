import os
import requests
import asyncio
import subprocess
import telebot
import edge_tts

BOT_TOKEN = "8607617237:AAFKkeTjLhB7LVQPHBzmu7ERKe8_euMYTrY"
bot = telebot.TeleBot(BOT_TOKEN)

BG_URL = "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/head-pose-face-detection-female.mp4"

def get_free_ai_text(prompt):
    try:
        # استخدام واجهةDuckDuckGo / DDG AI النصية المجانية المباشرة
        url = "https://html.duckduckgo.com/html/"
        # توليد نص بسيط ومباشر
        res = requests.post(
            "https://genai-api.duckduckgo.com/v1/chat",
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "user", "content": f"اكتب نص تعليق صوتي قصير ومشوق باللغة العربية عن: {prompt}"}
                ]
            },
            headers={"x-vnet-bypass": "1"},
            timeout=10
        )
        if res.status_code == 200:
            text = res.json().get("message", "")
            return text
    except:
        pass
    
    # نص افتراضي احتياطي ممتازة في حال تعثر الاتصال
    return f"الصداقة هي إحدى أجمل العلاقات الإنسانية وأعمقها قيمة. الصديق الحقيقي هو السند في الأوقات الصعبة والشريك في اللحظات السعيدة."

async def make_audio(text):
    tts = edge_tts.Communicate(text, voice="ar-EG-SalmaNeural")
    await tts.save("voice.mp3")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    status = bot.reply_to(message, "⏳ جاري إنشاء الفيديو...")
    try:
        # 1. جلب النص
        voice_text = get_free_ai_text(message.text)
        caption_text = f"✨ {message.text}\n\n#تيك_توك #إكسبلور #فيديو"

        # 2. إنشاء الصوت
        asyncio.run(make_audio(voice_text))

        # 3. تحميل خلفية الفيديو
        r = requests.get(BG_URL)
        with open("bg.mp4", "wb") as f:
            f.write(r.content)

        # 4. دمج الصوت مع الفيديو بسرعة وبدون استهلاك ذاكرة
        cmd = "ffmpeg -y -i bg.mp4 -i voice.mp3 -c:v copy -c:a aac -shortest output.mp4"
        subprocess.run(cmd, shell=True, check=True)

        # 5. إرسال الفيديو والنص
        with open("output.mp4", "rb") as video:
            bot.send_video(message.chat.id, video, caption=f"{voice_text}\n\n{caption_text}")
            
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
