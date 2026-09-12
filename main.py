import os
import asyncio
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands

# ==================================================
# 1. سيرفر ويب وهمي (Flask) لتخطي مشكلة Port في Render
# ==================================================
app = Flask('')

@app.route('/')
def home():
    return "Bot is Alive and Running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# تشغيل خادم الويب في المسار الجانبي
Thread(target=run_web).start()

# ==================================================
# 2. إعدادات المتغيرات وقراءة التوكن
# ==================================================
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
AFK_VOICE_CHANNEL_ID = 1350135312013201450  # ضع هنا ID روم الـ AFK الخاص بك

# ==================================================
# 3. إنشاء منطق البوت
# ==================================================
def create_bot(channel_id):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = commands.Bot(command_prefix='!', intents=intents)
    afk_users = {}

    @bot.event
    async def on_ready():
        print(f'✅ البوت {bot.user} جاهز للعمل!')
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                if bot.voice_clients:
                    for vc in bot.voice_clients:
                        if vc.guild == channel.guild:
                            await vc.move_to(channel)
                            break
                else:
                    await channel.connect()
                print(f'✅ دخل البوت {bot.user} إلى روم AFK: {channel.name}')
            except Exception as e:
                print(f'⚠️ فشل دخول البوت إلى AFK: {e}')
        else:
            print(f'❌ لم يتم العثور على روم AFK بـ ID: {channel_id}')

    @bot.event
    async def on_voice_state_update(member, before, after):
        # منع التأثر إذا كان العضو ليس البوت أو لم يتغير الروم
        if member.id != bot.user.id or before.channel == after.channel:
            return

        # إعادة البوت تلقائياً لروم الـ AFK إذا تم نقله أو طرده
        if after.channel is None or after.channel.id != channel_id:
            afk_channel = bot.get_channel(channel_id)
            if afk_channel:
                try:
                    if member.guild.voice_client:
                        await member.guild.voice_client.move_to(afk_channel)
                    else:
                        await afk_channel.connect()
                    print(f'🛡️ تم إرجاع البوت {bot.user} إلى روم AFK تلقائيًا.')
                except Exception as e:
                    print(f'⚠️ تعذر إرجاع البوت إلى AFK: {e}')

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        # الرد على منشن عضو متواجد في وضع AFK
        for mention in message.mentions:
            if mention.id in afk_users:
                reason = afk_users[mention.id]["reason"]
                await message.reply(f"🔇 **{mention.display_name}** غير متواجد (AFK). السبب: {reason}")

        # إلغاء وضع AFK وإعادة العضو لرومه السابق عند إرسال رسالة
        if message.author.id in afk_users:
            member = message.author
            data = afk_users.pop(member.id)
            original_channel = data.get("original_channel")
            original_nick = data.get("original_nick")

            try:
                await member.edit(nick=original_nick)
            except discord.Forbidden:
                pass

            if member.voice and member.voice.channel and member.voice.channel.id == channel_id and original_channel:
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
            afk_channel = bot.get_channel(channel_id)
            if afk_channel:
                try:
                    await member.move_to(afk_channel)
                    await ctx.send(f"🔇 تم نقل **{member.display_name}** إلى قناة AFK.")
                except discord.Forbidden:
                    await ctx.send("❌ البوت لا يملك صلاحية (Move Members) لنقلك صوتيًا!")
                    return
                except Exception as e:
                    await ctx.send(f"⚠️ خطأ أثناء النقل الصوتي: {e}")
                    return

        # إضافة [AFK] للاسم
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

    return bot

# ==================================================
# 4. تشغيل البرنامج
# ==================================================
async def main():
    if not BOT_TOKEN:
        print("❌ لم يتم العثور على DISCORD_TOKEN في متغيرات البيئة!")
        return

    bot = create_bot(AFK_VOICE_CHANNEL_ID)
    await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 تم إيقاف البوت.")
    except Exception as e:
        print(f"⚠️ خطأ أثناء التشغيل: {e}")
