import disnake
from disnake.ext import commands, tasks
from disnake.ui import Button, View
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
import asyncio
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import json
import pytz
import aiohttp
from datetime import datetime, timedelta
import os
import atexit

intents = disnake.Intents.default()
intents.messages = True 
intents.members = True 
intents.reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

discord_token = "MTI4Mjc2OTg2MTEwOTYxMjY3NQ.GfNH3F.cGRnx8mR4_RGS55BmYjwEFctBve33e_tPjFD8Y"

TWITCH_CLIENT_ID = "enspq6jfwy8e2dezkb5gc52plepju6"
TWITCH_CLIENT_SECRET = "r4eookccno8wra0d02bpz89i3k8iob"

last_up_bump_time = None

role_mappings = {
    "✅": "member"
}

stream_notified = {}

channel_id_verify = 1282779009461125153
message_id_verify = 1282781826779316235

channel_id_hello = 1282739459116503136
channel_id_bye = 1282756090265731203

#original
channel_id_stream = 1282751663534247977
ping_id_stream = 1282758184091648120
channel_id_clips = 1282751793876701275

#dev
# channel_id_stream = 1282807436830314517
# ping_id_stream = 1282758184091648120
# channel_id_clips = 1282807436830314517

bot.remove_command('help')

statuses = [
    "!help",
    "Twitch",
    "на Не придумал сори",
    "на маято",
    "на говнято",
    "на мнеленя"
]

status_index = 0

@tasks.loop(minutes=2)
async def change_status():
    global status_index
    status = statuses[status_index]
    await bot.change_presence(activity=disnake.Activity(type=disnake.ActivityType.watching, name=status))
    status_index = (status_index + 1) % len(statuses)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    
    # Получаем канал для отправки сообщения
    channel_id = 1282756369564569690  # Замените на ID вашего канала
    channel = bot.get_channel(channel_id)
    
    if channel:
        message = "Бот успешно запущен и готов к работе! 🎉"
        await channel.send(message)
        print(f'Сообщение о запуске отправлено в канал {channel.name}.')
    else:
        print(f'Не удалось найти канал с ID {channel_id}.')

    change_status.start()


emoji_to_add_verify = "✅"

@bot.command(name='verify')
async def verify(ctx):

    if verify:  # Убедитесь, что роль верификации существует
        embed = disnake.Embed(
            title="Верификация",
            description="Нажмите на реакцию с галочкой ниже, чтобы пройти верификацию и получить доступ к серверу.",
            color=0x00FF00  # Зеленый цвет
        )
        
        channel = bot.get_channel(channel_id_verify)  # Канал для верификации
        embed.set_image(url="https://i.pinimg.com/originals/d1/0d/10/d10d100c2e993cdc669d6960c3802e4d.jpg")
        
        if channel:
            message = await channel.send(embed=embed)
            await message.add_reaction(emoji_to_add_verify)
        else:
            print(f"Channel with ID {channel_id_verify} not found.")
    else:
        await ctx.send(f"Role '{verify}' not found.")


@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id == channel_id_verify and payload.message_id == message_id_verify:
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)

        if member:
            role_name = role_mappings.get(payload.emoji.name)
            if role_name:
                role = disnake.utils.get(guild.roles, name=role_name)

                if role:
                    try:
                        await member.add_roles(role)
                        print(f"Выдана роль {role_name} пользователю {member.mention}")
                    except disnake.errors.Forbidden:
                        print(f"Недостаточно прав для выдачи роли {role_name} пользователю {member.mention}")
                else:
                    print(f"Роль {role_name} не найдена")


@bot.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id == channel_id_verify and payload.message_id == message_id_verify:
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)

        if member:
            role_name = role_mappings.get(payload.emoji.name)
            if role_name:
                role = disnake.utils.get(guild.roles, name=role_name)

                if role:
                    try:
                        await member.remove_roles(role)
                        print(f"Удалена роль {role_name} у пользователя {member.mention}")
                    except disnake.errors.Forbidden:
                        print(f"Недостаточно прав для удаления роли {role_name} у пользователя {member.mention}")
                else:
                    print(f"Роль {role_name} не найдена")


