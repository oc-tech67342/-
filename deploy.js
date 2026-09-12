const { REST, Routes, SlashCommandBuilder } = require('discord.js');
require('dotenv').config();

const commands = [
    new SlashCommandBuilder()
        .setName('lock')
        .setDescription('قفل الروم ومنع الأعضاء من إرسال الرسائل'),

    new SlashCommandBuilder()
        .setName('unlock')
        .setDescription('فتح الروم والسماح للأعضاء بإرسال الرسائل')
].map(command => command.toJSON());

const rest = new REST({ version: '10' }).setToken(process.env.TOKEN);

(async () => {
    try {
        console.log('جاري تسجيل الأوامر...');

        await rest.put(
            Routes.applicationGuildCommands(
                process.env.CLIENT_ID,
                process.env.GUILD_ID
            ),
            { body: commands }
        );

        console.log('تم تسجيل الأوامر بنجاح!');
    } catch (error) {
        console.error(error);
    }
})();