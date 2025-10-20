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
        """Renvoie True 1 fois sur SHINY_CHANCE"""
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

    def random_gender(self, pokemon):
        """Renvoie le genre du Pokémon selon son ratio"""
        if pokemon["gender_rate"] is None:
            return "Asexué"
        return "Femelle" if random.random() < pokemon["gender_rate"] else "Mâle"

    # --- Auto-complétion des types ---
    @discord.app_commands.autocomplete(type=lambda _, __, current: [
        discord.app_commands.Choice(name=t, value=t)
        for t in TYPE_COLORS.keys()
        if current.lower() in t.lower()
    ])
    @discord.app_commands.command(
        name="starter",
        description="Reçois trois Pokémon de base au hasard (tu peux filtrer par type, ex: /starter Fée)"
    )
    @discord.app_commands.describe(type="Filtre un type précis de Pokémon (ex: Feu, Eau, Fée...)")
    async def starter(self, interaction: discord.Interaction, type: str = None):
        # Charge la base de données
        with open("data/pokemons.json", "r", encoding="utf-8") as f:
            pokemons = json.load(f)

        chosen_type = type.capitalize() if type else None

        # Filtrage : formes de base, non légendaires
        starters = [p for p in pokemons if p["evolution_stage"] == 0 and not p["is_legendary"]]

        # Si un type est précisé
        if chosen_type:
            starters = [p for p in starters if chosen_type in p["type"]]
            if not starters:
                await interaction.response.send_message(
                    f"Aucun Pokémon de type **{chosen_type}** disponible comme starter.",
                    ephemeral=True
                )
                return

        # Sélection aléatoire
        choices = random.sample(starters, min(3, len(starters)))
        sprites = []
        description = ""

        for poke in choices:
            shiny = self.check_shiny()
            gender = self.random_gender(poke)
            sprite = poke["sprite_shiny"] if shiny else poke["sprite"]
            sprites.append(sprite)
            shiny_star = "★" if shiny else ""
            types = " ".join(f"{TYPE_EMOJIS.get(t, '')} {t}" for t in poke["type"])
            description += f"**{poke['nom']} {shiny_star}** ({gender}) — {types}\n"

        file = self.merge_sprites(sprites)

        embed_color = TYPE_COLORS.get(chosen_type, 0x88CCEE) if chosen_type else 0x88CCEE
        embed = discord.Embed(
            title="🌟 Choisis ton starter !" if not chosen_type else f"🌟 Starters de type {chosen_type}",
            description=description,
            color=embed_color
        )
        embed.set_image(url="attachment://starters.png")
        embed.set_footer(text="Utilise /choose pour sélectionner ton Pokémon !")

        await interaction.response.send_message(embed=embed, file=file)


async def setup(bot):
    await bot.add_cog(Starters(bot))
