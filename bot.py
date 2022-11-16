import io
import json
from asyncio import sleep
from typing import Union
from discord import Reaction, Member, TextChannel, User, Intents, HTTPException
from discord.ext import commands
from discord.ext.commands import Bot, CommandError, UserInputError, CommandNotFound


class Settings:
    def __init__(self):
        self.reactions = list()
        self.channels = list()

    def __str__(self):
        return json.dumps(self, cls=SettingsEncoder, indent=2)

    def save(self, filename: str):
        with io.open(filename, 'w', encoding='utf-8') as file:
            file.write(str(self))

    @staticmethod
    def load(filename: str) -> 'Settings':
        with io.open(filename, 'r', encoding='utf-8') as file:
            json_data = file.read()
            data = Settings()
            data.__dict__ = json.loads(json_data)
            return data


class SettingsEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Settings):
            return o.__dict__
        return json.JSONEncoder.default(self, o)


class ReactionsHelper(Bot):
    data: Settings

    def __init__(self, filename: str, prefix: str, processing_reaction: str):
        intents = Intents.default()
        intents.messages = True
        intents.message_content = True
        super().__init__(command_prefix=prefix, intents=intents)
        self.filename = filename
        self.processing_reaction = processing_reaction
        self.help_command.add_check(commands.has_permissions(manage_messages=True))

    async def on_ready(self):
        print(f'{self.user} ready')

    async def on_command_error(self, ctx, exception: CommandError):
        if isinstance(exception, UserInputError):
            await ctx.send(str(exception))
        elif isinstance(exception, CommandNotFound):
            pass
        else:
            await super().on_command_error(ctx, exception)

    async def on_reaction_add(self, reaction: Reaction, user: Union[Member, User]):
        if self.data.channels.__contains__(reaction.message.channel.id):
            if self.data.reactions.__contains__(str(reaction.emoji)):
                await reaction.message.remove_reaction(reaction, user)

    @staticmethod
    def has_permissions():
        return commands.has_permissions(manage_messages=True)

    async def setup_hook(self):
        try:
            self.data = Settings.load(self.filename)
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = Settings()
        self.data.save(self.filename)

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
            if self.data.channels.__contains__(channel.id):
                raise UserInputError(message=f'{channel.name} already added')

            self.data.channels.append(channel.id)
            self.data.save(self.filename)
            await ctx.send(f'{channel.name} added')

        @channels.command(name='remove')
        async def remove_channel(ctx: Union[TextChannel, Member], *, args=None):
            if not args:
                raise UserInputError(message='No channels')

            channel = await get_channel_by_name(ctx, args)

            if not self.data.channels.__contains__(channel.id):
                raise UserInputError(message=f'{channel.name} not added')

            self.data.channels.remove(channel.id)
            self.data.save(self.filename)
            await ctx.send(f'{channel.name} removed')

        @channels.command(name='clear')
        async def clear_channels(ctx: Union[TextChannel, Member]):
            self.data.channels.clear()
            self.data.save(self.filename)
            await ctx.send('Cleared')

        @channels.command(name='show')
        async def show_channels(ctx: Union[TextChannel, Member]):
            if len(self.data.channels) == 0:
                await ctx.send('No channels')
            else:
                await check_channels(ctx)
                all_channels = ', '.join(ctx.guild.get_channel(i).name for i in self.data.channels)
                await ctx.send(f'Channels: {all_channels}')

        async def get_channel_by_name(ctx, args):
            try:
                return await commands.TextChannelConverter().convert(ctx, args)
            except TypeError:
                raise UserInputError(message=f'Channel {args} not found. Requires string channel name')

        async def check_channels(ctx: Union[TextChannel, Member]):
            checked = list()
            removed = list()
            for channel in self.data.channels:
                if ctx.guild.get_channel(channel):
                    checked.append(channel)
                else:
                    removed.append(channel)

            if len(removed) > 0:
                self.data.channels = checked
                self.data.save(self.filename)

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

            await ctx.message.add_reaction(self.processing_reaction)
            already_added = list()
            unknown = list()
            added = list()
            for reaction in args.split():
                if self.data.reactions.__contains__(reaction):
                    already_added.append(reaction)
                elif not await is_reaction(ctx, reaction):
                    unknown.append(reaction)
                else:
                    added.append(reaction)
                    self.data.reactions.append(reaction)
            self.data.save(self.filename)
            await ctx.message.remove_reaction(self.processing_reaction, self.user)

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
                if not self.data.reactions.__contains__(reaction):
                    not_added.append(reaction)
                else:
                    removed.append(reaction)
                    self.data.reactions.remove(reaction)
            self.data.save(self.filename)

            result = list()
            if len(not_added) > 0:
                result.append(' '.join(not_added) + ' not added')
            if len(removed) > 0:
                result.append(' '.join(removed) + ' removed')
            await ctx.send('\n'.join(result))

        @reactions.command(name='clear')
        async def clear_reactions(ctx: Union[TextChannel, Member]):
            self.data.reactions.clear()
            self.data.save(self.filename)
            await ctx.send('Cleared')

        @reactions.command(name='show')
        async def show_reactions(ctx: Union[TextChannel, Member]):
            if len(self.data.reactions) == 0:
                await ctx.send('No reactions')
            else:
                all_reactions = ' '.join(self.data.reactions)
                for part in split_msg(all_reactions, 512):
                    await ctx.send(f'{part}')
                    await sleep(0.5)

        @reactions.command(name='add-flags')
        async def add_flags_reactions(ctx: Union[TextChannel, Member]):
            with open('flags.json', 'r', encoding='utf-8') as file:
                flags = json.load(file)
                for flag in flags:
                    if not self.data.reactions.__contains__(flag):
                        self.data.reactions.append(flag)
                self.data.save(self.filename)

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
