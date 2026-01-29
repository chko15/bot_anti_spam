import discord
import re
import os
import unicodedata
from datetime import datetime, timedelta
from discord.ext import commands
from dotenv import load_dotenv
from collections import defaultdict

# ================= LOAD ENV =================

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

LOG_CHANNEL_ID = 1466507799361229003# <<< GANTI INI

# ================= INTENTS =================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= CONFIG =================

SCAM_KEYWORDS = [
    "mrbeast",
    "giveaway",
    "free nitro",
    "claim",
    "airdrop",
    "discord nitro"
]

WHITELIST_DOMAINS = [
    "youtube.com",
    "discord.com",
    "discord.gg",
    "twitter.com",
    "x.com"
]

URL_REGEX = re.compile(r"https?://\S+")

SPAM_LIMIT = 3       # pesan
SPAM_SECONDS = 10    # detik

user_message_log = defaultdict(list)

# ================= HELPERS =================

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = text.replace("rn", "m")
    return text

def is_whitelisted(url: str) -> bool:
    return any(domain in url for domain in WHITELIST_DOMAINS)

async def log_action_embed(guild, title, color, fields):
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if not channel:
        return

    embed = discord.Embed(
        title=title,
        color=color,
        timestamp=datetime.utcnow()
    )

    for name, value in fields:
        embed.add_field(name=name, value=value, inline=False)

    await channel.send(embed=embed)

# ================= EVENTS =================

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    now = datetime.utcnow()

    # ================= RATE LIMIT =================
    logs = user_message_log[message.author.id]
    logs.append(now)
    user_message_log[message.author.id] = [
        t for t in logs if now - t < timedelta(seconds=SPAM_SECONDS)
    ]

    if len(user_message_log[message.author.id]) >= SPAM_LIMIT:
        await message.delete()
        await message.author.timeout(
            timedelta(minutes=10),
            reason="Spam detected"
        )

        await log_action_embed(
            message.guild,
            "⏱️ SPAM DETECTED",
            discord.Color.orange(),
            [
                ("User", str(message.author)),
                ("Channel", message.channel.mention),
                ("Action", "Timeout 10 minutes")
            ]
        )
        return

    # ================= LINK SCAN =================
    content_normalized = normalize(message.content)
    urls = URL_REGEX.findall(message.content)

    if urls:
        for url in urls:
            if is_whitelisted(url):
                continue

            if any(keyword in content_normalized for keyword in SCAM_KEYWORDS):
                await message.delete()

                # akun baru → ban
                if message.author.created_at > now - timedelta(days=7):
                    await message.author.ban(reason="Scam link detected")
                    action = "Auto-BAN"
                else:
                    await message.author.timeout(
                        timedelta(minutes=30),
                        reason="Scam link detected"
                    )
                    action = "Timeout 30 minutes"

                await log_action_embed(
                    message.guild,
                    "🚨 SCAM LINK DETECTED",
                    discord.Color.red(),
                    [
                        ("User", str(message.author)),
                        ("Channel", message.channel.mention),
                        ("Action", action),
                        ("Link", url),
                        ("Message", message.content[:1024])
                    ]
                )
                return

    await bot.process_commands(message)

# ================= RUN =================

bot.run(TOKEN)
