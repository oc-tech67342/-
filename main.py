import os
import asyncio
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands

# --- 1. خادم الويب (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Live!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

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
    print(f'✅ البوت {bot.user} سجل الدخول بنجاح!')
    guilds = [g.name for g in bot.guilds]
    print(f'🌐 السيرفرات المتواجد بها البوت: {guilds}')

    channel = bot.get_channel(AFK_VOICE_CHANNEL_ID)
    if channel:
        print(f'📌 تم العثور على الروم الصوتي: {channel.name}')
        try:
            if bot.voice_clients:
                for vc in bot.voice_clients:
                    if vc.guild == channel.guild:
                        await vc.move_to(channel)
                        break
            else:
                await channel.connect()
            print(f'🔊 دخل البوت بنجاح إلى: {channel.name}')
        except Exception as e:
            print(f'❌ فشل الاتصال بالروم الصوتي: {e}')
    else:
        print(f'❌ لم يتم العثور على روم بالـ ID: {AFK_VOICE_CHANNEL_ID}')

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id != bot.user.id or before.channel == after.channel:
        return

    if after.channel is None or after.channel.id != AFK_VOICE_CHANNEL_ID:
        afk_channel = bot.get_channel(AFK_VOICE_CHANNEL_ID)
        if afk_channel:
            try:
                if member.guild.voice_client:
                    await member.guild.voice_client.move_to(afk_channel)
                else:
                    await afk_channel.connect()
            except Exception as e:
                print(f'⚠️ تعذر إرجاع البوت إلى AFK: {e}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    for mention in message.mentions:
        if mention.id in afk_users:
            reason = afk_users[mention.id]["reason"]
            await message.reply(f"🔇 **{mention.display_name}** غير متواجد (AFK). السبب: {reason}")

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

# --- 3. التشغيل الموحد ---
async def start_services():
    # تشغيل سيرفر Flask في خيط مستقل
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # تشغيل البوت
    if BOT_TOKEN:
        await bot.start(BOT_TOKEN)
    else:
        print("❌ لم يتم العثور على DISCORD_TOKEN!")

if __name__ == "__main__":
    asyncio.run(start_services())