#join people to server
@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(channel_id_hello)
    
    if channel:
        embed = disnake.Embed(
            description=(f"Привет, {member.mention}! Рады видеть тебя здесь.\n"
                        "Для того чтобы получить полный доступ к серверу, пройди верификацию в <#1282779009461125153>."),
            color=disnake.Color.green()
        )
        embed.set_image(url="https://c.tenor.com/vNapCUP0d3oAAAAC/tenor.gif")
        await channel.send(embed=embed)

#leave people from server
@bot.event
async def on_member_remove(member):
    channel = member.guild.get_channel(channel_id_bye)
    
    if channel:
        embed = disnake.Embed(
            description=f"Прощай, {member.mention}. Мы будем скучать по тебе.",
            color=disnake.Color.red()
        )
        embed.set_image(url="https://c.tenor.com/4E1q900bMwgAAAAC/tenor.gif")  # Замените на URL вашей гифки
        await channel.send(embed=embed)


@bot.command(name='send')
async def send(ctx, channel_id: int, *, message: str):
    # Проверка наличия роли
    role = disnake.utils.get(ctx.guild.roles, name='stuff')
    if role not in ctx.author.roles:
        await ctx.send(f"У вас нет роли `{role.name}`, чтобы использовать эту команду.")
        return

    # Получаем канал по ID
    channel = bot.get_channel(channel_id)
    
    # Если канал найден, отправляем сообщение
    if channel:
        await channel.send(message)
        await ctx.send(f"Сообщение отправлено в канал {channel.mention}.")
    else:
        await ctx.send(f"Канал с ID {channel_id} не найден.")

stream_notified = {}

# Function to load streamers configuration from file or database
def load_streamers():
    with open('streamers.json', 'r') as file:
        streamers_config = json.load(file)
    return streamers_config

# Function to save streamers configuration to file or database
def save_streamers(streamers_config):
    with open('streamers.json', 'w') as file:
        json.dump(streamers_config, file, indent=4)

# Function to get Twitch access token
def get_twitch_token():
    url = 'https://id.twitch.tv/oauth2/token'
    params = {
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, params=params)
    return response.json().get('access_token')

# Function to check if the user is live on Twitch
def is_user_live(username, access_token):
    url = f'https://api.twitch.tv/helix/streams?user_login={username}'
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    data = response.json().get('data')
    return len(data) > 0

async def get_stream_title(username, access_token):
    url = f"https://api.twitch.tv/helix/streams?user_login={username}"
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    data = response.json().get('data')
    if data:
        return data[0]['title']
    else:
        return "Нет доступного названия"

async def get_streamer_avatar(username, access_token):
    url = f"https://api.twitch.tv/helix/users?login={username}"
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    data = response.json().get('data')
    if data:
        return data[0]['profile_image_url']
    else:
        return "https://static.twitchcdn.net/assets/favicon-32-e29e246c157142c94346.png"  # Замените на URL изображения по умолчанию

# Функция для получения роли по названию
def get_role_by_name(guild, role_name):
    return disnake.utils.get(guild.roles, name=role_name)

