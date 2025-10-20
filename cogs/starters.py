import discord, random, json, requests
from io import BytesIO
from PIL import Image
from discord.ext import commands

SHINY_CHANCE = 100

TYPE_COLORS = {
    "Normal": 0xA8A77A, "Feu": 0xEE8130, "Eau": 0x6390F0,
    "Électrik": 0xF7D02C, "Plante": 0x7AC74C, "Glace": 0x96D9D6,
    "Combat": 0xC22E28, "Poison": 0xA33EA1, "Sol": 0xE2BF65,
    "Vol": 0xA98FF3, "Psy": 0xF95587, "Insecte": 0xA6B91A,
    "Roche": 0xB6A136, "Spectre": 0x735797, "Dragon": 0x6F35FC,
    "Ténèbres": 0x705746, "Acier": 0xB7B7CE, "Fée": 0xD685AD
}

TYPE_EMOJIS = {
    "Normal": "⚪", "Feu": "🔥", "Eau": "💧", "Électrik": "⚡",
    "Plante": "🌿", "Glace": "❄️", "Combat": "🥊", "Poison": "☠️",
    "Sol": "🌍", "Vol": "🌬️", "Psy": "🔮", "Insecte": "🐛",
    "Roche": "🪨", "Spectre": "👻", "Dragon": "🐉",
    "Ténèbres": "🌑", "Acier": "⚙️", "Fée": "✨"
}

class Starters(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_shiny(self):
        return random.randint(1, SHINY_CHANCE) == 1

    def merge_sprites(self, urls):
        """Télécharge et fusionne les sprites horizontalement"""
        images = [Image.open(BytesIO(requests.get(u).content)) for u in urls]
        w, h = images[0].size
        merged = Image.new("RGBA", (w * len(images), h))
        for i, img in enumerate(images):
            merged.paste(img, (i * w, 0))
        buffer = BytesIO()
        merged.save(buffer, format="PNG")
        buffer.seek(0)
        return discord.File(buffer, filename="starters.png")

    @discord.app_commands.command(name="starter", description="Reçois trois Pokémon de base au hasard")
    async def starter(self, interaction: discord.Interaction):
        with open("data/first_stage_pokemons.json", "r", encoding="utf-8") as f:
            pokemons = json.load(f)

        choices = random.sample(pokemons, 3)
        sprites = []
        description = ""

        for poke in choices:
            shiny = self.check_shiny()
            sprite = poke["sprite_shiny"] if shiny else poke["sprite"]
            sprites.append(sprite)
            emoji = "★" if shiny else ""
            types = " ".join(f"{TYPE_EMOJIS.get(t, '')} {t}" for t in poke["type"])
            description += f"**{poke['nom']} {emoji}** — {types}\n"

        file = self.merge_sprites(sprites)

        embed = discord.Embed(
            title="🌟 Choisis ton starter !",
            description=description,
            color=0x88CCEE
        )
        embed.set_image(url="attachment://starters.png")
        embed.set_footer(text="Utilise /choose pour sélectionner ton Pokémon !")

        await interaction.response.send_message(embed=embed, file=file)

async def setup(bot):
    await bot.add_cog(Starters(bot))
