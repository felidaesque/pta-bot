import discord, json, os, requests
from discord.ext import commands

CLASSES_DE_BASE = [
    "Topdresseur",
    "Éleveur",
    "Coordinateur",
    "Ranger",
    "Chercheur",
    "Artiste martial",
    "Télékinésiste"
]

CLASSES_AVANCEES = {
    "Topdresseur": ["As des stats", "Stratège", "Combattant de groupe", "Spécialiste d’un type", "Outsider"],
    "Éleveur": ["Botaniste", "Chef", "Évolutif", "Médecin", "Maître des capacités"],
    "Coordinateur": ["Chorégraphe", "Coach", "Designer", "Toiletteur", "Étoile montante"],
    "Ranger": ["Invocateur", "Officier", "Cavalier", "Agent spécial", "Survivaliste"],
    "Chercheur": ["Archéologue", "Artisan Pokéball", "Photographe", "Scientifique", "Observateur"],
    "Artiste martial": ["Maître d’aura", "Bagarreur déloyal", "Mentor", "Ninja", "Yogi"],
    "Télékinésiste": ["Adepte de l’air", "Secoueur de terre", "Souffleur de feu", "Mystimaniac", "Éveilleur de pluie"]
}


class Classes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.GIST_ID = "b4485737f8d88706b414392796f3843f"

    # ---------------- Utilitaires Gist ---------------- #
    def load_users(self):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            print("[❌] Aucun GITHUB_TOKEN défini.")
            return {}
        try:
            url = f"https://api.github.com/gists/{self.GIST_ID}"
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            content = r.json()["files"]["users.json"]["content"]
            return json.loads(content)
        except Exception as e:
            print(f"[❌] Erreur lecture users.json : {e}")
            return {}

    def save_users(self, data):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            print("[❌] Aucun GITHUB_TOKEN défini.")
            return
        try:
            url = f"https://api.github.com/gists/{self.GIST_ID}"
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
            payload = {"files": {"users.json": {"content": json.dumps(data, ensure_ascii=False, indent=2)}}}
            requests.patch(url, headers=headers, json=payload, timeout=10)
        except Exception as e:
            print(f"[❌] Erreur sauvegarde users.json : {e}")

    # ---------------- /classe ---------------- #
    @discord.app_commands.command(
        name="classe",
        description="Choisis ta classe de dresseur pour ton personnage actif."
    )
    @discord.app_commands.describe(nom="Nom de la classe à choisir (ex: Ranger, Chercheur...)")
    async def classe(self, interaction: discord.Interaction, nom: str):
        users = self.load_users()
        user_id = str(interaction.user.id)
        if user_id not in users or not users[user_id].get("active"):
            await interaction.response.send_message(
                "Tu n’as aucun personnage actif. Utilise `/perso <nom>`.", ephemeral=True
            )
            return

        active = users[user_id]["active"]
        perso = users[user_id]["characters"].get(active, {})

        nom = nom.strip().capitalize()
        if nom not in [c.capitalize() for c in CLASSES_DE_BASE]:
            await interaction.response.send_message(
                f"❌ Classe inconnue. Choisis parmi : {', '.join(CLASSES_DE_BASE)}", ephemeral=True
            )
            return

        if "classes" in perso and len(perso["classes"]) > 0:
            await interaction.response.send_message(
                "Ce personnage a déjà une classe. Les suivantes doivent être ajoutées par un MJ.",
                ephemeral=True
            )
            return

        perso["classes"] = [{"nom": nom, "niveau": 1}]
        users[user_id]["characters"][active] = perso
        self.save_users(users)
        await interaction.response.send_message(f"✅ Classe **{nom}** choisie pour **{active}** !")

    # ---------------- /classes ---------------- #
    @discord.app_commands.command(
        name="classes",
        description="Affiche les classes de ton personnage actif."
    )
    async def classes(self, interaction: discord.Interaction):
        users = self.load_users()
        user_id = str(interaction.user.id)
        if user_id not in users or not users[user_id].get("active"):
            await interaction.response.send_message("Aucun personnage actif.", ephemeral=True)
            return

        active = users[user_id]["active"]
        perso = users[user_id]["characters"].get(active, {})
        classes = perso.get("classes")

        if not classes:
            await interaction.response.send_message(
                "Aucune classe définie. Utilise `/classe <nom>` pour en choisir une.", ephemeral=True
            )
            return

        desc = ""
        for c in classes:
            desc += f"• **{c['nom']}** — Niveau {c['niveau']}\n"
            if c["nom"] in CLASSES_AVANCEES:
                desc += f"  → Sous-classes possibles : {', '.join(CLASSES_AVANCEES[c['nom']])}\n"

        embed = discord.Embed(
            title=f"🦋 Classes de {active}",
            description=desc,
            color=0x88CCEE
        )
        await interaction.response.send_message(embed=embed)

    # ---------------- /classe_ajouter ---------------- #
    @discord.app_commands.command(
        name="classe_ajouter",
        description="(ADMIN) Ajoute une classe supplémentaire à un personnage (base ou avancée)."
    )
    @discord.app_commands.describe(nom="Nom de la classe à ajouter")
    @commands.has_permissions(administrator=True)
    async def classe_ajouter(self, interaction: discord.Interaction, nom: str):
        users = self.load_users()
        user_id = str(interaction.user.id)
        if user_id not in users or not users[user_id].get("active"):
            await interaction.response.send_message("Tu n’as aucun personnage actif.", ephemeral=True)
            return

        active = users[user_id]["active"]
        perso = users[user_id]["characters"].get(active, {})

        nom = nom.strip().capitalize()
        perso.setdefault("classes", []).append({"nom": nom, "niveau": 1})
        users[user_id]["characters"][active] = perso
        self.save_users(users)
        await interaction.response.send_message(f"🆕 Classe **{nom}** ajoutée à **{active}**.")

async def setup(bot):
    await bot.add_cog(Classes(bot))
