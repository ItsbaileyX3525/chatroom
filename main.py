#import the required modules
from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
import sqlite3
from cryptography.fernet import Fernet
import bcrypt
import time
import re
import html
import base64 
import random
import string

def get_random_string(length):
    letters = string.ascii_lowercase
    
    return ''.join(random.choice(letters) for i in range(length))

#setup the encrpytion - ripped from stack overflow lol
f = open('key.env')
key = f.read()
key.encode()
f.close()

cipher_suite = Fernet(key) #setting up the cipher with the key
encoded_text = cipher_suite.encrypt(b"Hello stackoverflow!") #Used to encrpyt text
decoded_text = cipher_suite.decrypt(encoded_text) #Used to decrypt 

def read_list_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            # Read the content of the file and convert it to a list
            content = file.read()
            my_list = eval(content)
            return my_list
    except FileNotFoundError:
        print(f"The file '{filename}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

data_list = read_list_from_file('emojis.emo')

def epoch_to_dd_mm_yyyy():
    epoch_time = time.time()
    time_struct = time.gmtime(epoch_time)
    day = time_struct.tm_mday
    month = time_struct.tm_mon
    year = time_struct.tm_year
    formatted_date = "{:02d}/{:02d}/{:04d}".format(day, month, year)
    return formatted_date

def replace_colon_items(input_string, data_list=data_list):
    pattern = r':(.*?):'
    matches = re.findall(pattern, input_string)
    for match in matches:
        if match in data_list:
            input_string = input_string.replace(f':{match}:', data_list[match])
    return input_string

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
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, message TEXT, date TEXT)''')
    conn.commit()
    conn.close()

# Function to get all messages from the database
def get_messages():
    conn = sqlite3.connect("chatroom.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, message, date FROM messages ORDER BY id ASC")
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
    try:
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password=? WHERE username=?", (hashed_password, username))
        conn.commit()
        conn.close()
        return True
    except:
        return False
    
#Clear out the entire database of chats in case of anything
def clear_messages():
    conn = sqlite3.connect("chatroom.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages")
    conn.commit()
    conn.close()
    send_js("""const chatBox = document.getElementById('chat-box');chatBox.innerHTML = ''""")
    send({'username': 'System', 'message': 'Admin wiped the message database! (refresh to remove this message)', 'date': epoch_to_dd_mm_yyyy()}, broadcast=True)

#Wipe all the databases (messasges and users)
def wipeEverything():
    print("Wiped completely")
    #Wipe messages
    conn = sqlite3.connect("chatroom.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages")
    conn.commit()
    conn.close()

    #Wipe usernames and passwords
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")
    conn.commit()
    conn.close()

    send_js('''setTimeout(function(){
            Logout()
    }, 5000);showNotification("Admin wiped everything, signing out in 3 seconds")
           ''')


# Function to add a new message to the database
def add_message(username, message, date):
    message = str.encode(message);username = str.encode(username)
    message = cipher_suite.encrypt(message)
    username = cipher_suite.encrypt(username)
    conn = sqlite3.connect("chatroom.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (username, message, date) VALUES (?, ?, ?)", (username, message, date))
    conn.commit()
    conn.close()

@app.route("/")
def index():
    newMessageList = [] 
    messages = get_messages()
    if messages:
        for message in messages:
            if len(message) >= 3:
                Dusername = message[0]
                Dusername = cipher_suite.decrypt(Dusername)
                Dusername = Dusername.decode()
                Dmessage = message[1]
                Dmessage = cipher_suite.decrypt(Dmessage)
                Dmessage = Dmessage.decode()
                Dmessage = replace_colon_items(Dmessage)
                Ddate = message[2]
                newMessageList.append((Dusername, Dmessage, Ddate))
            else:
                print(messages)
                    
    return render_template("index.html", messages=newMessageList)

@socketio.on('AdminMessage')
def handle_admin_message(message_data):
    date = epoch_to_dd_mm_yyyy()
    if message_data['key'] == 'AdminKey':
        message = message_data['message']
        message = message.split()
        if message_data['message'] == '/wipe':
            clear_messages()
        elif message[0] == '/change':
            print("changed " + message[1], "'s password.")
            username =message[1]
            username.strip()
            password =  message[2]
            password.strip() 
            change_password(username, new_password=password)
    else:
        send({'username': "Admin", 'message': message_data['message'], 'date': date}, broadcast=True)

sounds={
    "hellNaw":'"hellNaw"',
    "clang":'"clang"',
    "mew":'"mew"',
    "boom":'"boom"',
    "whatDaDogDoin":'"whatDaDogDoin"',
    "pluh":'"pluh"',
    "gay":'"gay"'
}

def handleCommands(input, args=None, username=None):
    if input == '/help':
        try:
            args = args.strip()
            if args == '':
                args = None
        except:
            pass
        send_js(f'''const chatBox = document.getElementById("chat-box");
                    const messageElement = document.createElement("p");
                    messageElement.innerHTML = `<strong style="color: rgb(198, 201, 204);">System:</strong>
                    <span style="color: rgb(198, 201, 204);"> {"The current list of commands are: /help, /emojis, /emojiList, /fullEmojiList, /play, /playList and /changePwd for specific help use /help (command)" if args is None else "Syntax is /changePwd (NewPassword)" if args == "changePwd" or args=='/changePwd' else 'Syntax is /play (soundName), example /play hellNaw' if args=='/play' or args=='play' else "That command doesn't exist or doesn't have any help related to it." if args is None or args != '' else None} </span>`;
                    chatBox.appendChild(messageElement);''', sid=request.sid)
    elif input == '/emojis':
        send_js('''const chatBox = document.getElementById("chat-box");
                     const messageElement = document.createElement("p");
                     messageElement.innerHTML = `<strong style="color: rgb(198, 201, 204);">System:</strong>
                     <span style="color: rgb(198, 201, 204);"> To use emojis it's like discord, so it's :skull: to see a list of popular emojis use /emojiList </span>`;
                     chatBox.appendChild(messageElement);''', sid=request.sid)
    elif input == '/emojiList':
        send_js('''const chatBox = document.getElementById("chat-box");
                     const messageElement = document.createElement("p");
                     messageElement.innerHTML = `<strong style="color: rgb(198, 201, 204);">System:</strong>
                     <span style="color: rgb(198, 201, 204);"> The top 4 used are: :skull:, :smile:, :cry:, :thumbs_up: to see all of them use /fullEmojiList </span>`;
                     chatBox.appendChild(messageElement);''', sid=request.sid)
    elif input == '/fullEmojiList':
        send_js('''const chatBox = document.getElementById("chat-box");
                     const messageElement = document.createElement("p");
                     messageElement.innerHTML = `<strong style="color: rgb(198, 201, 204);">System:</strong>
                     <span style="color: rgb(198, 201, 204);"> Enjoy :)\nJk lol I'm not going to flood you with 900 lines of emojis but you can view the emoji list from <a target="_blank" href="https://pastebin.com/1b0QnGxg">here</a></span>`;
                     chatBox.appendChild(messageElement);''', sid=request.sid)
    elif input == '/changePwd':
        success = change_password(username, args)
        send_js(f'''const chatBox = document.getElementById("chat-box");
                     const messageElement = document.createElement("p");
                     messageElement.innerHTML = `<strong style="color: rgb(198, 201, 204);">System:</strong>
                     <span style="color: rgb(198, 201, 204);"> {f'Successfully changed password to {args}' if success else f'Failed to change the password to {args}' } </span>`;
                     chatBox.appendChild(messageElement);''', sid=request.sid)
    elif input == '/wipe':
        if args == 'AdminKey':
            clear_messages()        
        else:
            send_js('''const chatBox = document.getElementById("chat-box");
                const messageElement = document.createElement("p");
                messageElement.innerHTML = `<strong style="color: rgb(198, 201, 204);">System:</strong>
                <span style="color: rgb(198, 201, 204);"> Sorry but that key just isn't right. Perhaps you're not an admin and don't have the access key </span>`;
                chatBox.appendChild(messageElement);''', sid=request.sid)
    elif input == '/play':
        if args in sounds:
            send_js(f"""playAudio({sounds[args]})""")
    elif input == '/playList':
        send_js('''const chatBox = document.getElementById("chat-box");
                const messageElement = document.createElement("p");
                messageElement.innerHTML = `<strong style="color: rgb(198, 201, 204);">System:</strong>
                <span style="color: rgb(198, 201, 204);"> Current list of sounds are: 'hellNaw', 'clang', 'gay', 'pluh', 'whatDaDogDoin', 'boom' and 'mew'. </span>`;
                chatBox.appendChild(messageElement);''', sid=request.sid)
    elif input == '/destroyAll':
        if args == "AdminKey":
            wipeEverything()
        else:
            send_js('''const chatBox = document.getElementById("chat-box");
                const messageElement = document.createElement("p");
                messageElement.innerHTML = `<strong style="color: rgb(198, 201, 204);">System:</strong>
                <span style="color: rgb(198, 201, 204);"> Sorry but that key just isn't right. </span>`;
                chatBox.appendChild(messageElement);''', sid=request.sid)
    else:
        send_js('''const chatBox = document.getElementById("chat-box");
                const messageElement = document.createElement("p");
                messageElement.innerHTML = `<strong style="color: rgb(198, 201, 204);">System:</strong>
                <span style="color: rgb(198, 201, 204);"> Sorry I don't believe that is a command, perhaps check your spelling? </span>`;
                chatBox.appendChild(messageElement);''', sid=request.sid)

#Handle user image upload
@socketio.on('imageUpload')
def handle_user_upload(imageData):
    imageDataU = imageData[0][len("data:image/png;base64,"):]
    #I guess png only for now
    image = base64.b64decode(imageDataU)
    username=imageData[1]
    randomImageName = get_random_string(40)
    date = epoch_to_dd_mm_yyyy()
    f = open(f"static/usersUploaded/{randomImageName}.png", "wb")
    f.write(image)
    f.close()
    message = f'<img src="../static/usersUploaded/{randomImageName}.png" alt="{username} style="width=80%; height=80%"/>'
    add_message(username, message, date)
    send({'username': username, 'message': message, 'date': date}, broadcast=True)

@socketio.on('message')
def handle_message(message_data):
    username = message_data['username']
    lowerUser = username.lower()
    message = message_data['message']
    date = epoch_to_dd_mm_yyyy()
    trimmedMessage = message.split()

    if lowerUser in hardBannedNames:
        send_js('''alert("This is a reserved name, sorry.")''', sid=request.sid)
    elif trimmedMessage[0].startswith("/"):
        parts = message.split(" ", 1)
        print(parts)
        if len(parts) > 2:
            send_js('''const chatBox = document.getElementById("chat-box");
                const messageElement = document.createElement("p");
                messageElement.innerHTML = `<strong style="color: rgb(198, 201, 204);">System:</strong>
                <span style="color: rgb(198, 201, 204);"> Error: Password cannot contain spaces. </span>`;
                chatBox.appendChild(messageElement);''', sid=request.sid)
        else:
            try:
                handleCommands(parts[0],parts[1],username)
            except:
                handleCommands(parts[0])
    else:
        if re.match(r'(https?://.*\.(?:png|jpg|jpeg|gif|webp))', message):
            # If it's an image URL, render it as an image
            message = f'<img src="{message}" alt="{username} style="width=80%; height=80%"/>'
            send({'username': username, 'message': message, 'date': date}, broadcast=True)
            add_message(username, message, date)
        elif re.match(r'(https?://.*\.(?:mp4|mov|webm))', message):
            #Same with a video URL
            message = f'<video preload = "none"  src="{message}" alt="{username}" controls autoplay muted></video>'
            send({'username': username, 'message': message, 'date': date}, broadcast=True)
        else:
            escaped_message = html.escape(message)
            add_message(username, escaped_message, date)
            escaped_message = replace_colon_items(escaped_message)
            send({'username': username, 'message': escaped_message, 'date': date}, broadcast=True)
            send_js("""notifyUser()""")


#Login
@app.route("/Login")
def Login():
    return render_template("Login.html")

@app.route("/PrivacyPolicy")
def PrivacyPolicy():
    return render_template("PrivacyPolicy.html")

def create_table_accounts():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      username TEXT NOT NULL UNIQUE, 
                      password TEXT NOT NULL,
                      agreement TEXT NOT NULL)''')
    conn.commit()
    conn.close()

