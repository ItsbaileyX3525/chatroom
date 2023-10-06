#import the required modules
from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
import sqlite3
from cryptography.fernet import Fernet

#setup the encrpytion - ripped from stack overflow lol
key=b'aCkApqJJoVHfoj79F8h0367griF43gv9aYftgxdfo-E='
cipher_suite = Fernet(key) #setting up the cipher with the key
encoded_text = cipher_suite.encrypt(b"Hello stackoverflow!") #Used to encrpyt text
decoded_text = cipher_suite.decrypt(encoded_text) #Used to decrypt 

#define the application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

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
    print(sid)
    if sid != None:
        emit('execute_js', js_code, room=sid)
    else:
        emit('execute_js', js_code, broadcast=True)

'''@socketio.on('userConnected')
def sent_raw(user='System', mess='Default message'):
    jscode = f"""const chatBox = document.getElementById("chat-box");const messageElement = document.createElement("p");messageElement.innerHTML = `<strong>{user}:</strong> {mess}`;chatBox.appendChild(messageElement);"""
    send_js(jscode)'''

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
    message = cipher_suite.encrypt(username)
    conn = sqlite3.connect("chatroom.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (username, message) VALUES (?, ?)", (username, message))
    conn.commit()
    conn.close()

@app.route("/")
def index():
    messages = get_messages()
    if messages:
        messages = str.encode(messages)
        messages = cipher_suite.decrypt(messages)
        messages = messages.decode()
    return render_template("index.html", messages=messages)

@socketio.on('AdminMessage')
def handle_admin_message(message_data):
    print(message_data)
    if message_data['key'] == 'LeonStinks':
        if message_data['message'] == '/wipe':
            clear_messages() 

@socketio.on('message')
def handle_message(message_data):
    username = message_data['username']
    message = message_data['message']
    if message_data['username'] in hardBannedNames:
        send_js('''alert("This is a reserved name, sorry.")''', sid=request.sid)
    elif message == '/help' or message == '/help ':
        send_js('''messageElement.innerHTML = `<strong style="color: rgb(198, 201, 204);">System:</strong> <span style="color: rgb(198, 201, 204);">Sorry, but the help command is under-construction... :(</span>`''', sid=request.sid)
    else:
        add_message(username, message)
        send({'username': username, 'message': message}, broadcast=True)

if __name__ == "__main__":
    init_db()
    socketio.run(app, debug=True, host='0.0.0.0')