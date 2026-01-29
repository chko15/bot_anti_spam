import discord
import re
import os
from datetime import datetime, timedelta
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 🚫 Kata & domain scam
SCAM_KEYWORDS = [
    "mrbeast", "giveaway", "free nitro", "airdrop", "claim now"
]

SCAM_DOMAINS = [
    "mrbeast", "discord-gift", "nitro", "giveaway"
]

URL_REGEX = re.compile(r"https?://\S+")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()

    # 🔗 Deteksi link
    if URL_REGEX.search(content):

        # 🔍 Keyword / domain scam
        if any(word in content for word in SCAM_KEYWORDS + SCAM_DOMAINS):

            # ⏱️ Akun baru (<7 hari)
            if message.author.created_at > datetime.utcnow() - timedelta(days=7):
                await message.delete()

                try:
                    await message.author.timeout(
                        timedelta(minutes=30),
                        reason="Scam link detected"
                    )
                except:
                    pass

                await message.channel.send(
                    f"🚨 {message.author.mention} scam link terdeteksi dan diblokir."
                )
                return

    await bot.process_commands(message)

bot.run(TOKEN)
