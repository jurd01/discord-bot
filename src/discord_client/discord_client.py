import asyncio
import re

from discord.ext import commands

from src.abc.service import Service
from src.twitch.twitchclient import TwitchClient
from src.util.constants import SUBSCRIPTIONS, DISCORD_FORMATTING_CHARS
from src.util.dataclasses import Notification, Subscription
from src.util.logging import get_logger

logger = get_logger(__name__)


class DiscordClient(commands.Bot, Service):
    # TODO decouple twitch client
    def __init__(self, token, command_prefix, twitch_client: TwitchClient, **options):
        self.token = token
        super().__init__(command_prefix, **options)
        self.remove_command('help')
        self.add_cog(Commands(command_prefix))
        self.twitch_client = twitch_client

    def run(self):
        super().run(self.token)

    def shutdown(self):
        self.logout()
        logger.info('Bot logged out.')

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Discord bot started as {self.user.name}")
        # await self.send_live_notif(Notification(1,1,'jurd_',1,'','live','live test!',1,'','',''))

    def _build_live_notif(self, notif: Notification, sub: Subscription):
        game_name = self.twitch_client.get_game_name(notif.game_id)
        message = f'{sub.mention} {notif.user_name} is live! ' \
            f'- {notif.title} ' \
            f'- {game_name}\n'

        for c in DISCORD_FORMATTING_CHARS:
            message = message.replace(c, '\\' + c)

        # don't replace chars in url
        message += f'https://www.twitch.tv/{notif.user_name}'

        logger.debug(f'Message to send: {message}')
        return message

    async def _send_live_notif(self, notif: Notification, sub: Subscription):
        try:
            await self.get_guild(sub.server_id).get_channel(sub.channel_id).send(
                self._build_live_notif(notif, sub))
        except Exception as e:
            logger.exception(e)
            # logger.error(e)

    async def send_live_notif(self, notif: Notification):
        """
        {
            'id': '0123456789',
            'user_id': '5678',
            'user_name': 'wjdtkdqhs',
            'game_id': '21779',
            'community_ids': [],
            'type': 'live',
            'title': 'Best Stream Ever',
            'viewer_count': 417,
            'started_at': '2017-12-01T10:09:45Z',
            'language': 'en',
            'thumbnail_url': 'https://link/to/thumbnail.jpg'
        }
        """
        await asyncio.gather(
            *[self._send_live_notif(notif, sub) for sub in SUBSCRIPTIONS if sub.user_name == notif.user_name])


class Commands(commands.Cog):
    def __init__(self, command_prefix):
        self.command_prefix = command_prefix

    @commands.command(help="This is a test command.")
    async def test(self, context):
        await context.send('hello!')

    @commands.command(pass_context=True)
    async def info(self, ctx):
        # TODO version
        return await ctx.send("""
```
I send notifications when streams go live!
Version: `0.0.1`
Author: @jurd#0202
Source: https://github.com/jurd01/discord-bot/
```
        """)

    @commands.command(help="Help!", pass_context=True)
    async def help(self, ctx, *args):
        # default help
        if len(args) != 1:
            return await ctx.invoke(self.info)
        else:
            command_to_get_help_for = args[0]
            if not command_to_get_help_for.startswith(self.command_prefix):
                return await ctx.send(f'!help takes no parameters, '
                                      f'or the name of a command (including {self.command_prefix}).')

            command_no_prefix = command_to_get_help_for.replace(self.command_prefix, "")
            for command in self.get_commands():
                if command.name == command_no_prefix:
                    return await ctx.send(command.help)

            return await ctx.send(f'Command {command_to_get_help_for} not found!')
