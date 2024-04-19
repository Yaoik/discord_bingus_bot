from typing import List
import asyncio
from my_token import TOKEN, MY_GUILD, DB_GUILD, SHAPKA, YARICK
import discord
from discord import File, Guild, app_commands
from discord.utils import SequenceProxy
import re
import string
import random
from PIL import Image 
import os, shutil
import time
import logging
from logging.handlers import TimedRotatingFileHandler
import copy
from DiscordDatabase import DiscordDatabase
from DiscordDatabase.DiscordDatabase import Database
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Создание TimedRotatingFileHandler
handler = TimedRotatingFileHandler(filename='logs\\pars_py_log.log', when='midnight', interval=1, backupCount=30, encoding='utf-8')
handler.setLevel(logging.INFO)

# Создание форматтера
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)

# Добавление обработчика к логгеру
logger.addHandler(handler)

# Добавление потокового обработчика для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(console_handler)



class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)
        self.database: None|Database = None
        #assert isinstance(self.guild, Guild)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        self.guild = await self.fetch_guild(MY_GUILD)
        self.tree.copy_global_to(guild=self.guild)
        await self.tree.sync(guild=self.guild)



intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)

#my_guilds = SequenceProxy([discord.Object(id=guild.id) for guild in client.guilds])

async def delete_files():
    path = 'media/pictures'
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
            

db = DiscordDatabase(client, DB_GUILD)
@client.event
async def on_ready():
    #await tree.sync(guild=discord.Object(478560120138366997))
    print("Ready!")
    await delete_files()
    global SHAPKA, YARICK
    SHAPKA = await client.fetch_user(SHAPKA)
    YARICK = await client.fetch_user(YARICK)
    assert SHAPKA is not None
    assert YARICK is not None
    print(f'{SHAPKA=}')
    print(f'{YARICK=}')
    client.database = await db.new("GIFS","backup")
    #await client.database.set("name","Ankush")
    #name = await client.database.get("name")
    #print(name)

@client.event
async def on_message(message:discord.message.Message):
    if message.author == client.user:
        return

    if message.content.startswith('!to_gif'):
        #reference = message.reference
        #print(reference)
        
        for at in message.attachments:
            apttern_before = r'^(.*)\.'
            apttern_after = r'\.([^\.]+)$'
            before = re.search(apttern_before, at.filename)
            after = re.search(apttern_after, at.filename)
            if after is not None:
                if after.group().lower() in ['.png', '.jpg', '.bmp', '.gif']:
                    file = await at.to_file(filename=''.join(random.choices(string.ascii_letters+string.digits, k=16))+'.gif')
                    name = str(time.time()) + ''.join(random.choices(string.ascii_letters+string.digits, k=16))
                    path = f'media\\pictures\\{name}.png'
                    img = Image.open(file.fp)
                    img.save(path) # .resize((300,300))
                    file = File(path, filename='test.gif')
                    await message.channel.send(file=file)
                    os.remove(path)
            
        if message.attachments == []:
            await message.channel.send('Hello!')

@client.tree.context_menu(name='Show Join Date')
async def show_join_date(interaction: discord.Interaction, member: discord.Member):
    # The format_dt function formats the date time into a human readable representation in the official client
    joined_at = member.joined_at
    assert joined_at is not None
    await interaction.response.send_message(f'{member} joined at {discord.utils.format_dt(joined_at)}')

@client.tree.context_menu(name='to_gif')
async def context_menu_to_gif(interaction: discord.Interaction, message: discord.Message):
    #logging.info(f'context_menu_to_gif {message.attachments=}')
    #logging.info(f'context_menu_to_gif {message.application=}')
    #logging.info(f'context_menu_to_gif {message.components=}')
    #logging.info(f'context_menu_to_gif {message.stickers=}')
    #logging.info(f'context_menu_to_gif {message.content=}')
    if len(message.attachments) > 0:
        files = await to_gif(interaction, message.attachments)
        if len(files)>0:
            await interaction.response.send_message(files=files, ephemeral=False)
        else:
            await interaction.response.send_message('Не найдено изображений', ephemeral=True)
    else:
        
        await interaction.response.send_message('Не найдено изображений', ephemeral=True)


@client.tree.command(name='to_gif', description="clear the number of messages you want.")
@app_commands.rename(attachment='картинка')
@app_commands.describe(categorie='Категория для поиска')
async def command_to_gif(interaction: discord.Interaction, attachment: discord.Attachment, categorie:str|None=None, *, private:bool=False):
    files = await to_gif(interaction, [attachment], categorie=categorie, private=private)
    if len(files)>0:
        await interaction.response.send_message(files=files, ephemeral=False)
    else:
        await interaction.response.send_message('Не найдено изображений', ephemeral=True)
    #await interaction.response.send_message(f'Modify {categories=} {private=}', ephemeral=True)

async def to_gif(interaction: discord.Interaction, attachments: list[discord.Attachment], *, categorie:str|None=None, gif_name:str|None=None, private:bool=False):
    files = []
    for at in attachments:
        logging.info(f'{at=}')
        pttern_before = r'^(.*)\.'
        pttern_after = r'\.([^\.]+)$'
        before = re.search(pttern_before, at.filename)
        after = re.search(pttern_after, at.filename)
        if after is not None:
            if after.group().lower() in ['.png', '.jpg', '.bmp', '.gif']:
                file = await at.to_file()
                name = str(time.time()) + ''.join(random.choices(string.ascii_letters+string.digits, k=16))
                path = f'media\\pictures\\{name}.png'
                img = Image.open(file.fp)
                img.save(path) # .resize((300,300))
                file = File(path, filename=f'{before}gif')
                #await message.channel.send(file=file)
                files.append(file)
                if categorie:
                    if not private:
                        msg_yarick = await YARICK.send(categorie, file=file) # type:ignore
                        msg_shapka = await SHAPKA.send(categorie, file=file) # type:ignore
                        assert msg_shapka is not None
                        assert msg_yarick is not None
                        gifs = await client.database.get(categorie) # type:ignore
                        if gif_name:
                            gif = {gif_name:[msg_yarick.id, msg_shapka.id]}
                        else:
                            gif_name = str(time.time()) + ''.join(random.choices(string.ascii_letters+string.digits, k=16))
                            gif = {gif_name:[msg_yarick.id, msg_shapka.id]}
                            
                        if isinstance(gifs, list):
                            gifs.append(gif)
                            gifs_new = await client.database.set(categorie, gifs)
                        elif gifs is None:
                            gifs_new = await client.database.set(categorie, [gif])
                #await interaction.response.send_message(file=file, ephemeral=False)
    return files


@client.tree.command(name='frrrr', description="hehehehe.")
async def fruits(interaction: discord.Interaction, fruit: str):
    await interaction.response.send_message(f'Your favourite fruit seems to be {fruit}')

@fruits.autocomplete('fruit')
async def fruits_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    fruits = ['Banana', 'Pineapple', 'Apple', 'Watermelon', 'Melon', 'Cherry']
    return [
        app_commands.Choice(name=fruit, value=fruit)
        for fruit in fruits if current.lower() in fruit.lower()
    ]
    
    
client.run(TOKEN)