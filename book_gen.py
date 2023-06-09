import os
import discord
from discord.ext import tasks
from discord.components import ActionRow, Button, ButtonStyle
from dotenv import load_dotenv
import openai_async

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

class BotClient(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = discord.app_commands.CommandTree(self)

    async def on_ready(self):
        self.tree.copy_global_to(guild=self.guilds[0])
        await self.tree.sync()
        print(f'We have logged in as {self.user}')
        generate_ideas.start()  # Start the task

client = BotClient()

@client.tree.command(name="coloring_channel", description="Generate a coloring book idea and create a channel for it")
async def generate_ideas(interaction: discord.Interaction):
    guild = client.guilds[0]  # Change to your guild
    response = await openai_async.complete(
        f"{OPENAI_KEY}",
        timeout=30,
        payload={
            "model": "text-davinci-003",
            "prompt": "Generate a single coloring book idea\n\n\Ensure the name is 50 characters or less and replace spaces with \"-\".\n\n Examples: [frogs, dogs-in-boxes, cats-on-roofs, frogs-in-water]",
            "max_tokens": 100,
        }
    )
    idea = response.json()["choices"][0]["text"].strip()
    await guild.create_text_channel(idea)
    interaction.response.send_message(f"Created channel: #{idea}")

class ButtonView(discord.ui.View):
    @discord.ui.button(label="V", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction):
        await interaction.response.send_message("Please enter your own prompt:")

@client.tree.command(name="generate", description="Generate coloring page ideas")
async def generate(interaction: discord.Interaction, num_prompts: int) -> None:
    if num_prompts > 5:
        await interaction.response.send_message("You can only generate up to 5 prompts at a time.", ephemeral=True)
        return

    initial_response = await interaction.response.send_message(f"Generating {num_prompts} ideas...")
    print(f"initial_response: {initial_response}")

    prompts = []
    for _ in range(num_prompts):
        response = await openai_async.complete(
            f"{OPENAI_KEY}",
            timeout=30,
            payload={
                "model": "text-davinci-003",
                "prompt": f"Generate a unique or interesting single-sentence description of an image for {interaction.channel.name}. Keep it short but descriptive and replace commas with spaces.",
                "temperature": 1.0,
                "max_tokens": 500
            },
        )
        prefix='a picture of a thick-lined, simple-shaped, coloring book page, '
        suffix=', in the style of barbiecore, disney animation, caffenol developing, hurufiyya, dynamic and spontaneous, sleek, rinpa school, --no border, --ar 35:45'
        text_response=response.json()["choices"][0]["text"].strip()
        prompts.append(text_response)
        print(text_response)

        return_prompt = prefix + "{" + ",".join(prompts) + "}" + suffix
    if initial_response is not None:    
        await initial_response.edit(content='\n'.join(prompts), view=ButtonView())
    else:
        await interaction.followup.send(f"Here are {num_prompts} coloring page ideas:\n" + return_prompt, ephemeral=True, view=ButtonView())
    print(f"prompts: {prompts}")

client.run(DISCORD_TOKEN)
