import discord
import re
import os
import unicodedata
from datetime import datetime, timedelta
from discord.ext import commands
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

LOG_CHANNEL_ID = 1466507799361229003  # GANTI DENGAN ID CHANNEL LOG

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= CONFIG =================

SCAM_KEYWORDS = [
    "mrbeast", "giveaway", "free nitro", "claim", "airdrop"
]

WHITELIST_DOMAINS = [
    "youtube.com",
    "discord.com",
    "discord.gg",
    "twitter.com",
    "x.com"
]

URL_REGEX = re.compile(r"https?://\S+")

SPAM_LIMIT = 3      # jumlah pesan
SPAM_SECONDS = 10   # dalam detik

user_message_log = defaultdict(list)

# ================= HELPERS =================

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = text.replace("rn", "m")  # trick scam
    return text

def is_whitelisted(url: str) -> bool:
    return any(domain in url for domain in WHITELIST_DOMAINS)

async def log_action(guild, content):
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(content)

# ================= EVENTS =================

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    now = datetime.utcnow()
    logs = user_message_log[message.author.id]
    logs.append(now)
    user_message_log[message.author.id] = [
        t for t in logs if now - t < timedelta(seconds=SPAM_SECONDS)
    ]

    # 🚫 RATE LIMIT
    if len(user_message_log[message.author.id]) >= SPAM_LIMIT:
        await message.delete()
        await message.author.timeout(
            timedelta(minutes=10),
            reason="Spam detected"
        )
        await log_action(
            message.guild,
            f"⏱️ **Spam Timeout** {message.author} in {message.channel}"
        )
        return

    content = normalize(message.content)

    # 🔗 LINK CHECK
    urls = URL_REGEX.findall(message.content)
    if urls:
        for url in urls:
            if is_whitelisted(url):
                continue

            if any(keyword in content for keyword in SCAM_KEYWORDS):
                await message.delete()

                # 👶 AKUN BARU
                if message.author.created_at > now - timedelta(days=7):
                    await message.author.ban(reason="Scam link (auto-ban)")
                    action = "🔨 **Auto-BAN**"
                else:
                    await message.author.timeout(
                        timedelta(minutes=30),
                        reason="Scam link"
                    )
                    action = "⏱️ **Timeout**"

                await log_action(
                    message.guild,
                    f"""{action}
👤 User: {message.author}
📍 Channel: {message.channel}
🔗 Link: `{url}`
📝 Content: `{message.content}`"""
                )
                return

    await bot.process_commands(message)

bot.run(TOKEN)
