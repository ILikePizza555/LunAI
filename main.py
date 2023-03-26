import discord
import os
import openai
import logging

# Setup logging
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.DEBUG)
# Set the discord http logger level to info
logging.getLogger("discord.http").setLevel(logging.INFO)

# Create a stream handler, set it's format and add it the root logger
stderr_handler = logging.StreamHandler()
stderr_handler.setFormatter(logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}",
    datefmt = "%Y-%m-%d %H:%M:%S",
    style = "{"
))
logging.getLogger().addHandler(stderr_handler)

# Create Discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Create OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

@client.event
async def on_ready():
    permissions = discord.Permissions()
    permissions.read_messages = True
    permissions.moderate_members = True
    permissions.send_messages = True
    permissions.send_messages_in_threads = True

    invite_url = discord.utils.oauth_url(1089633150516338868, permissions = permissions)
    print(f"Successfully started bot as {client.user}. Invite url {invite_url}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$ping'):
        await message.channel.send('Pong!')
        return

discord_token = os.getenv("DISCORD_BOT_TOKEN")
client.run(discord_token, log_handler=None)