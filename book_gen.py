import os
import time
import discord
from discord.ext import tasks
from discord.components import ActionRow, Button, ButtonStyle
from dotenv import load_dotenv
import openai_async
import pyautogui as pg

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

client = BotClient()

class ButtonView(discord.ui.View):
    @discord.ui.button(label="V", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction):
        await interaction.response.send_message("Please enter your own prompt:")

class NewChannelButtonView(discord.ui.View):
    def __init__(self, channel_id: int):
        super().__init__()
        self.channel_id = channel_id

    @discord.ui.button(label="Link to channel", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction, item=None):
        channel = client.get_channel(self.channel_id)                
        await interaction.response.send_message(f"Here is the link to your new channel: {channel.mention}", ephemeral=True)
    
# make button to go to new channel
# get message with interaction.original_response()
# use message.channel.mention to make link

@client.tree.command(name="new_coloring_book", description="Create a new coloring book with a title, description, and 7 search keywords")
async def new_coloring_book(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(f"Generating new book")
    name = await create_channel_name()
    channel_name = name.replace(" ", "-").strip()
    initial_response = await interaction.original_response()
    await initial_response.edit(content=f"Generating new book: {channel_name}")

    subtitle = await create_book_subtitle_str(name)
    await initial_response.edit(content=f"Generating new book: {channel_name}, with subtitle: {subtitle}")

    description = await create_book_description_str(name)
    await initial_response.edit(content=f"Generating new book: {channel_name}, with description: {description}")
    
    keywords = await create_book_keywords_str(name)
    await initial_response.edit(content=f"Generated new book: {channel_name}, with description: {description} and keywords: {keywords}")

    topic = f"Description: {description}\n\nSubtitle: {subtitle}\n\nKeywords: {keywords}"
    channel = await interaction.guild.create_text_channel(channel_name, topic=topic)

    await initial_response.edit(content=f"Generated new book: {channel.mention}, with description: {description} and keywords: {keywords}", view=NewChannelButtonView(channel.id))
    # add image scraper
    role = discord.utils.get(interaction.guild.roles, name="midjourney prompt feeder")
    await channel.set_permissions(role, read_messages=True, send_messages=True)
    await channel.send(f"Welcome to {channel_name}! This channel is for generating coloring book pages related to {name}. To generate `n` coloring book pages with your own prompt, type `/generate` in this channel (i.e. `/generate 2` to generate 2 pages). To generate a new coloring book, type `/new_coloring_book` in this channel (this will create a new channel with title, description, and keywords).\n\n{topic}")

async def create_channel_name():
    name_response = await text_response(prompt="Generate a unique or interesting title for a children's coloring book. Keep it short but descriptive.", max_tokens=100)
    return name_response

@client.tree.command(name="create_book_description", description="Create a description for a coloring book based on a name")
async def create_book_description(interaction: discord.Interaction, name: str) -> None:
    description = await create_book_description_str(name)
    await interaction.response.send_message(f'Description for {name}: {description}')

async def create_book_description_str(name: str):
    topic_response = await text_response(prompt=f"Generate a unique or interesting description of a children's coloring book about {name}. Keep it short but descriptive.", max_tokens=1000)
    return topic_response

@client.tree.command(name="create_book_subtitle", description="Create a subtitle for a coloring book based on a name")
async def create_book_subtitle(interaction: discord.Interaction, name: str) -> None:
    subtitle = await create_book_subtitle_str(name)
    await interaction.response.send_message(f'Subtitle for {name}: {subtitle}')

async def create_book_subtitle_str(name: str):
    subtitle_response = await text_response(prompt=f"Generate a unique or interesting subtitle for a children's coloring book about {name}. Keep it short but descriptive.", max_tokens=50)
    return subtitle_response

@client.tree.command(name="create_book_keywords", description="Create keywords for a coloring book based on a name")
async def create_book_keywords(interaction: discord.Interaction, name: str) -> None:
    keywords = await create_book_keywords_str(name)
    await interaction.response.send_message(f'Keywords for {name}: {keywords}')

async def create_book_keywords_str(name: str):
    keywords_response = await text_response(prompt=f"Generate 7 unique or interesting keywords optimized for search for a children's coloring book about {name}. Keep them short but descriptive.", max_tokens=100)
    return keywords_response

async def text_response(prompt: str, max_tokens: int = 500, model = "text-davinci-003"):
    response = await openai_async.complete(
        f"{OPENAI_KEY}",
        timeout=30,
        payload={
            "model": model,
            "prompt": prompt,
            "temperature": 1.0,
            "max_tokens": max_tokens
        },
    )
    return response.json()["choices"][0]["text"].strip()

@client.tree.command(name="generate", description="Generate coloring page ideas")
async def generate(interaction: discord.Interaction, num_prompts: int) -> None:
    print("foo")
    if num_prompts > 50:
        await interaction.response.send_message("You can only generate up to 50 prompts at a time.", ephemeral=True)
        return
    
    if interaction.channel.topic is None:
        interaction.channel.topic = await create_book_description_str(interaction.channel.name)

    initial_response = await interaction.response.send_message(f"Generating {num_prompts} ideas...")
    print(f"initial_response: {initial_response}")

    prompts = []
    for _ in range(num_prompts):
        response = await openai_async.complete(
            f"{OPENAI_KEY}",
            timeout=30,
            payload={
                "model": "text-davinci-003",
                "prompt": f"Generate a unique or interesting single-sentence description of an image suitable for a children's coloring page about {interaction.channel.topic}. Keep it short but descriptive, do not include colors.",
                "temperature": 1.0,
                "max_tokens": 500
            },
        )
        prefix='a picture of a thick-lined, simple-shaped, coloring book page, '
        suffix=', in the style of barbiecore, disney animation, caffenol developing, hurufiyya, dynamic and spontaneous, sleek, rinpa school, --no border, --ar 35:45'
        prompt_response=response.json()["choices"][0]["text"].replace(',', ' ').strip()
        prompts.append(prompt_response)        

        # Here we send the prompt to Midjourney using PyAutoGUI
        pg.typewrite('/imagine')
        pg.typewrite(' ') # better success rate with separate command for space
        pg.press('enter')
        pg.typewrite(prefix + text_response + suffix)
        pg.press('enter')

    result_message = f"Generated {len(prompts)} Coloring Pages for {interaction.channel.topic}"

    if initial_response is not None:    
        await initial_response.edit(content=result_message, view=ButtonView())
    else:
        await interaction.followup.send(result_message, ephemeral=True, view=ButtonView())
    print(f"prompts: {prompts}")

client.run(DISCORD_TOKEN)
