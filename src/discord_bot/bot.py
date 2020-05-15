from discord.ext import commands

from src.util.constants import ANNOUNCE_CHANNEL
from src.util.logging import get_logger

logger = get_logger(__name__)


class Bot(commands.Bot):
    def __init__(self, token, command_prefix, **options):
        self.token = token
        super().__init__(command_prefix, **options)
        self.remove_command('help')
        self.add_cog(Commands(command_prefix))

    def run(self):
        super().run(self.token)

    def shutdown(self):
        self.logout()
        logger.info('Bot logged out.')

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Discord bot started as {super()}")

    async def send_live_notif(self, data):
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
        user_name = data['user_name']
        await self.get_channel(ANNOUNCE_CHANNEL).send(f'@everyone https://www.twitch.tv/{user_name}')


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