# Функция для уведомления о стриме
async def notify_stream():
    access_token = get_twitch_token()
    streamers_config = load_streamers()

    special_streamer_username = "twogirlswatching"
    special_users = [
        {"discord_id": "828993106421874758"}, 
        {"discord_id": "852865584952508447"}  
    ]

    currently_live = {}

    for streamer in streamers_config['streamers']:
        username = streamer['username']
        twitch_link = f"https://www.twitch.tv/{username}"

        if is_user_live(username, access_token):
            if not stream_notified.get(username, False):
                try:
                    title = await get_stream_title(username, access_token)
                    game_name = await get_stream_game(username, access_token)
                    viewer_count = await get_viewer_count(username, access_token)
                    avatar_url = await get_streamer_avatar(username, access_token)

                    formatted_title = f"[{title}]({twitch_link})"
                    embed = disnake.Embed(
                        title=title,
                        color=disnake.Color.purple()
                    )
                    embed.set_author(name=username, icon_url=avatar_url)
                    embed.add_field(name="Игра", value=game_name, inline=True)
                    embed.add_field(name="Зрители", value=viewer_count, inline=True)
                    embed.set_image(url=f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{username}-1920x1080.jpg")

                    button = disnake.ui.Button(style=disnake.ButtonStyle.link, label="Перейти на стрим", url=twitch_link)
                    view = disnake.ui.View()
                    view.add_item(button)

                    channel = bot.get_channel(channel_id_stream)
                    if channel:
                        content = f"<@&{ping_id_stream}> {formatted_title}"
                        await channel.send(content=content, embed=embed, view=view)
                        stream_notified[username] = True
                        
                    guild = bot.get_guild(1282739459116503132)  # Замените на ID вашего сервера
                    role = get_role_by_name(guild, "стримит")
                    if role:
                        if username == special_streamer_username:
                            # Если стримит "twogirlswatching", выдаем роль двум определенным пользователям
                            for user in special_users:
                                member = guild.get_member(int(user["discord_id"]))
                                if member:
                                    await member.add_roles(role)
                                    print(f"Выдана роль 'стримит' пользователю {member.mention}")
                        else:
                            # Стандартная логика для выдачи роли стримеру
                            for member in guild.members:
                                if str(member.id) == streamer['discord_id']:  # Проверяем ID участника
                                    await member.add_roles(role)
                                    print(f"Выдана роль 'стримит' пользователю {member.mention}")

                except Exception as e:
                    print(f"Ошибка при уведомлении о стриме для {username}: {e}")
            
            # Обновляем текущее состояние стримеров
            currently_live[username] = True

        else:
            if stream_notified.get(username, False):
                # Стример был в сети, но теперь оффлайн
                try:
                    guild = bot.get_guild(1282739459116503132)  # Замените на ID вашего сервера
                    role = get_role_by_name(guild, "стримит")
                    if role:
                        if username == special_streamer_username:
                            # Снимаем роль с определенных пользователей, если стрим оффлайн
                            for user in special_users:
                                member = guild.get_member(int(user["discord_id"]))
                                if member:
                                    await member.remove_roles(role)
                                    print(f"Роль 'стримит' снята с пользователя {member.mention}")
                        else:
                            # Стандартная логика снятия роли
                            for member in guild.members:
                                if str(member.id) == streamer['discord_id']:  # Проверяем ID участника
                                    await member.remove_roles(role)
                                    print(f"Роль 'стримит' снята с пользователя {member.mention}")
                                
                    stream_notified[username] = False

                except Exception as e:
                    print(f"Ошибка при снятии роли 'стримит' для {username}: {e}")

            # Обновляем текущее состояние стримеров
            currently_live[username] = False

        await asyncio.sleep(1)

# Дополнительные функции для получения данных о стриме
async def get_stream_game(username, access_token):
    url = f"https://api.twitch.tv/helix/streams?user_login={username}"
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    data = response.json().get('data')
    if data:
        return data[0]['game_name']
    else:
        return "Unknown Game"

async def get_viewer_count(username, access_token):
    url = f"https://api.twitch.tv/helix/streams?user_login={username}"
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    data = response.json().get('data')
    if data:
        return data[0]['viewer_count']
    else:
        return "0"

# Check if the user has the required role
def has_role(role_name):
    async def predicate(ctx):
        role = disnake.utils.get(ctx.guild.roles, name=role_name)
        return role in ctx.author.roles
    return commands.check(predicate)

# Command to add a new streamer
@bot.command(name='add_streamer')
@has_role('stuff')
async def add_streamer(ctx, discord_id: int, twitch_username: str):
    # Проверка наличия роли
    role = disnake.utils.get(ctx.guild.roles, name='stuff')
    if role not in ctx.author.roles:
        await ctx.send("у вас недостаточно прав для выполнения этой команды.")
        return

    # Загрузка текущих стримеров
    streamers_config = load_streamers()

    # Проверка, существует ли уже стример с таким именем на Twitch
    if any(streamer['username'] == twitch_username for streamer in streamers_config['streamers']):
        await ctx.send(f"Стример с именем {twitch_username} уже есть в списке.")
        return

    # Поиск участника по ID Discord
    member = ctx.guild.get_member(discord_id)
    if not member:
        await ctx.send(f"Пользователь с ID {discord_id} не найден на сервере.")
        return

    # Добавление нового стримера в конфигурацию
    new_streamer = {
        "discord_id": str(discord_id),
        "username": twitch_username
    }
    streamers_config['streamers'].append(new_streamer)

    # Сохранение обновленной конфигурации
    save_streamers(streamers_config)

    # Инициализация флага уведомления для нового стримера
    stream_notified[twitch_username] = False

    await ctx.send(f"Стример {twitch_username} добавлен в список.")

@bot.command(name='remove_streamer')
@has_role('stuff')
async def remove_streamer(ctx, discord_id: int):
    # Проверка наличия роли
    role = disnake.utils.get(ctx.guild.roles, name='stuff')
    if role not in ctx.author.roles:
        await ctx.send("у вас недостаточно прав для выполнения этой команды.")
        return

    # Загрузка текущих стримеров
    streamers_config = load_streamers()

    # Поиск и удаление стримера
    streamer_to_remove = next((streamer for streamer in streamers_config['streamers'] if streamer['discord_id'] == str(discord_id)), None)

    if not streamer_to_remove:
        await ctx.send(f"Стример с ID {discord_id} не найден в списке.")
        return

    # Удаление стримера из конфигурации
    streamers_config['streamers'].remove(streamer_to_remove)

    # Сохранение обновленной конфигурации
    save_streamers(streamers_config)

    # Сброс флага уведомления для удаленного стримера
    twitch_username = streamer_to_remove['username']
    stream_notified.pop(twitch_username, None)

    await ctx.send(f"Стример {twitch_username} удален из списка.")


# Функция для получения времени последней проверки и текущего времени
def get_time_window():
    now = datetime.utcnow()  # Текущее время
    last_check_time = now - timedelta(minutes=10)  # Проверяем за последние 10 минут
    return last_check_time.isoformat() + 'Z', now.isoformat() + 'Z'

async def get_recent_clips(broadcaster_id, access_token, started_at, ended_at, username):
    url = (
        f'https://api.twitch.tv/helix/clips?broadcaster_id={broadcaster_id}'
        f'&first=100&started_at={started_at}&ended_at={ended_at}'
    )
    
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            clips = data.get('data', [])
    
    print(f"Получено клипов для {username} ({broadcaster_id}): {len(clips)}")  # Отладочное сообщение
    return clips



# Функция для получения ID стримера
async def get_broadcaster_id(username, access_token):
    url = f'https://api.twitch.tv/helix/users?login={username}'
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            data = data.get('data', [])
            if data:
                return data[0]['id']
    return None

async def check_new_clips():
    access_token = get_twitch_token()
    streamers_config = load_streamers()

    while True:  # Бесконечный цикл для регулярной проверки всех стримеров
        # Обходим всех стримеров из списка
        for streamer in streamers_config['streamers']:
            username = streamer['username']
            broadcaster_id = await get_broadcaster_id(username, access_token)
            avatar_url = await get_streamer_avatar(username, access_token)

            if broadcaster_id:
                # Обновляем временной диапазон перед каждой проверкой
                started_at, ended_at = get_time_window()
                
                try:
                    # Получаем клипы для каждого стримера
                    recent_clips = await get_recent_clips(broadcaster_id, access_token, started_at, ended_at, username)

                    for clip in recent_clips:
                        clip_id = clip['id']
                        if clip_id not in stream_notified:
                            title = clip['title']
                            url = clip['url']
                            thumbnail_url = clip['thumbnail_url']

                            # Создаем embed с информацией о клипе
                            embed = disnake.Embed(
                                title=f"{title}",
                                color=disnake.Color.purple(),
                            )
                            embed.set_image(url=thumbnail_url)  # Увеличиваем изображение
                            embed.set_author(name=username, icon_url=avatar_url)

                            # Создание кнопки с ссылкой на клип
                            button = disnake.ui.Button(style=disnake.ButtonStyle.link, label="Смотреть клип", url=url)
                            view = disnake.ui.View()
                            view.add_item(button)

                            # Указываем ID роли для пинга
                            role_mention = f"<@&{ping_id_stream}>"  # Формат для упоминания роли через ID

                            # Отправляем сообщение в указанный канал с пингом роли
                            channel = bot.get_channel(channel_id_clips)
                            if channel:
                                content = f"{role_mention} Новый клип от {username}!"
                                await channel.send(content=content, embed=embed, view=view)
                                
                            stream_notified[clip_id] = True  # Запоминаем, что клип был уведомлен

                except Exception as e:
                    print(f"Ошибка при получении новых клипов для {username}: {e}")
            
            await asyncio.sleep(1)  # Небольшая пауза между запросами к API для каждого стримера

        # Делаем паузу на 5 минут перед следующей проверкой
        await asyncio.sleep(60)

# Запуск планировщика
scheduler = AsyncIOScheduler()
scheduler.add_job(check_new_clips, 'interval', seconds=15, max_instances=1)
scheduler.add_job(notify_stream, 'interval', seconds=5, max_instances=3)

scheduler.start()

def format_date(date_str):
    # Определяем маппинг месяцев на русском языке
    months = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
        7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }

    # Преобразуем строку даты в объект datetime
    created_at_datetime = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    
    # Форматируем дату
    day = created_at_datetime.day
    month = created_at_datetime.month
    year = created_at_datetime.year
    formatted_date = f"{day} {months[month]} {year} года"

    return formatted_date

