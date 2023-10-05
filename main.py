#import the required modules
from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
import sqlite3

#define the application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

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
def send_js(js_code):
    # Emit the received JavaScript code to the client
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
    conn = sqlite3.connect("chatroom.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (username, message) VALUES (?, ?)", (username, message))
    conn.commit()
    conn.close()

@app.route("/")
def index():
    messages = get_messages()
    return render_template("index.html", messages=messages)

@socketio.on('message')
def handle_message(message_data):
    print(message_data)
    if message_data['message'] == '/wipe' and message_data['username'] == 'Admin':
        clear_messages()
    else:
        username = message_data['username']
        message = message_data['message']
        add_message(username, message)
        send({'username': username, 'message': message}, broadcast=True)

if __name__ == "__main__":
    init_db()
    socketio.run(app, debug=True, host='0.0.0.0')