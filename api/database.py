import sqlite3
from .config import cipher_suite

# Initialize the SQLite database
def init_db(name):
    conn = sqlite3.connect(f"./databases/{name}.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, message TEXT, date TEXT, colour TEXT)''')
    conn.commit()
    conn.close()

def create_table_accounts():
    conn = sqlite3.connect('./databases/users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      username TEXT NOT NULL UNIQUE, 
                      password TEXT NOT NULL,
                      agreement TEXT NOT NULL,
                      UUID TEXT NOT NULL)''')
    conn.commit()
    conn.close()
 
create_table_accounts()

# Function to get all messages from the database
def get_messages(name):
    conn = None
    try:
        conn = sqlite3.connect(f"./databases/{name}.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, message, date, colour FROM messages ORDER BY id ASC")
        messages = cursor.fetchall()
        conn.close()
    finally:
        if conn:
            conn.close()
    return messages

# Function to add a new message to the database
def add_message(username, message, date, colour, room=False):
    print("Ran code")
    message = str.encode(message)
    username = str.encode(username)
    message = cipher_suite.encrypt(message)
    username = cipher_suite.encrypt(username)

    db_path = f"./databases/custom/{room}.db" if room else "./databases/chatroom.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch the last message from the same user
    cursor.execute("SELECT message FROM messages WHERE username = ? ORDER BY id DESC LIMIT 1", (username,))
    last_message = cursor.fetchone()

    # Decrypt last message if exists
    if last_message:
        last_message_decrypted = cipher_suite.decrypt(last_message[0]).decode()
        if last_message_decrypted == cipher_suite.decrypt(message).decode():
            conn.close()
            return False # Reject duplicate message

    # Insert the new message
    cursor.execute("INSERT INTO messages (username, message, date, colour) VALUES (?, ?, ?, ?)", (username, message, date, colour))
    conn.commit()
    conn.close()

    return True