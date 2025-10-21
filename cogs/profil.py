import discord, json, requests, os
from discord.ext import commands

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

    def save_users(self, data):
        """Sauvegarde users.json sur le Gist."""
        try:
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                print("[❌] Aucun GITHUB_TOKEN défini.")
                return
            url = f"https://api.github.com/gists/{self.GIST_ID}"
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "PokemonManagerBot"
            }
            payload = {
                "files": {
                    "users.json": {"content": json.dumps(data, ensure_ascii=False, indent=4)}
                }
            }
            requests.patch(url, headers=headers, json=payload, timeout=10)
        except Exception as e:
            print(f"[❌] Erreur sauvegarde users.json : {e}")

    def load_pokemons(self):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    # --- /portrait ---
    @discord.app_commands.command(
        name="portrait",
        description="Ajoute ou modifie l’image de ton personnage actif."
    )
    @discord.app_commands.describe(
        fichier="Envoie une image (jpg/png/webp) pour ton personnage actif."
    )
    async def portrait(
        self,
        interaction: discord.Interaction,
        fichier: discord.Attachment
    ):
        users = self.load_users()
        user_id = str(interaction.user.id)

        # vérif basique
        if user_id not in users or not users[user_id].get("characters"):
            await interaction.response.send_message(
                "Tu n’as encore aucun personnage. Utilise `/perso <nom>` pour en créer un !",
                ephemeral=True
            )
            return

        active = users[user_id].get("active")
        if not active or active not in users[user_id]["characters"]:
            await interaction.response.send_message(
                "Tu n’as aucun personnage actif. Utilise `/perso <nom>` pour en activer un.",
                ephemeral=True
            )
            return

        # vérif du fichier
        if not fichier.content_type or not fichier.content_type.startswith("image/"):
            await interaction.response.send_message(
                "Le fichier envoyé n’est pas une image valide.",
                ephemeral=True
            )
            return

        image_url = fichier.url
        perso_data = users[user_id]["characters"][active]
        perso_data["portrait"] = image_url
        self.save_users(users)

        embed = discord.Embed(
            title=f"🖼️ Portrait mis à jour pour {active}",
            color=0x88CCEE,
            description="Image enregistrée avec succès !"
        )
        embed.set_image(url=image_url)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Profil(bot))
