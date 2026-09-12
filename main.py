import os
import asyncio
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands

# --- 1. خادم ويب اختياري (يزيله إن لم يكن لديك حاجة) ---
app = Flask('')


@app.route('/')
def home():
    return "Bot is online!"


def run():
    app.run(host='0.0.0.0', port=10000)


def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()


# --- 2. إعدادات البوت ---
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
AFK_VOICE_CHANNEL_ID = 1350135312013201450

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
afk_users = {}


@bot.event
async def on_ready():
    print(f'✅ البوت {bot.user} متصل بالشبكة بنجاح!')
    channel = bot.get_channel(AFK_VOICE_CHANNEL_ID)
    if not channel:
        print(f'❌ لم يتم العثور على الروم ID: {AFK_VOICE_CHANNEL_ID}')
        return

    print(f'📌 جاري محاولة الاتصال بالروم الصوتي: {channel.name}')
    try:
        if not channel.guild.voice_client:
            await channel.connect(reconnect=True, timeout=30.0)
        else:
            await channel.guild.voice_client.move_to(channel)
        print(f'🔊 دخل البوت بنجاح إلى: {channel.name}')
    except Exception as e:
        print(f'❌ خطأ أثناء الاتصال الصوتي (تأكد من PyNaCl والصلاحيات): {e}')


@bot.event
async def on_voice_state_update(member, before, after):
    # أعد البوت تلقائياً إلى روم AFK إذا أُخرج أو نُقل
    if member.id != bot.user.id:
        return

    if after.channel is not None and after.channel.id == AFK_VOICE_CHANNEL_ID:
        return

    afk_channel = bot.get_channel(AFK_VOICE_CHANNEL_ID)
    if not afk_channel:
        return

    try:
        if member.guild.voice_client:
            await member.guild.voice_client.move_to(afk_channel)
        else:
            await afk_channel.connect(reconnect=True, timeout=30.0)
    except Exception as e:
        print(f'⚠️ تعذر إعادة البوت لـ AFK: {e}')


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # الرد عند مناداة شخص في وضع AFK
    for mention in message.mentions:
        if mention.id in afk_users:
            reason = afk_users[mention.id]["reason"]
            await message.reply(f"🔇 **{mention.display_name}** غير متواجد (AFK). السبب: {reason}")

    # إلغاء وضع AFK عند إرسال رسالة
    if message.author.id in afk_users:
        member = message.author
        data = afk_users.pop(member.id)
        original_channel = data.get("original_channel")
        original_nick = data.get("original_nick")

        try:
            await member.edit(nick=original_nick)
        except discord.Forbidden:
            pass

        if member.voice and member.voice.channel and member.voice.channel.id == AFK_VOICE_CHANNEL_ID and original_channel:
            try:
                await member.move_to(original_channel)
                await message.channel.send(f"🔊 تم إرجاع **{member.display_name}** إلى قناته الأصلية.")
            except Exception as e:
                await message.channel.send(f"⚠️ خطأ في إرجاع الصوت: {e}")

        await message.channel.send(f"👋 مرحبًا بعودتك **{member.display_name}**! تم إلغاء وضع AFK.")

    await bot.process_commands(message)


@bot.command()
async def afk(ctx, *, reason: str = "لم يحدد سببًا."):
    member = ctx.author
    original_nick = member.nick
    original_channel = member.voice.channel if member.voice else None

    if member.voice and member.voice.channel:
        afk_channel = bot.get_channel(AFK_VOICE_CHANNEL_ID)
        if afk_channel:
            try:
                await member.move_to(afk_channel)
                await ctx.send(f"🔇 تم نقل **{member.display_name}** إلى قناة AFK.")
            except Exception as e:
                await ctx.send(f"⚠️ خطأ أثناء النقل الصوتي: {e}")
                return

    try:
        new_nick = f"[AFK] {member.display_name}"[:32]
        await member.edit(nick=new_nick)
    except discord.Forbidden:
        pass

    afk_users[member.id] = {
        "reason": reason,
        "original_channel": original_channel,
        "original_nick": original_nick
    }
    await ctx.send(f"✅ **{member.display_name}** دخل وضع AFK. السبب: {reason}")


# --- 3. التشغيل ---
if __name__ == "__main__":
    keep_alive()
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
    else:
        print("❌ لم يتم العثور على DISCORD_TOKEN في متغيرات البيئة!")
