require('dotenv').config();

const {
    Client,
    GatewayIntentBits,
    PermissionsBitField,
    ChannelType,
    REST,
    Routes
} = require('discord.js');

const client = new Client({
    intents: [GatewayIntentBits.Guilds]
});

const commands = [
    {
        name: 'lock',
        description: 'يقفل الكتابة في جميع الرومات'
    },
    {
        name: 'unlock',
        description: 'يفتح الكتابة في جميع الرومات'
    }
];

client.once('clientReady', async () => {
    console.log(`BOT READY: ${client.user.tag}`);
    console.log(`BOT ID: ${client.user.id}`);
    console.log(`CLIENT ID: ${process.env.CLIENT_ID}`);

    try {
        const rest = new REST({ version: '10' })
            .setToken(process.env.TOKEN);

        await rest.put(
            Routes.applicationGuildCommands(
                process.env.CLIENT_ID,
                process.env.GUILD_ID
            ),
            { body: commands }
        );

        console.log('SLASH COMMANDS REGISTERED');
    } catch (error) {
        console.error('COMMAND REGISTER ERROR:', error);
    }
});

client.on('interactionCreate', async interaction => {
    console.log(`INTERACTION: ${interaction.commandName}`);

    if (!interaction.isChatInputCommand()) return;

    if (!interaction.memberPermissions?.has(
        PermissionsBitField.Flags.ManageChannels
    )) {
        return interaction.reply({
            content: '❌ ما عندك صلاحية استخدام هذا الأمر.',
            ephemeral: true
        });
    }

    if (interaction.commandName === 'lock') {
        await interaction.deferReply();

        let success = 0;

        for (const channel of interaction.guild.channels.cache.values()) {
            try {
                if (
                    channel.type === ChannelType.GuildText ||
                    channel.type === ChannelType.GuildAnnouncement
                ) {
                    await channel.permissionOverwrites.edit(
                        interaction.guild.roles.everyone,
                        { SendMessages: false }
                    );

                    success++;
                }
            } catch (error) {
                console.log(`لم أستطع قفل: ${channel.name}`);
            }
        }

        await interaction.editReply(
            `🔒 تم قفل ${success} روم عن الأعضاء.`
        );
    }

    if (interaction.commandName === 'unlock') {
        await interaction.deferReply();

        let success = 0;

        for (const channel of interaction.guild.channels.cache.values()) {
            try {
                if (
                    channel.type === ChannelType.GuildText ||
                    channel.type === ChannelType.GuildAnnouncement
                ) {
                    await channel.permissionOverwrites.edit(
                        interaction.guild.roles.everyone,
                        { SendMessages: null }
                    );

                    success++;
                }
            } catch (error) {
                console.log(`لم أستطع فتح: ${channel.name}`);
            }
        }

        await interaction.editReply(
            `🔓 تم فتح ${success} روم للأعضاء.`
        );
    }
});

client.on('error', error => {
    console.error('DISCORD ERROR:', error);
});

client.login(process.env.TOKEN);