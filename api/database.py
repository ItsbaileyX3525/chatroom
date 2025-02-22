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
    message = str.encode(message);username = str.encode(username);
    message = cipher_suite.encrypt(message)
    username = cipher_suite.encrypt(username)
    if room:
        conn = sqlite3.connect(f"./databases/custom/{room}.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (username, message, date, colour) VALUES (?, ?, ?, ?)", (username, message, date, colour))
        conn.commit()
        conn.close()
    else:
        conn = sqlite3.connect("./databases/chatroom.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (username, message, date, colour) VALUES (?, ?, ?, ?)", (username, message, date, colour))
        conn.commit()
        conn.close()
