from asyncio import sleep
from typing import Union

from discord import Reaction, Member, TextChannel, User, Intents, HTTPException, LoginFailure
from discord.ext import commands
from discord.ext.commands import Bot, CommandError, UserInputError, CommandNotFound

from .flags import *
from .settings import *

_log = logging.getLogger(__name__)


class ReactionsHelper(Bot):
    def __init__(self, config_filepath: str, config: Settings):
        self._config_filepath = config_filepath
        self._config = config
        _log.info(f'Data stored in: {config_filepath}')

        intents = Intents.default()
        intents.messages = True
        super().__init__(intents=intents, command_prefix=self._config.command_prefix)
        self.help_command.add_check(self.has_permissions())

        self.setup_commands()

    async def on_ready(self):
        _log.info(f'{self.user} ready')

    async def on_command_error(self, ctx, exception: CommandError):
        if isinstance(exception, UserInputError):
            await ctx.send(str(exception))
        else:
            _log.error(str(exception))

    async def on_reaction_add(self, reaction: Reaction, user: Union[Member, User]):
        if self._config.channels.__contains__(reaction.message.channel.id):
            if self._config.reactions.__contains__(str(reaction.emoji)):
                await reaction.message.remove_reaction(reaction, user)

    @staticmethod
    def has_permissions():
        return commands.has_permissions(manage_messages=True)

    def run_with_token(self):
        try:
            super().run(self._config.token)
        except LoginFailure as e:
            _log.error(str(e))
            _log.error('Specify token in ~/.reactionshelperbot.json')

    def setup_commands(self):
        # Channels
        @self.group(name='channels')
        @self.has_permissions()
        async def channels(ctx: Union[TextChannel, Member]):
            if ctx.invoked_subcommand is None:
                await show_channels(ctx)

        @channels.command(name='add')
        async def add_channel(ctx: Union[TextChannel, Member], *, args=None):
            if not args:
                raise UserInputError(message='No channels')

            channel = await get_channel_by_name(ctx, args)
            if self._config.channels.__contains__(channel.id):
                raise UserInputError(message=f'{channel.name} already added')

            self._config.channels.append(channel.id)
            self._config.save(self._config_filepath)
            await ctx.send(f'{channel.name} added')

        @channels.command(name='remove')
        async def remove_channel(ctx: Union[TextChannel, Member], *, args=None):
            if not args:
                raise UserInputError(message='No channels')

            channel = await get_channel_by_name(ctx, args)

            if not self._config.channels.__contains__(channel.id):
                raise UserInputError(message=f'{channel.name} not added')

            self._config.channels.remove(channel.id)
            self._config.save(self._config_filepath)
            await ctx.send(f'{channel.name} removed')

        @channels.command(name='clear')
        async def clear_channels(ctx: Union[TextChannel, Member]):
            self._config.channels.clear()
            self._config.save(self._config_filepath)
            await ctx.send('Cleared')

        @channels.command(name='show')
        async def show_channels(ctx: Union[TextChannel, Member]):
            if len(self._config.channels) == 0:
                await ctx.send('No channels')
            else:
                await check_channels(ctx)
                all_channels = ', '.join(ctx.guild.get_channel(i).name for i in self._config.channels)
                await ctx.send(f'Channels: {all_channels}')

        async def get_channel_by_name(ctx, args):
            try:
                return await commands.TextChannelConverter().convert(ctx, args)
            except TypeError:
                raise UserInputError(message=f'Channel {args} not found. Requires string channel name')

        async def check_channels(ctx: Union[TextChannel, Member]):
            checked = list()
            removed = list()
            for channel in self._config.channels:
                if ctx.guild.get_channel(channel):
                    checked.append(channel)
                else:
                    removed.append(channel)

            if len(removed) > 0:
                self._config.channels = checked
                self._config.save(self._config_filepath)

        # Reactions
        @self.group(name='reactions')
        @self.has_permissions()
        async def reactions(ctx: Union[TextChannel, Member]):
            if ctx.invoked_subcommand is None:
                await show_reactions(ctx)

        @reactions.command(name='add')
        async def add_reactions(ctx: Union[TextChannel, Member], *, args=None):
            if not args:
                raise UserInputError(message='No reactions')

            await ctx.message.add_reaction(self._config.processing_reaction)
            already_added = list()
            unknown = list()
            added = list()
            for reaction in args.split():
                if self._config.reactions.__contains__(reaction):
                    already_added.append(reaction)
                elif not await is_reaction(ctx, reaction):
                    unknown.append(reaction)
                else:
                    added.append(reaction)
                    self._config.reactions.append(reaction)
            self._config.save(self._config_filepath)
            await ctx.message.remove_reaction(self._config.processing_reaction, self.user)

            result = list()
            if len(already_added) > 0:
                result.append(' '.join(already_added) + ' already added')
            if len(unknown) > 0:
                result.append(' '.join(unknown) + ' unknown')
            if len(added) > 0:
                result.append(' '.join(added) + ' added')
            await ctx.send('\n'.join(result))

        @reactions.command(name='remove')
        async def remove_reactions(ctx: Union[TextChannel, Member], *, args=None):
            if not args:
                raise UserInputError(message='No reactions')

            not_added = list()
            removed = list()
            for reaction in args.split():
                if not self._config.reactions.__contains__(reaction):
                    not_added.append(reaction)
                else:
                    removed.append(reaction)
                    self._config.reactions.remove(reaction)
            self._config.save(self._config_filepath)

            result = list()
            if len(not_added) > 0:
                result.append(' '.join(not_added) + ' not added')
            if len(removed) > 0:
                result.append(' '.join(removed) + ' removed')
            await ctx.send('\n'.join(result))

        @reactions.command(name='clear')
        async def clear_reactions(ctx: Union[TextChannel, Member]):
            self._config.reactions.clear()
            self._config.save(self._config_filepath)
            await ctx.send('Cleared')

        @reactions.command(name='show')
        async def show_reactions(ctx: Union[TextChannel, Member]):
            if len(self._config.reactions) == 0:
                await ctx.send('No reactions')
            else:
                all_reactions = ' '.join(self._config.reactions)
                for part in split_msg(all_reactions, 512):
                    await ctx.send(f'{part}')
                    await sleep(0.5)

        @reactions.command(name='add-flags')
        async def add_flags_reactions(ctx: Union[TextChannel, Member]):
            for flag in flags:
                if not self._config.reactions.__contains__(flag):
                    self._config.reactions.append(flag)
            self._config.save(self._config_filepath)
            await ctx.send('Success')

        async def is_reaction(ctx: Union[TextChannel, Member], reaction: str) -> bool:
            try:
                while self.is_ws_ratelimited():
                    await sleep(1)
                await ctx.message.add_reaction(reaction)
                await ctx.message.remove_reaction(reaction, self.user)
                await sleep(1)
                return True
            except HTTPException:
                return False

        def split_msg(msg: str, max_length: int):
            while msg:
                yield msg[:max_length]
                msg = msg[max_length:]
