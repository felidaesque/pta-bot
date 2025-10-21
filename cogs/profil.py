import discord, json, requests
from discord.ext import commands
import os

# --- Constantes globales (à partager avec starters.py) ---
DATA_PATH = "data/pokemons.json"

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


class Profil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # même Gist ID que dans starters.py
        self.GIST_ID = "b4485737f8d88706b414392796f3843f"

    def load_users(self):
        """Lecture users.json depuis l’API GitHub."""
        try:
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                print("[❌] Aucun GITHUB_TOKEN défini.")
                return {}
            url = f"https://api.github.com/gists/{self.GIST_ID}"
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "PokemonManagerBot"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            gist_data = response.json()
            content = gist_data["files"]["users.json"]["content"]
            return json.loads(content)
        except Exception as e:
            print(f"[❌] Erreur lecture users.json : {e}")
            return {}

    def load_pokemons(self):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    # --- /profil ---
    @discord.app_commands.command(
        name="profil",
        description="Affiche le profil d’un personnage (le tien ou un autre des tiens)."
    )
    @discord.app_commands.describe(nom="Nom du personnage (laisse vide pour ton personnage actif)")
    async def profil(self, interaction: discord.Interaction, nom: str = None):
        users = self.load_users()
        user_id = str(interaction.user.id)

        if user_id not in users or not users[user_id].get("characters"):
            await interaction.response.send_message(
                "Tu n’as encore aucun personnage. Utilise `/perso <nom>` pour en créer un !",
                ephemeral=True
            )
            return

        active = users[user_id].get("active")
        target_name = nom or active

        if not target_name or target_name not in users[user_id]["characters"]:
            persos = ", ".join(users[user_id]["characters"].keys())
            await interaction.response.send_message(
                f"Impossible de trouver ce personnage. Personnages disponibles : {persos}",
                ephemeral=True
            )
            return

        perso_data = users[user_id]["characters"][target_name]
        if "starter" not in perso_data:
            await interaction.response.send_message(
                f"Ton personnage **{target_name}** n’a pas encore choisi de starter. Utilise `/starter` puis `/choose`.",
                ephemeral=True
            )
            return

        pokemons = self.load_pokemons()
        pokemon = next((p for p in pokemons if p["nom"].lower() == perso_data["starter"].lower()), None)
        if not pokemon:
            await interaction.response.send_message(
                "Erreur : ton Pokémon n’existe pas dans la base de données.",
                ephemeral=True
            )
            return

        shiny = perso_data.get("shiny", False)
        sprite = pokemon["sprite_shiny"] if shiny else pokemon["sprite"]
        types = " ".join(f"{TYPE_EMOJIS.get(t, '')} {t}" for t in pokemon["type"])
        shiny_star = "★" if shiny else ""

        embed = discord.Embed(
            title=f"Profil de {target_name}",
            color=TYPE_COLORS.get(pokemon["type"][0], 0x88CCEE)
        )
        embed.set_thumbnail(url=sprite)
        embed.add_field(name="Pokémon", value=f"**{pokemon['nom']} {shiny_star}**", inline=False)
        embed.add_field(name="Genre", value=perso_data.get("gender", 'Inconnu'), inline=True)
        embed.add_field(name="Niveau", value=str(perso_data.get("niveau", 1)), inline=True)
        embed.add_field(name="Expérience", value=str(perso_data.get("xp", 0)), inline=True)
        embed.add_field(name="Type", value=types, inline=False)
        embed.set_footer(text="(Personnage actif)" if target_name == active else "(Personnage inactif)")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Profil(bot))