create_table_accounts ()

@socketio.on('OnConnect')
def connected(username):
    send_js(f'''showNotification("{username} has conncted!")''')

@socketio.on('register')
def register(data):
    username = data['username']
    password = data['password']
    agreement = data['agreed']
    print(agreement)
    Dusername = username.lower()
    Dusername = Dusername.strip()

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    existing_user = cursor.fetchone()
    if Dusername in hardBannedNames:
        emit('registration_response', {'message': 'Reserved username.'})
    elif existing_user:
        emit('registration_response', {'message': 'Username already exists.'})
    elif agreement != "yes":
        emit('registration_response', {'message': 'Please agree to the privacy policy and consent service.'})
    else:
        # Hashing password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username, password, agreement) VALUES (?, ?, ?)", (username, hashed_password, agreement))
        conn.commit()
        conn.close()
        emit('registration_response', {'message': 'Registration successful'})
        send_js(f'''localStorage.setItem('username', "{username}");localStorage.setItem('LoggedIn', 1);window.location.href = "../"''', sid=request.sid)

@socketio.on('login')
def login(data):
    username = data['username']
    password = data['password']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute("SELECT password FROM users WHERE username=?", (username,))
    hashed_password = cursor.fetchone()
    cursor.execute("SELECT agreement FROM users WHERE username=?", (username,))
    agreed = cursor.fetchone()
    conn.close()
    if hashed_password and bcrypt.checkpw(password.encode('utf-8'), hashed_password[0]):
        if agreed[0] == 'yes':
            send_js(f'''localStorage.setItem("username", "{username}");localStorage.setItem("LoggedIn", 1);window.location.href = "../"''', sid=request.sid)
        else:
           emit('login_response', {'message': 'Account has not agreed to privacy policy, please contact Admin or create new account'}) 
    else:
        emit('login_response', {'message': 'Invalid username or password'})


if __name__ == "__main__":
    init_db()
    socketio.run(app, debug=True, host='0.0.0.0',port=5000)