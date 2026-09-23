import os
import json
import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DATA_FILE = "scripts.json"

# =========================================================
# ONLY THESE 4 ROLES CAN CREATE THE HUB PANEL
# =========================================================

ALLOWED_SETUP_ROLES = {
    1545926929868390534,
    1534370551114498156,
    1545926740692574288,
    1534370551152246956
}

# =========================================================
# BOT
# =========================================================

intents = discord.Intents.default()

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


# =========================================================
# SCRIPT STORAGE
# =========================================================

def load_scripts():
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return {}


def save_scripts(scripts):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            scripts,
            file,
            indent=4,
            ensure_ascii=False
        )


# =========================================================
# SCRIPT PAGE
# =========================================================

class ScriptPageView(discord.ui.View):

    def __init__(self, script_name):
        super().__init__(timeout=300)

        self.script_name = script_name

    @discord.ui.button(
        label="Mobile View",
        emoji="📱",
        style=discord.ButtonStyle.secondary
    )
    async def mobile_view(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        scripts = load_scripts()
        script = scripts.get(self.script_name)

        if not script:
            await interaction.response.send_message(
                "❌ Script no longer exists.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=self.script_name,
            description=script.get(
                "description",
                "No description."
            ),
            color=discord.Color.from_rgb(
                20,
                200,
                255
            )
        )

        image = script.get("image")

        if image:
            embed.set_image(url=image)

        embed.add_field(
            name="Version",
            value=script.get("version", "V1"),
            inline=True
        )

        embed.add_field(
            name="Status",
            value="🟢 Updated",
            inline=True
        )

        embed.add_field(
            name="Added By",
            value=script.get("author", "Unknown"),
            inline=True
        )

        code = script.get("code", "")

        if code:
            embed.add_field(
                name="Script",
                value=f"```lua\n{code[:3900]}\n```",
                inline=False
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# =========================================================
# SCRIPT DROPDOWN
# =========================================================

class ScriptSelect(discord.ui.Select):

    def __init__(self):

        scripts = load_scripts()

        options = []

        for name, data in list(scripts.items())[:25]:

            options.append(
                discord.SelectOption(
                    label=name[:100],
                    description=data.get(
                        "description",
                        "Free script"
                    )[:100],
                    emoji="📜"
                )
            )

        if not options:

            options.append(
                discord.SelectOption(
                    label="No scripts available",
                    description="Use /addscript to add one.",
                    emoji="📭"
                )
            )

        super().__init__(
            placeholder="Pick a script...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        selected = self.values[0]

        if selected == "No scripts available":

            await interaction.response.send_message(
                "📭 There are no scripts yet.\n"
                "Use `/addscript` to add one.",
                ephemeral=True
            )

            return

        scripts = load_scripts()
        script = scripts.get(selected)

        if not script:

            await interaction.response.send_message(
                "❌ Script not found.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title=selected,
            description=script.get(
                "description",
                "No description."
            ),
            color=discord.Color.from_rgb(
                20,
                200,
                255
            )
        )

        image = script.get("image")

        if image:
            embed.set_image(url=image)

        embed.add_field(
            name="Version",
            value=script.get("version", "V1"),
            inline=True
        )

        embed.add_field(
            name="Status",
            value="🟢 Updated",
            inline=True
        )

        embed.add_field(
            name="Added By",
            value=script.get("author", "Unknown"),
            inline=True
        )

        code = script.get("code", "")

        if code:
            embed.add_field(
                name="Script",
                value=f"```lua\n{code[:3900]}\n```",
                inline=False
            )

        await interaction.response.send_message(
            embed=embed,
            view=ScriptPageView(selected),
            ephemeral=True
        )


# =========================================================
# HUB VIEW
# =========================================================

class HubView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(
            ScriptSelect()
        )


# =========================================================
# SETUP
# =========================================================

@tree.command(
    name="setup",
    description="Create the Messbitious Hub Free Scripts panel."
)
async def setup(interaction: discord.Interaction):

    member = interaction.user

    if not isinstance(member, discord.Member):

        await interaction.response.send_message(
            "❌ This command must be used inside the server.",
            ephemeral=True
        )

        return

    has_allowed_role = any(
        role.id in ALLOWED_SETUP_ROLES
        for role in member.roles
    )

    if not has_allowed_role:

        await interaction.response.send_message(
            "❌ You don't have permission to create the hub panel.",
            ephemeral=True
        )

        return

    embed = discord.Embed(
        title="Messbitious Hub",
        description=(
            "Welcome to **Messbitious Hub Free Scripts**.\n\n"
            "📜 Pick a script from the menu below."
        ),
        color=discord.Color.from_rgb(
            20,
            200,
            255
        )
    )

    embed.add_field(
        name="⚡ Free Scripts",
        value=(
            "Browse the available scripts "
            "using the dropdown below."
        ),
        inline=False
    )

    embed.set_footer(
        text="Messbitious Hub Free Scripts"
    )

    await interaction.channel.send(
        embed=embed,
        view=HubView()
    )

    await interaction.response.send_message(
        "✅ Hub panel created!",
        ephemeral=True
    )


# =========================================================
# ADD SCRIPT
# =========================================================

@tree.command(
    name="addscript",
    description="Add a free development script to the hub."
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
@app_commands.describe(
    name="Script name",
    description="Short script description",
    version="Script version",
    image="Direct image URL",
    code="Script code"
)
async def addscript(
    interaction: discord.Interaction,
    name: str,
    description: str,
    version: str,
    image: str,
    code: str
):

    scripts = load_scripts()

    scripts[name] = {
        "description": description,
        "version": version,
        "image": image,
        "code": code,
        "author": interaction.user.display_name
    }

    save_scripts(scripts)

    embed = discord.Embed(
        title="✅ Script Added",
        description=(
            f"**{name}** was added to "
            "**Messbitious Hub Free Scripts**."
        ),
        color=discord.Color.from_rgb(
            20,
            200,
            255
        )
    )

    if image:
        embed.set_thumbnail(url=image)

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# =========================================================
# REMOVE SCRIPT
# =========================================================

@tree.command(
    name="removescript",
    description="Remove a script from the hub."
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
@app_commands.describe(
    name="Name of the script"
)
async def removescript(
    interaction: discord.Interaction,
    name: str
):

    scripts = load_scripts()

    if name not in scripts:

        await interaction.response.send_message(
            "❌ That script doesn't exist.",
            ephemeral=True
        )

        return

    del scripts[name]

    save_scripts(scripts)

    await interaction.response.send_message(
        f"🗑️ **{name}** was removed.",
        ephemeral=True
    )


# =========================================================
# SCRIPTS
# =========================================================

@tree.command(
    name="scripts",
    description="Open Messbitious Hub Free Scripts."
)
async def scripts(interaction: discord.Interaction):

    embed = discord.Embed(
        title="Messbitious Hub",
        description="📜 Pick a script from the menu below.",
        color=discord.Color.from_rgb(
            20,
            200,
            255
        )
    )

    embed.set_footer(
        text="Messbitious Hub Free Scripts"
    )

    await interaction.response.send_message(
        embed=embed,
        view=HubView()
    )


# =========================================================
# HELP
# =========================================================

@tree.command(
    name="help",
    description="Show Messbitious Hub commands."
)
async def help_command(interaction: discord.Interaction):

    embed = discord.Embed(
        title="Messbitious Hub Free Scripts",
        description=(
            "📜 **Public Commands**\n"
            "`/scripts` — Open the script hub\n"
            "`/help` — Show commands\n\n"
            "🛠️ **Staff Commands**\n"
            "`/setup` — Create the hub panel\n"
            "`/addscript` — Add a script\n"
            "`/removescript` — Remove a script"
        ),
        color=discord.Color.from_rgb(
            20,
            200,
            255
        )
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# =========================================================
# BOT READY
# =========================================================

@bot.event
async def on_ready():

    await tree.sync()

    print(
        f"Logged in as {bot.user}"
    )

    print(
        "⚡ Messbitious Hub Free Scripts is online!"
    )


# =========================================================
# START
# =========================================================

if not TOKEN:

    raise RuntimeError(
        "DISCORD_TOKEN is missing from .env"
    )

bot.run(TOKEN)