@bot.command(name='stats')
async def stats(ctx, username: str):
    access_token = get_twitch_token()  # Уберите await здесь
    
    # Получение информации о пользователе
    user_info = await get_user_info(username, access_token)
    
    if user_info:
        user_id = user_info['id']
        avatar_url = user_info['profile_image_url']
        description = user_info['description']
        created_at = user_info['created_at']  # Дата создания аккаунта

        # Форматируем дату
        formatted_date = format_date(created_at)

        # Получение количества фолловеров
        followers_count = await get_followers_count(user_id, access_token)

        # Информация о подписке (недоступна через API)
        subscribers_count = "Недоступно через публичный API"

        # Создаем embed с информацией
        embed = disnake.Embed(
            title=f"Статистика для {username}",
            color=disnake.Color.blue()
        )
        embed.set_thumbnail(url=avatar_url)  # Устанавливаем аватарку пользователя
        embed.add_field(name="Фолловеры", value=followers_count, inline=True)
        embed.add_field(name="Дата создания аккаунта", value=formatted_date, inline=True)
        embed.add_field(name="Описание", value=description or "Нет описания", inline=False)
        embed.set_author(name=username, icon_url=avatar_url)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"Пользователь {username} не найден на Twitch.")

# Функция для получения информации о пользователе (аватар, описание и id)
async def get_user_info(username, access_token):
    url = f"https://api.twitch.tv/helix/users?login={username}"
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            if data['data']:
                return data['data'][0]
            return None

