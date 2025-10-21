import discord, random, json, requests, os
from io import BytesIO
from PIL import Image
from discord.ext import commands

# --- Constantes globales ---
DATA_PATH = "data/pokemons.json"
USERS_PATH = "data/users.json"
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

    # --- FONCTIONS UTILITAIRES ---
    def check_shiny(self):
        return random.randint(1, SHINY_CHANCE) == 1

    def merge_sprites(self, urls):
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
        if pokemon["gender_rate"] is None:
            return "Asexué"
        return "Femelle" if random.random() < pokemon["gender_rate"] else "Mâle"

    def load_pokemons(self):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_users(self):
        if not os.path.exists(USERS_PATH):
            os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
            with open(USERS_PATH, "w", encoding="utf-8") as f:
                json.dump({}, f)
        with open(USERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_users(self, data):
        with open(USERS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # --- /perso ---
    @discord.app_commands.command(
        name="perso",
        description="Crée ou active un personnage (ex: /perso Sarah)"
    )
    @discord.app_commands.describe(nom="Nom du personnage à créer ou activer")
    async def perso(self, interaction: discord.Interaction, nom: str):
        users = self.load_users()
        user_id = str(interaction.user.id)

        if user_id not in users:
            users[user_id] = {"active": nom, "characters": {nom: {}}}
            message = f"👤 Nouveau personnage **{nom}** créé et activé."
        else:
            if "characters" not in users[user_id]:
                users[user_id]["characters"] = {}
            if nom not in users[user_id]["characters"]:
                users[user_id]["characters"][nom] = {}
                message = f"👤 Nouveau personnage **{nom}** créé."
            users[user_id]["active"] = nom
            message = f"✅ Personnage **{nom}** activé."

        self.save_users(users)
        await interaction.response.send_message(message)

    # --- /starter ---
    @discord.app_commands.command(
        name="starter",
        description="Reçois trois Pokémon de base au hasard (tu peux filtrer par type, ex: /starter Fée)"
    )
    @discord.app_commands.describe(type="Filtre un type précis de Pokémon (ex: Feu, Eau, Fée...)")
    async def starter(self, interaction: discord.Interaction, type: str = None):
        users = self.load_users()
        user_id = str(interaction.user.id)

        # Vérifie le perso actif
        if user_id not in users or not users[user_id].get("active"):
            await interaction.response.send_message(
                "Tu n’as encore aucun personnage actif. Utilise `/perso <nom>` pour en créer un !",
                ephemeral=True
            )
            return

        active = users[user_id]["active"]
        if active not in users[user_id]["characters"]:
            users[user_id]["characters"][active] = {}

        pokemons = self.load_pokemons()
        chosen_type = type.capitalize() if type else None
        starters = [p for p in pokemons if p["evolution_stage"] == 0 and not p["is_legendary"]]

        if chosen_type:
            starters = [p for p in starters if chosen_type in p["type"]]
            if not starters:
                await interaction.response.send_message(
                    f"Aucun Pokémon de type **{chosen_type}** disponible comme starter.",
                    ephemeral=True
                )
                return

        choices = random.sample(starters, min(3, len(starters)))
        sprites, description = [], ""
        temp_data = []

        for poke in choices:
            shiny = self.check_shiny()
            gender = self.random_gender(poke)
            sprite = poke["sprite_shiny"] if shiny else poke["sprite"]
            sprites.append(sprite)
            shiny_star = "★" if shiny else ""
            types = " ".join(f"{TYPE_EMOJIS.get(t, '')} {t}" for t in poke["type"])
            description += f"**{poke['nom']} {shiny_star}** ({gender}) — {types}\n"
            temp_data.append({"nom": poke["nom"], "shiny": shiny, "gender": gender})

        # Sauvegarde temporaire dans le perso actif
        users[user_id]["characters"][active]["starters"] = temp_data
        self.save_users(users)

        file = self.merge_sprites(sprites)
        color = TYPE_COLORS.get(chosen_type, 0x88CCEE)

        embed = discord.Embed(
            title=f"🌟 Choisis ton starter ! ({active})",
            description=description,
            color=color
        )
        embed.set_image(url="attachment://starters.png")
        embed.set_footer(text="Utilise /choose pour sélectionner ton Pokémon !")

        await interaction.response.send_message(embed=embed, file=file)

    # --- /choose ---
    @discord.app_commands.command(
        name="choose",
        description="Choisis ton Pokémon starter parmi ceux proposés par /starter."
    )
    @discord.app_commands.describe(nom="Nom du Pokémon que tu veux choisir")
    async def choose(self, interaction: discord.Interaction, nom: str):
        users = self.load_users()
        user_id = str(interaction.user.id)

        if user_id not in users or not users[user_id].get("active"):
            await interaction.response.send_message(
                "Tu n’as pas encore de personnage actif. Utilise `/perso <nom>`.",
                ephemeral=True
            )
            return

        active = users[user_id]["active"]
        perso_data = users[user_id]["characters"].get(active, {})

        if "starters" not in perso_data:
            await interaction.response.send_message(
                "Tu n’as pas encore généré de starters avec `/starter` !", ephemeral=True
            )
            return

        starters = perso_data["starters"]
        choix = next((p for p in starters if p["nom"].lower() == nom.lower()), None)

        if not choix:
            noms_dispo = ", ".join([p["nom"] for p in starters])
            await interaction.response.send_message(
                f"Ce Pokémon n’était pas dans ta sélection. Choisis parmi : {noms_dispo}",
                ephemeral=True
            )
            return

        # Sauvegarde définitive du starter choisi
        users[user_id]["characters"][active] = {
            "starter": choix["nom"],
            "shiny": choix["shiny"],
            "gender": choix["gender"],
            "niveau": 5,
            "xp": 0
        }
        self.save_users(users)

        shiny_star = "★" if choix["shiny"] else ""
        await interaction.response.send_message(
            f"Tu as choisi **{choix['nom']} {shiny_star} ({choix['gender']})** comme starter pour **{active}** ! 🎉"
        )


async def setup(bot):
    await bot.add_cog(Starters(bot))
