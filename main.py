#import the required modules
from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
import sqlite3
from cryptography.fernet import Fernet
import time


#setup the encrpytion - ripped from stack overflow lol
key=b'aCkApqJJoVHfoj79F8h0367griF43gv9aYftgxdfo-E='
cipher_suite = Fernet(key) #setting up the cipher with the key
encoded_text = cipher_suite.encrypt(b"Hello stackoverflow!") #Used to encrpyt text
decoded_text = cipher_suite.decrypt(encoded_text) #Used to decrypt 

def epoch_to_dd_mm_yyyy():
    epoch_time = time.time()
    time_struct = time.gmtime(epoch_time)
    day = time_struct.tm_mday
    month = time_struct.tm_mon
    year = time_struct.tm_year
    formatted_date = "{:02d}/{:02d}/{:04d}".format(day, month, year)
    return formatted_date

#define the application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
#sslify = SSLify(app)

hardBannedNames = ['System', 'system']

# Initialize the SQLite database
def init_db():
    conn = sqlite3.connect("chatroom.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, message TEXT)''')
    conn.commit()
    conn.close()

# Function to get all messages from the database
def get_messages():
    conn = sqlite3.connect("chatroom.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, message FROM messages ORDER BY id ASC")
    messages = cursor.fetchall()
    conn.close()
    return messages

@socketio.on('send_js_code')
def send_js(js_code, sid=None):
    if sid != None:
        emit('execute_js', js_code, room=sid)
    else:
        emit('execute_js', js_code, broadcast=True)

def get_password(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username=?", (username,))
    password = cursor.fetchone()
    conn.close()
    if password:
        return password[0]
    else:
        return None

def change_password(username, new_password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))
    conn.commit()
    conn.close()
    return True

def clear_messages():
    conn = sqlite3.connect("chatroom.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages")
    conn.commit()
    conn.close()
    send_js("""console.log("Balls");const chatBox = document.getElementById('chat-box');chatBox.innerHTML = ''""")
    send({'username': 'System', 'message': 'Admin wiped the message database! (refresh to remove this message)'}, broadcast=True)


# Function to add a new message to the database
def add_message(username, message):
    message = str.encode(message);username = str.encode(username)
    message = cipher_suite.encrypt(message)
    username = cipher_suite.encrypt(username)
    conn = sqlite3.connect("chatroom.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (username, message) VALUES (?, ?)", (username, message))
    conn.commit()
    conn.close()

@app.route("/")
def index():
    newMessageList = [] 
    messages = get_messages()
    if messages:
        for message in messages:
            Dusername = message[0]
            Dusername = cipher_suite.decrypt(Dusername)
            Dusername = Dusername.decode()
            Dmessage = message[1]
            Dmessage = cipher_suite.decrypt(Dmessage)
            Dmessage = Dmessage.decode()

            newMessageList.append((Dusername,Dmessage))
            
    return render_template("index.html", messages=newMessageList)

@socketio.on('AdminMessage')
def handle_admin_message(message_data):
    if message_data['key'] == 'LeonStinks':
        username = message_data['message']
        username = username.split()
        if message_data['message'] == '/wipe':
            clear_messages()
        elif username[0] == '/change':
            change_password(username[1], new_password=username[2])
    else:
        send({'username': "Admin", 'message': message_data['message']}, broadcast=True)

@socketio.on('message')
def handle_message(message_data):
    username = message_data['username']
    lowerUser = username.lower()
    message = message_data['message']
    if lowerUser in hardBannedNames: 
        send_js('''alert("This is a reserved name, sorry.")''', sid=request.sid)
    elif message == '/help' or message == '/help ':
        send_js('''const chatBox = document.getElementById("chat-box");const messageElement = document.createElement("p");messageElement.innerHTML = `<strong style="color: rgb(198, 201, 204);">System:</strong><span style="color: rgb(198, 201, 204);"> The current list of commands are: /help... Thats it :P</span>`;chatBox.appendChild(messageElement);''', sid=request.sid)
        
    else:
        add_message(username, message)
        send({'username': username, 'message': message, 'date': epoch_to_dd_mm_yyyy()}, broadcast=True)



#Login
@app.route("/Login")
def Login():
    return render_template("Login.html")

def create_table_accounts():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      username TEXT NOT NULL UNIQUE, 
                      password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

create_table_accounts ()

@socketio.on('register')
def register(data):
    username = data['username']
    password = data['password']
    Dusername = username.lower()
    Dusername = Dusername.strip()

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    existing_user = cursor.fetchone()
    if Dusername in hardBannedNames:
        emit('registration_response', {'message': 'Reserved username.'})
    elif existing_user:
        emit('registration_response', {'message': 'Username already exists'})
    else:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        emit('registration_response', {'message': 'Registration successful'})
        send_js(f'''localStorage.setItem('username', "{username}");localStorage.setItem('LoggedIn', 1);window.location.href = "../"''', sid=request.sid)
        send_js(f'''showNotification("{username}")''')

@socketio.on('login')
def login(data):
    username = data['username']
    password = data['password']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        send_js(f'''localStorage.setItem("username", "{username}");localStorage.setItem("LoggedIn", 1);window.location.href = "../"''', sid=request.sid)
        send_js(f'''showNotification("{username} has joined!")''')
    else:
        emit('login_response', {'message': 'Invalid username or password'})


if __name__ == "__main__":
    init_db()
    socketio.run(app, debug=True, host='0.0.0.0')