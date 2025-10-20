import discord, random, json
from discord.ext import commands

SHINY_CHANCE = 100

TYPE_COLORS = {
    "Normal": 0xA8A77A,
    "Feu": 0xEE8130,
    "Eau": 0x6390F0,
    "Électrik": 0xF7D02C,
    "Plante": 0x7AC74C,
    "Glace": 0x96D9D6,
    "Combat": 0xC22E28,
    "Poison": 0xA33EA1,
    "Sol": 0xE2BF65,
    "Vol": 0xA98FF3,
    "Psy": 0xF95587,
    "Insecte": 0xA6B91A,
    "Roche": 0xB6A136,
    "Spectre": 0x735797,
    "Dragon": 0x6F35FC,
    "Ténèbres": 0x705746,
    "Acier": 0xB7B7CE,
    "Fée": 0xD685AD
}

class Starters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_shiny(self):
        return random.randint(1, SHINY_CHANCE) == 1

    @discord.app_commands.command(name="starter", description="Reçois trois Pokémon de base au hasard")
    async def starter(self, interaction: discord.Interaction):
        # charge les données
        with open("data/first_stage_pokemons.json", "r", encoding="utf-8") as f:
            pokemons = json.load(f)

        # tire 3 Pokémon
        choices = random.sample(pokemons, 3)
        embeds = []

        for poke in choices:
            shiny = self.check_shiny()
            sprite = poke["sprite_shiny"] if shiny else poke["sprite"]
            name = f"{poke['nom']} {'★' if shiny else ''}"
            types = ", ".join(poke["type"])

            # couleur du premier type
            color = TYPE_COLORS.get(poke["type"][0], 0x88CCEE)

            # embed pour chaque Pokémon
            embed = discord.Embed(title=name, description=types, color=color)
            embed.set_image(url=sprite)
            embeds.append(embed)

        await interaction.response.send_message(
            content="Voici tes trois starters ! 🌱🔥💧",
            embeds=embeds
        )

async def setup(bot):
    await bot.add_cog(Starters(bot))
