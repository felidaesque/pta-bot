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
        synced = await bot.tree.sync()
        print(f"{len(synced)} commande(s) slash synchronisée(s).")
    except Exception as e:
        print(f"Erreur de sync : {e}")

@bot.tree.command(name="ping", description="Teste si le bot répond")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong ! 🏓")

bot.run(os.getenv("DISCORD_TOKEN"))
