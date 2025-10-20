import discord, random, json
from discord.ext import commands

SHINY_CHANCE = 100  # 1 sur 100

class Starters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_shiny(self):
        return random.randint(1, SHINY_CHANCE) == 1

    @discord.app_commands.command(name="starter", description="Reçois trois Pokémon de base au hasard")
    async def starter(self, interaction: discord.Interaction):
        with open("data/first_stage_pokemons.json", "r", encoding="utf-8") as f:
            pokemons = json.load(f)

        choices = random.sample(pokemons, 3)

        embed = discord.Embed(title="Voici tes starters :", color=0x88CCEE)
        for poke in choices:
            shiny = self.check_shiny()
            sprite = poke["sprite_shiny"] if shiny else poke["sprite"]
            name = f"{poke['nom']} {'★' if shiny else ''}"
            types = ", ".join(poke["type"])
            embed.add_field(name=name, value=types, inline=False)
            embed.set_thumbnail(url=sprite)

        embed.set_footer(text="Utilise /choose pour en sélectionner un (bientôt disponible).")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Starters(bot))