# Функция для получения количества фолловеров канала
async def get_followers_count(broadcaster_id, access_token):
    url = f"https://api.twitch.tv/helix/channels/followers?broadcaster_id={broadcaster_id}"
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            return data.get('total', 0)
        
@bot.command(name='streamers')
async def streamers(ctx):
    # Load current streamers
    streamers_config = load_streamers()
    
    # Create embed
    embed = disnake.Embed(title="Список стримеров", color=disnake.Color.purple())
    
    # Add each streamer to the embed
    for streamer in streamers_config['streamers']:
        discord_id = streamer['discord_id']
        username = streamer['username']
        discord_user = bot.get_user(int(discord_id))
        if discord_user:
            embed.add_field(name=f"Discord: {discord_user.name}", value=f"Twitch: {username}", inline=False)
    
    # Add a footer with the number of streamers and a thank you message
    num_streamers = len(streamers_config['streamers'])
    embed.set_footer(text=f"Всего стримеров: {num_streamers} | Спасибо, что вы с нами ❤️")
    
    # Send embed
    await ctx.send(embed=embed)

@bot.command(name='set_name')
@has_role('stuff')
async def set_bot_name(ctx, *, new_name: str):
    try:
        await bot.user.edit(username=new_name)
        await ctx.send(f"Имя бота изменено на `{new_name}`.")
    except Exception as e:
        await ctx.send(f"Произошла ошибка при изменении имени бота: {e}")

