import discord
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image
import aiohttp
import os

discord_token = ""

load_dotenv()
client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

directory = os.getcwd()
print(directory)

async def download_image(url, filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                # Define output folder
                output_folder = "to"

                # Check if the output folder exists, and create it if necessary
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)

                with open(f"{os.getcwd()}/{output_folder}/{filename}", "wb") as f:
                    f.write(await response.read())
                print(f"Image downloaded: {filename}")

@client.event
async def on_ready():
    print("Bot connected, ready to listen for images with \"Image #\" so I can download upscaled Midjourney images for you to process.\nI can also scrape images matching a string using !fetchall string")

@client.event
async def on_message(message):
    for attachment in message.attachments:
        if "Image #" in message.content:
            if attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                await download_image(attachment.url, f"{attachment.filename}")
    
    await client.process_commands(message)

@client.command()
async def fetchall(ctx, text):
    """Scrapes all images matching a string from the current channel. Useful if you forgot to run the bot before upscaling images."""
    messages = []
    await ctx.send(f"Scraping upscaled images matching \"{text}\"...")
    async for message in ctx.channel.history(limit=None):
        messages.append(message)

    images_downloaded = 0
    for message in messages:
        if text in message.content and "Image #" in message.content:
            for attachment in message.attachments:
                if attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                    await download_image(attachment.url, f"{attachment.filename}")
                    images_downloaded += 1
    if images_downloaded > 0:
        await ctx.send(f"Scraped {images_downloaded} images matching \"{text}\".")
    else:
        await ctx.send(f"Found no images matching \"{text}\". Look again, Sherlock.")

client.run(discord_token)
