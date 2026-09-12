import asyncio
import os
import discord
from discord.ext import commands

# ==================================================
# الإعدادات
# ==================================================

# 🔑 قراءة التوكن من متغيرات البيئة في Render
# إذا لم يجد المتغير DISCORD_TOKEN سيعود لقيمة فارغة
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

# 🔊 ID روم AFK
AFK_VOICE_CHANNEL_ID = 1350135312013201450


# ==================================================
# إنشاء البوت
# ==================================================

def create_bot(channel_id):

    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = commands.Bot(
        command_prefix='!',
        intents=intents
    )

    afk_users = {}

    # ==================================================
    # عند تشغيل البوت
    # ==================================================

    @bot.event
    async def on_ready():
        print(f'✅ البوت {bot.user} جاهز للعمل!')

        channel = bot.get_channel(channel_id)
        if channel:
            try:
                # التحقق مما إذا كان البوت متصلًا بالفعل بروم صوتي
                if bot.voice_clients:
                    for vc in bot.voice_clients:
                        if vc.guild == channel.guild:
                            await vc.move_to(channel)
                            break
                else:
                    await channel.connect()

                print(f'✅ دخل البوت {bot.user} إلى روم AFK: {channel.name}')
            except Exception as e:
                print(f'⚠️ فشل دخول البوت {bot.user} إلى AFK: {e}')
        else:
            print(f'❌ لم أجد روم AFK بالـ ID: {channel_id}')

    # ==================================================
    # حماية البوت من Disconnect والنقل
    # ==================================================

    @bot.event
    async def on_voice_state_update(member, before, after):
        if member.id != bot.user.id:
            return

        if before.channel == after.channel:
            return

        # إذا خرج البوت أو تم نقله لغرفة أخرى
        if after.channel is None or after.channel.id != channel_id:
            afk_channel = bot.get_channel(channel_id)
            if not afk_channel:
                return

            try:
                if member.guild.voice_client:
                    await member.guild.voice_client.move_to(afk_channel)
                else:
                    await afk_channel.connect()

                print(f'🛡️ تم إرجاع البوت {bot.user} إلى روم AFK تلقائيًا.')
            except Exception as e:
                print(f'⚠️ تعذر إرجاع البوت إلى AFK: {e}')

    # ==================================================
    # نظام AFK (عند إرسال رسالة)
    # ==================================================

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        # الرد على منشن عضو في وضع AFK
        for mention in message.mentions:
            if mention.id in afk_users:
                reason = afk_users[mention.id]["reason"]
                await message.reply(
                    f"🔇 **{mention.display_name}** غير متواجد (AFK). السبب: {reason}"
                )

        # إلغاء وضع AFK إذا كان المرسل هو الشخص المتواجد بالـ AFK
        if message.author.id in afk_users:
            member = message.author
            data = afk_users.pop(member.id)
            original_channel = data.get("original_channel")
            original_nick = data.get("original_nick")

            # إرجاع الاسم المستعار الأصلي
            try:
                await member.edit(nick=original_nick)
            except discord.Forbidden:
                pass

            # إرجاع العضو إلى رومه الأصلي إذا كان موجودًا في روم AFK
            if member.voice and member.voice.channel:
                if member.voice.channel.id == channel_id and original_channel:
                    try:
                        await member.move_to(original_channel)
                        await message.channel.send(
                            f"🔊 تم إرجاع **{member.display_name}** إلى قناته الأصلية."
                        )
                    except Exception as e:
                        await message.channel.send(f"⚠️ خطأ في إرجاع الصوت: {e}")

            await message.channel.send(
                f"👋 مرحبًا بعودتك **{member.display_name}**! تم إلغاء وضع AFK."
            )

        await bot.process_commands(message)

    # ==================================================
    # أمر !afk
    # ==================================================

    @bot.command()
    async def afk(ctx, *, reason: str = "لم يحدد سببًا."):
        member = ctx.author

        original_nick = member.nick
        original_channel = None

        if member.voice and member.voice.channel:
            original_channel = member.voice.channel
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

        # تعديل الاسم المستعار لإضافة [AFK]
        try:
            new_nick = f"[AFK] {member.display_name}"
            if len(new_nick) > 32:
                new_nick = new_nick[:32]
            await member.edit(nick=new_nick)
        except discord.Forbidden:
            pass

        # حفظ بيانات العضو
        afk_users[member.id] = {
            "reason": reason,
            "original_channel": original_channel,
            "original_nick": original_nick
        }

        await ctx.send(f"✅ **{member.display_name}** دخل وضع AFK. السبب: {reason}")

    return bot


# ==================================================
# تشغيل البرنامج
# ==================================================

async def main():
    if not BOT_TOKEN:
        print("❌ لم يتم العثور على DISCORD_TOKEN في متغيرات البيئة (Environment Variables)!")
        return

    bot = create_bot(AFK_VOICE_CHANNEL_ID)
    await bot.start(BOT_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 تم إيقاف البوت بواسطة المستخدم.")
    except Exception as e:
        print(f"⚠️ خطأ أثناء التشغيل: {e}")
