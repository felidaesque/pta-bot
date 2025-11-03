import discord, json, os, requests
from discord.ext import commands

STATS_NAMES = ["attaque", "defense", "attaque_spé", "defense_spé", "vitesse"]

# tableau des modificateurs Aozora
def calc_mod(value: int) -> int:
    if value == 1: return 0
    if value in (2, 3): return 1
    if value in (4, 5): return 2
    if value in (6, 7): return 3
    if value in (8, 9): return 4
    if value in (10, 11): return 5
    if value in (12, 13): return 6
    if value in (14, 15): return 7
    return 0


class Stats(commands.Cog):
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

    # ---------------- Commande /stats set ---------------- #
    @discord.app_commands.command(
        name="stats_set",
        description="Assigne tes stats (doit contenir 2, 3, 4, 5 et 6 une seule fois chacun)."
    )
    @discord.app_commands.describe(
        attaque="Valeur d’attaque (2-6)",
        defense="Valeur de défense (2-6)",
        attaque_spé="Valeur d’attaque spéciale (2-6)",
        defense_spé="Valeur de défense spéciale (2-6)",
        vitesse="Valeur de vitesse (2-6)"
    )
    async def stats_set(self, interaction: discord.Interaction, attaque: int, defense: int, attaque_spé: int, defense_spé: int, vitesse: int):
        values = [attaque, defense, attaque_spé, defense_spé, vitesse]
        if sorted(values) != [2, 3, 4, 5, 6]:
            await interaction.response.send_message(
                "❌ Tu dois utiliser **exactement une fois chaque valeur 2, 3, 4, 5, 6**.", ephemeral=True
            )
            return

        users = self.load_users()
        user_id = str(interaction.user.id)
        if user_id not in users or not users[user_id].get("active"):
            await interaction.response.send_message(
                "Tu n’as encore aucun personnage actif. Utilise `/perso <nom>` pour en créer un !", ephemeral=True
            )
            return
        active = users[user_id]["active"]
        perso = users[user_id]["characters"].get(active, {})

        perso["stats"] = {
            "attaque": attaque,
            "defense": defense,
            "attaque_spé": attaque_spé,
            "defense_spé": defense_spé,
            "vitesse": vitesse
        }
        perso["modificateurs"] = {k: calc_mod(v) for k, v in perso["stats"].items()}
        perso["pvs"] = 20  # valeur initiale fixe
        users[user_id]["characters"][active] = perso

        self.save_users(users)
        await interaction.response.send_message(
            f"✅ Stats définies pour **{active}** : {attaque}/{defense}/{attaque_spé}/{defense_spé}/{vitesse}", ephemeral=True
        )

    # ---------------- Commande /stats afficher ---------------- #
    @discord.app_commands.command(
        name="stats",
        description="Affiche les stats et modificateurs du personnage actif."
    )
    async def stats(self, interaction: discord.Interaction):
        users = self.load_users()
        user_id = str(interaction.user.id)
        if user_id not in users or not users[user_id].get("active"):
            await interaction.response.send_message("Aucun personnage actif.", ephemeral=True)
            return
        active = users[user_id]["active"]
        perso = users[user_id]["characters"].get(active)
        stats = perso.get("stats")
        if not stats:
            await interaction.response.send_message(
                "Aucune stat définie. Utilise `/stats_set` pour les attribuer.", ephemeral=True
            )
            return

        mods = perso.get("modificateurs", {})
        desc = "\n".join([f"**{k.capitalize()}** : {v} 〔+{mods.get(k,0)}〕" for k, v in stats.items()])
        pvs = perso.get("pvs", 20)
        embed = discord.Embed(
            title=f"📊 Stats de {active}",
            description=f"{desc}\n\n❤️ PVs : {pvs}",
            color=0x88CCEE
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))
