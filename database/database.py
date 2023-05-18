import sqlite3

conn = sqlite3.connect('database/database.db')
cursor = conn.cursor()

# cursor.execute("""CREATE TABLE messages (
#         chat_id integer,
#         vk_id integer,
#         tg_id integer
#     )""")

# cursor.execute("""CREATE TABLE chats (
#         vk_id integer,
#         tg_id integer
#     )""")

def add_message(chat_id: int, vk_id: int, tg_id: int):
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    values = [chat_id, vk_id, tg_id]
    cursor.execute("INSERT INTO messages VALUES (?, ?, ?)", values)
    conn.commit()
    conn.close()

def add_chat(vk_id: int, tg_id: int):
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    values = [vk_id, tg_id]
    cursor.execute("INSERT INTO chats VALUES (?, ?)", values)
    conn.commit()
    conn.close()

def find_chat_tg(vk_chat_id: int) -> int:
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    values = [vk_chat_id]
    cursor.execute("SELECT * FROM chats WHERE vk_id = (?)", values)
    chat = cursor.fetchone()
    conn.commit()
    conn.close()
    if chat:
        return chat[1]
    else:
        return 0

def find_chat_vk(tg_chat_id: int) -> int:
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    values = [tg_chat_id]
    cursor.execute("SELECT * FROM chats WHERE tg_id = (?)", values)
    chat = cursor.fetchone()
    conn.commit()
    conn.close()
    if chat:
        return chat[0]
    else:
        return 0

def find_message_tg(vk_messages_id: int) -> int:
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    values = [vk_messages_id]
    cursor.execute("SELECT * FROM messages WHERE vk_id = (?)", values)
    message = cursor.fetchone()
    conn.commit()
    conn.close()
    if message:
        return message[2]
    else:
        return 0

def find_message_vk(tg_messages_id: int) -> int:
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    values = [tg_messages_id]
    cursor.execute("SELECT * FROM messages WHERE tg_id = (?)", values)
    message = cursor.fetchone()
    conn.commit()
    conn.close()
    if message:
        return message[1]
    else:
        return 0
