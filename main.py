from vkbottle.user import Message, User
import requests
from random import randint
from vkbottle.dispatch.rules.base import ChatActionRule
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode
from telethon import functions
from telethon.types import DialogFilter, DialogFilterDefault, InputPeerChat
from telethon.sync import TelegramClient
from database.database import add_chat, add_message, find_chat_tg, find_chat_vk, find_message_tg, find_message_vk
from personaldata import api_hash, api_id, bot_url, tg_bot_token, vk_login, vk_password, vk_token

bot = Bot(token=tg_bot_token, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot)

vk = User(vk_token)


# Получить имя пользователя
async def user_name(user_id: int) -> str:
    user = await vk.api.users.get(user_id=user_id)
    return f"{user[0].first_name} {user[0].last_name}"


# Получить название беседы
async def chat_title(chat_id: int) -> str:
    chat = await vk.api.messages.get_conversations_by_id(peer_ids=chat_id)
    return chat.items[0].chat_settings.title


# Получить id чата в который нужно отпавить сообщение
async def tg_chat_id(peer_id: int, from_chat: bool) -> int:
    chat = find_chat_tg(peer_id)
    if chat:
        return chat
    else:
        if from_chat:
            title = await chat_title(peer_id)
            photo = await get_chat_photo_url(peer_id)
        else:
            title = await user_name(peer_id)
            photo = await get_user_photo_url(peer_id)

        async with TelegramClient('telethon_application', api_id, api_hash) as client:
            created_chat = await client(
                functions.messages.CreateChatRequest(
                    users=[bot_url],
                    title=title
                )
            )

            await client(
                functions.messages.EditChatPhotoRequest(
                    chat_id=created_chat.chats[0].id,
                    photo=await client.upload_file(requests.get(photo).content)
                )
            )

        id = created_chat.chats[0].id

        await add_chat_to_folder(id)

        add_chat(peer_id, -id)
        return -id


async def add_chat_to_folder(id: int):
    async with TelegramClient('telethon_application', api_id, api_hash) as client:
        folders = await client(functions.messages.GetDialogFiltersRequest())

        for folder in folders:
            if folder != DialogFilterDefault() and folder.title == 'VK':

                chats = folder.include_peers
                chats.append(InputPeerChat(id))
                
                await client(
                    functions.messages.UpdateDialogFilterRequest(
                        id=folder.id,
                        filter=DialogFilter(
                            id=folder.id,
                            title=folder.title,
                            pinned_peers=folder.pinned_peers,
                            include_peers=chats,
                            exclude_peers=folder.exclude_peers,
                            contacts=folder.contacts,
                            non_contacts=folder.non_contacts,
                            groups=folder.groups,
                            broadcasts=folder.broadcasts,
                            bots=folder.bots,
                            exclude_muted=folder.exclude_muted,
                            exclude_read=folder.exclude_read,
                            exclude_archived=folder.exclude_archived,
                            emoticon=folder.emoticon
                        )
                    )
                )


# Личное сообщение или из чата
def from_chat(message: Message) -> bool:
    if message.chat_id < 0:
        return False
    else:
        return True


# Получить id сообщения на которое отвечают в VK
# Прописывать в каждой отправке сообщения из тг (если нет ответа то просто выведет 0 и ничего не перешлется)
async def get_reply_message(message: Message) -> int:
    try:
        replied_id = message.reply_message.id
        return find_message_tg(replied_id)
    except Exception:
        return 0


# получить ссылку на фото чата
async def get_chat_photo_url(chat_id: int) -> str:
    request = await vk.api.messages.get_conversations_by_id(
        peer_ids=chat_id
    )

    try:
        url = request.items[0].chat_settings.photo.photo_200
    except Exception:
        url = 'https://cdn-icons-png.flaticon.com/512/1370/1370907.png'

    return url


# получить ссылку на аватарку пользователя
async def get_user_photo_url(user_id: int) -> str:
    request = await vk.api.users.get(user_ids=user_id, fields='photo_400_orig')
    return request[0].photo_400_orig


# найти фото максимально размера
def max_size(sizes: list) -> str:
    maxx = [0, 0]
    for size in sizes:
        if size.height > maxx[1]:
            maxx = [size, size.height]
    return maxx[0].url


# Изменение фотографии беседы
@vk.on.chat_message(ChatActionRule('chat_photo_update'))
async def change_chat_photo(message: Message):
    url = max_size(message.attachments[0].photo.sizes)

    chat_id = await tg_chat_id(message.peer_id, 1)

    async with TelegramClient('telethon_application', api_id, api_hash) as client:
        await client(
            functions.messages.EditChatPhotoRequest(
                chat_id=-chat_id,
                photo=await client.upload_file(requests.get(url).content)
            )
        )

    await bot.send_message(
        chat_id=chat_id,
        text=f'--- {await user_name(message.from_id)} изменил(а) фотографию чата ---'
    )


@vk.on.chat_message(ChatActionRule('chat_title_update'))
async def chat_rename(message: Message):
    chat_id = await tg_chat_id(message.peer_id, 1)

    request = await bot.get_chat(chat_id=chat_id)
    prev = request.title
    new = message.action.text

    async with TelegramClient('telethon_application', api_id, api_hash) as client:
        await client(
            functions.messages.EditChatTitleRequest(
                chat_id=-chat_id,
                title=new
            )
        )

    await bot.send_message(
        chat_id=chat_id,
        text=f'--- {await user_name(message.from_id)} изменил(а) название чата с {prev} на {new} ---'
    )


@dp.message_handler()
async def message_sending(message: types.Message):
    # peer_id = find_chat_vk(message.chat.id)
    # vk.messages.send(peer_id=peer_id, message=message, random_id=randint(-2147483647, 2147483647))
    # await bot.send_message(chat_id=message.chat.id, text=message)
    try:
        peer_id = find_chat_vk(message.chat.id)
        reply_to = find_message_vk(message.reply_to_message.message_id)
        await vk.api.messages.send(
            peer_id=peer_id,
            message=message.text,
            random_id=randint(-2147483647, 2147483647),
            reply_to=reply_to
        )
    except Exception:
        peer_id = find_chat_vk(message.chat.id)
        await vk.api.messages.send(
            peer_id=peer_id,
            message=message.text,
            random_id=randint(-2147483647, 2147483647)
        )


@vk.on.message()
async def polling(message: Message):
    in_chat = from_chat(message)
    id = await tg_chat_id(message.peer_id, in_chat)

    if in_chat:
        text = f'{await user_name(message.from_id)}\n{message.text}'
    else:
        text = f'{message.text}'

    msg_tg = await bot.send_message(
        chat_id=id,
        text=text,
        reply_to_message_id=await get_reply_message(message)
        )
    
    add_message(id, message.id, msg_tg['message_id'])


if __name__ == '__main__':
    vk_async = asyncio.ensure_future(dp.start_polling())
    tg_async = asyncio.ensure_future(vk.run_polling())
    loop = asyncio.get_event_loop()
    loop.run_forever()
