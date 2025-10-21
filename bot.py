import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Connecté en tant que {bot.user}")
    try:
        await bot.tree.sync()
        print("Commandes slash synchronisées.")
    except Exception as e:
        print(e)

async def load_extensions():
    await bot.load_extension("cogs.starters")
    await bot.load_extension("cogs.profil")

if __name__ == "__main__":
    import asyncio
    asyncio.run(load_extensions())
    bot.run(os.getenv("DISCORD_TOKEN"))

