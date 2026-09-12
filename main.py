import os
import threading
import urllib.request
import time

import discord
from flask import Flask

TOKEN = os.environ.get("DISCORD_TOKEN", "") or "ضع_توكن_البوت_هنا"

AFK_VOICE_CHANNEL_ID = 1350135312013201450
TARGET_VOICE_CHANNEL_ID = None

BOT_NAME = "SMH Bots || Afk"

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True

bot = discord.Client(intents=intents)
app = Flask(__name__)


@app.route("/")
@app.route("/health")
def health():
    return "AFK bot is alive"


def keep_alive():
    def ping():
        while True:
            try:
                urllib.request.urlopen("https://afk-bot-o71y.onrender.com", timeout=60)
            except Exception:
                pass
            time.sleep(240)
    threading.Thread(target=ping, daemon=True).start()


@bot.event
async def on_ready():
    print(f"✅ البوت {BOT_NAME} متصل بالشبكة بنجاح!")
    if not bot.guilds:
        print("❌ البوت ليس في أي سيرفر")
        return
    guild = bot.guilds[0]
    afk_channel = guild.get_channel(AFK_VOICE_CHANNEL_ID)
    if afk_channel is None:
        print("❌ الروم الصوتي غير موجود - تأكد من الـ ID")
        return
    print(f"📌 جاري محاولة الاتصال بالروم الصوتي: {afk_channel.name}")
    try:
        await afk_channel.connect()
        print(f"🔊 دخل البوت بنجاح إلى: {afk_channel.name}")
    except Exception as e:
        print(f"❌ خطأ أثناء الاتصال الصوتي (تأكد من PyNaCl والصلاحيات): {e}")


@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel is None or after.channel.id != AFK_VOICE_CHANNEL_ID:
        return
    if member.id == bot.user.id:
        return
    if before.channel is not None and before.channel.id == AFK_VOICE_CHANNEL_ID:
        return
    target = None
    if TARGET_VOICE_CHANNEL_ID:
        target = member.guild.get_channel(TARGET_VOICE_CHANNEL_ID)
    if target is None:
        target = before.channel
    if target is None or target.id == after.channel.id:
        return
    try:
        await member.move_to(target)
        print(f"🔁 تم نقل {member.display_name} إلى {target.name}")
    except Exception as e:
        print(f"❌ فشل نقل {member.display_name}: {e}")


def run_web():
    app.run(host="0.0.0.0", port=10000)


if __name__ == "__main__":
    keep_alive()
    threading.Thread(target=run_web, daemon=True).start()
    bot.run(TOKEN)