@bot.command(name='set_avatar')
@has_role('stuff')
async def set_bot_avatar(ctx, url: str = None):
    if url is None:
        if not ctx.message.attachments:
            await ctx.send("Пожалуйста, прикрепите изображение для установки в качестве аватарки.")
            return

        # Получение первого вложенного файла
        attachment = ctx.message.attachments[0]
        try:
            # Загрузка изображения
            image = await attachment.read()
            # Изменение аватарки
            await bot.user.edit(avatar=image)
            await ctx.send("Аватарка бота успешно изменена.")
        except Exception as e:
            await ctx.send(f"Произошла ошибка при изменении аватарки бота: {e}")

    else:
        # Если URL предоставлен, скачиваем изображение с этого URL
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        image = await response.read()
                        # Изменение аватарки
                        await bot.user.edit(avatar=image)
                        await ctx.send("Аватарка бота успешно изменена.")
                    else:
                        await ctx.send(f"Не удалось загрузить изображение с URL: {url}")
        except Exception as e:
            await ctx.send(f"Произошла ошибка при изменении аватарки бота: {e}")


@bot.command(name='help')
async def help_command(ctx):
    embed = disnake.Embed(
        title="Помощь по командам бота",
        description="Список доступных команд:",
        color=0xF5B1CC
    )
    embed.add_field(
        name="!stats <twitch_username>",
        value="Отображает статистику стримера.",
        inline=False
    )
    embed.add_field(
        name="!streamers",
        value="Отображает список всех стримеров.",
        inline=False
    )
    embed.add_field(
        name="!help",
        value="Отображает это сообщение справки.",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name='help_admin')
@has_role('stuff')
async def help_command(ctx):
    # Проверка наличия роли (может быть необязательна, если используется has_role)
    role = disnake.utils.get(ctx.guild.roles, name='stuff')
    if role not in ctx.author.roles:
        await ctx.send(f"У вас нет роли `{role.name}`, чтобы использовать эту команду.")
        return

    # Создание embed-сообщения
    embed = disnake.Embed(
        title="Помощь по командам бота",
        description="Список команд:",
        color=0x9B59B6  # Фиолетовый цвет
    )
    embed.add_field(
        name="!add_streamer <discord_id> <twitch_username>",
        value="Добавляет нового стримера в список для уведомлений.",
        inline=False
    )
    embed.add_field(
        name="!remove_streamer <discord_id> <twitch_username>",
        value="Удаляет стримера из списка уведомлений.",
        inline=False
    )
    embed.add_field(
        name="!stats <twitch_username>",
        value="Отображает статистику стримера.",
        inline=False
    )
    embed.add_field(
        name="!streamers",
        value="Отображает список всех стримеров.",
        inline=False
    )
    embed.add_field(
        name="!send <id_channel>",
        value="Отправляет сообщение в указаный канал.",
        inline=False
    )
    embed.add_field(
        name="!set_name <new_name>",
        value="Изменяет имя бота.",
        inline=False
    )
    embed.add_field(
        name="!set_avatar <url>",
        value="Изменяет аватарку бота по url либо прикрепленному изображению.",
        inline=False
    )
    embed.add_field(
        name="!help",
        value="Справка для пользователей.",
        inline=False
    )
    embed.add_field(
        name="!help_admin",
        value="Справка для администраторов.",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('У вас недостаточно прав для использования этой команды.')
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send('Команда не найдена.')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Необходимые аргументы отсутствуют.')
    elif isinstance(error, commands.BadArgument):
        await ctx.send('Проверьте аргументы команды.')
    else:
        await ctx.send(f'Произошла ошибка при выполнении команды: {error}')
bot.run(discord_token)

