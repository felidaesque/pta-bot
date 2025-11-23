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

    # --------- Fonctions internes ---------
    def load_users(self):
        """Lecture users.json depuis le Gist GitHub."""
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

    # --------- Commande /profil ---------
    @discord.app_commands.command(
        name="profil",
        description="Affiche le profil complet de ton personnage actif."
    )
    async def profil(self, interaction: discord.Interaction):
        users = self.load_users()
        user_id = str(interaction.user.id)

        # Vérifs de base
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

        perso_data = users[user_id]["characters"][active]

        if "starter" not in perso_data:
            await interaction.response.send_message(
                f"Ton personnage **{active}** n’a pas encore choisi de Pokémon starter. Utilise `/starter` puis `/choose`.",
                ephemeral=True
            )
            return

        # Données de base du starter
        pokemons = self.load_pokemons()
        pokemon = next((p for p in pokemons if p["nom"].lower() == perso_data["starter"].lower()), None)
        if not pokemon:
            await interaction.response.send_message(
                "Erreur : ce Pokémon n’existe pas dans la base de données.",
                ephemeral=True
            )
            return

        shiny = perso_data.get("shiny", False)
        gender = perso_data.get("gender", "Inconnu")
        sprite = pokemon["sprite_shiny"] if shiny else pokemon["sprite"]
        types = " ".join(f"{TYPE_EMOJIS.get(t, '')} {t}" for t in pokemon["type"])
        shiny_star = "★" if shiny else ""

        # Données de dresseur
        niveau = perso_data.get("niveau", 1)
        xp = perso_data.get("xp", 0)
        pvs = perso_data.get("pvs")

        # Données avancées
        classes = perso_data.get("classes", [])
        distinctions = perso_data.get("distinctions", [])
        team = perso_data.get("pokemons", [])

        portrait = perso_data.get("portrait")

        embed = discord.Embed(
            title=f"Profil de {active}",
            color=TYPE_COLORS.get(pokemon["type"][0], 0x88CCEE)
        )

        # Portrait = thumbnail, Pokémon = image
        if portrait:
            embed.set_thumbnail(url=portrait)
        else:
            embed.set_thumbnail(url=sprite)

        embed.set_image(url=sprite)

        # Bloc starter
        embed.add_field(
            name="Pokémon starter",
            value=f"{pokemon['nom']} {shiny_star}\nSexe : {gender}",
            inline=True
        )
        embed.add_field(
            name="Type",
            value=types or "Inconnu",
            inline=True
        )

        # Bloc dresseur
        dresseur_txt = f"Niveau : {niveau}\nExpérience : {xp}"
        if pvs is not None:
            dresseur_txt += f"\nPV max : {pvs}"
        embed.add_field(
            name="Dresseur",
            value=dresseur_txt,
            inline=False
        )

        # Bloc classes
        if classes:
            classes_txt = "\n".join(
                f"• {c.get('nom', 'Inconnue')} (niv {c.get('niveau', 1)})"
                for c in classes
            )
        else:
            classes_txt = "Aucune classe pour le moment."
        embed.add_field(
            name="Classes",
            value=classes_txt,
            inline=False
        )

        # Bloc distinctions
        if distinctions:
            max_show = 5
            lines = [f"• {d}" for d in distinctions[:max_show]]
            if len(distinctions) > max_show:
                rest = len(distinctions) - max_show
                lines.append(f"... et {rest} autre(s).")
            distinctions_txt = "\n".join(lines)
        else:
            distinctions_txt = "Aucune distinction pour le moment."
        distinctions_txt += f"\n\nTotal : {len(distinctions)}"
        embed.add_field(
            name="Distinctions",
            value=distinctions_txt,
            inline=False
        )

        # Bloc équipe
        if team:
            team_lines = []
            for p in team:
                nom_poke = p.get("nom", "???")
                shiny_mark = "★" if p.get("shiny") else ""
                types_p = p.get("type", [])
                types_p_txt = ", ".join(types_p) if types_p else "Type inconnu"
                team_lines.append(f"• {nom_poke} {shiny_mark} ({types_p_txt})")
            team_txt = "\n".join(team_lines)
        else:
            team_txt = "Aucun autre Pokémon pour le moment."
        embed.add_field(
            name="Équipe",
            value=team_txt,
            inline=False
        )

        embed.set_footer(text="(Personnage actif)")
        await interaction.response.send_message(embed=embed)



async def setup(bot):
    await bot.add_cog(Profil(bot))
