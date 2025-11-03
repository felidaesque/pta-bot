import discord, json, os, requests
from discord.ext import commands

# Niveaux d’après ton tableau Aozora
DISTINCTION_THRESHOLDS = {
    1: 0,  2: 1,  3: 2,  4: 3,  5: 5,  6: 7,  7: 9,
    8: 12, 9: 15, 10: 18, 11: 22, 12: 26, 13: 30,
    14: 35, 15: 40
}

PALIER_LEVELS = [3, 7, 11]


class Distinctions(commands.Cog):
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

    # ---------------- /distinction_ajouter (ADMIN) ---------------- #
    @discord.app_commands.command(
        name="distinction_ajouter",
        description="(ADMIN) Ajoute une distinction (badge, concours, etc.) à un personnage spécifique."
    )
    @discord.app_commands.describe(
        user="Utilisateur concerné",
        character="Nom du personnage",
        nom="Nom ou description de la distinction"
    )
    @commands.has_permissions(administrator=True)
    async def distinction_ajouter(self, interaction: discord.Interaction, user: discord.User, character: str, nom: str):
        users = self.load_users()
        target_id = str(user.id)

        if target_id not in users or character not in users[target_id].get("characters", {}):
            await interaction.response.send_message(
                f"❌ Impossible de trouver le personnage **{character}** pour {user.display_name}.",
                ephemeral=True
            )
            return

        perso = users[target_id]["characters"][character]
        distinctions = perso.setdefault("distinctions", [])
        nom = nom.strip()

        if nom in distinctions:
            await interaction.response.send_message(
                f"⚠️ Le personnage **{character}** a déjà la distinction **{nom}**.", ephemeral=True
            )
            return

        distinctions.append(nom)
        self.update_level(perso)
        users[target_id]["characters"][character] = perso
        self.save_users(users)

        await interaction.response.send_message(
            f"🏅 Distinction **{nom}** ajoutée à **{character}** ({user.display_name}) ! Niveau actuel : {perso.get('niveau', 1)}"
        )

    # ---------------- /distinctions ---------------- #
    @discord.app_commands.command(
        name="distinctions",
        description="Affiche la liste des distinctions et le niveau de ton personnage actif."
    )
    async def distinctions(self, interaction: discord.Interaction):
        users = self.load_users()
        user_id = str(interaction.user.id)
        if user_id not in users or not users[user_id].get("active"):
            await interaction.response.send_message("Aucun personnage actif.", ephemeral=True)
            return

        active = users[user_id]["active"]
        perso = users[user_id]["characters"].get(active, {})
        distinctions = perso.get("distinctions", [])
        niveau = perso.get("niveau", 1)
        total = len(distinctions)

        desc = "\n".join([f"• {d}" for d in distinctions]) if distinctions else "Aucune distinction pour le moment."
        embed = discord.Embed(
            title=f"🏆 Distinctions de {active}",
            description=f"{desc}\n\n📈 **Total :** {total}\n⭐ **Niveau actuel :** {niveau}",
            color=0xFFD700
        )
        await interaction.response.send_message(embed=embed)

    # ---------------- /niveau ---------------- #
    @discord.app_commands.command(
        name="niveau",
        description="Affiche le niveau actuel et la progression vers le prochain niveau."
    )
    async def niveau(self, interaction: discord.Interaction):
        users = self.load_users()
        user_id = str(interaction.user.id)
        if user_id not in users or not users[user_id].get("active"):
            await interaction.response.send_message("Aucun personnage actif.", ephemeral=True)
            return

        active = users[user_id]["active"]
        perso = users[user_id]["characters"].get(active, {})
        distinctions = perso.get("distinctions", [])
        niveau = perso.get("niveau", 1)
        total = len(distinctions)

        next_level = niveau + 1
        needed = DISTINCTION_THRESHOLDS.get(next_level)
        if needed is None:
            msg = f"🎓 {active} est au niveau maximum ({niveau}) !"
        else:
            rest = max(0, needed - total)
            msg = f"⭐ Niveau {niveau} — {total} distinctions\n➡️ Il en faut encore **{rest}** pour atteindre le niveau {next_level}."

        embed = discord.Embed(title=f"Niveau de {active}", description=msg, color=0x88CCEE)
        await interaction.response.send_message(embed=embed)

    # ---------------- Fonction : calcul automatique de niveau ---------------- #
    def update_level(self, perso: dict):
        """Met à jour le niveau et les PVs selon le nombre de distinctions."""
        total = len(perso.get("distinctions", []))
        current = perso.get("niveau", 1)
        new_level = current

        for lvl, threshold in sorted(DISTINCTION_THRESHOLDS.items()):
            if total >= threshold:
                new_level = lvl

        if new_level > current:
            perso["niveau"] = new_level
            if "pvs" not in perso:
                perso["pvs"] = 20
            for palier in PALIER_LEVELS:
                if current < palier <= new_level:
                    perso["pvs"] += 4
            print(f"[⭐] {perso.get('nom','(sans nom)')} passe au niveau {new_level} (+PV).")


async def setup(bot):
    await bot.add_cog(Distinctions(bot))
