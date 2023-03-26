import discord
import os
import logging

# Setup logging
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.DEBUG)
# Set the discord http logger level to info
logging.getLogger("discord.http").setLevel(logging.INFO)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Successfully started bot as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


DISCORD_TOKEN_ENVAR = "DISCORD_BOT_TOKEN"

if __name__ == "__main__":
    discord_token = os.getenv(DISCORD_TOKEN_ENVAR)
    client.run(discord_token, log_handler=None)