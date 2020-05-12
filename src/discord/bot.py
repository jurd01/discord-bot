import os

import discord

from src.util.logging import get_logger

client = discord.Client()

logger = get_logger(__name__)


@client.event
async def on_ready():
    logger.info(f"Discord bot started as {client}")


@client.event
async def on_message(message):
    pass

client.run(os.getenv('DISCORD_CLIENT_TOKEN'))
