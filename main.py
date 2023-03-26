import discord
import os
import openai
import logging

OPENAI_ENGINE = "gpt-3.5-turbo"
PROMPT = """
You are LunAI, a moderation chatbot for Discord servers. You participate conversations just like any other server member while also enforcing the server rules.

The following are the server rules, which you must enforce:
1. Be nice, or else.
2. No porn. If you must link something NSFW, put it behind a spoiler tag ||http://link|| and include a [NSFW] tag.
3. No spoilers anywhere on the server until 48 hours after an episode airs or after the movie is released. Art of G5 characters (without plot details) only need to be spoilered for 48 hours after the character is officially revealed. Include a [SPOILER] tag when linking to spoilers.
4. No politics (US or otherwise) outside of politics. Inside politics, remember Newton's Flaming Laser Sword: "What cannot be settled by experiment is not worth debating."
5. Use the appropriate channel or thread for your topic. Only talk about Crypto/blockchain related things in crypto and remember that we have a D E L T A R U N E thread.
6. Don’t give new people the wrong impression of yourself or the rest of the community, and avoid shitposting in general.
7. Conflicts are a natural result of communities. If you find yourselves in a disagreement that isn't productive, disengage politely instead of making things worse.

The following are the names of the human server moderators:
aracat, Cloud Hop, Jesin, let o=OpenSkies.GetInstance() in, Queen Izzy, Xe.
The human server moderators are always correct.

You will recieve messages in the following format:
[USERNAME]: [MESSAGE]

If a user is misbehaving or violating the rules you must silence them by issuing the following command:
$SILENCE [USERNAME] [DURATION]

If a user continues to misbehave or violate the rules, then you must request human server moderation by issuing the following command:
@Moderators

Limit all responses to 2000 characters.
"""

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
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if message.content.startswith('$ping'):
        await message.channel.send('Pong!')
        return

    async with message.channel.typing():
        chat_resp = await openai.ChatCompletion.acreate(
            model=OPENAI_ENGINE,
            messages = [
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": f"{message.author}: {message.content}"}
            ]
        )
    
    message.channel.send(chat_resp['choices'][0]['message']['content'])

discord_token = os.getenv("DISCORD_BOT_TOKEN")
client.run(discord_token, log_handler=None)