#import the required modules
from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
import sqlite3
from cryptography.fernet import Fernet
import bcrypt
import time
import os
import re
import html
import base64 
import random
import string

#In case the folder doesnt exist otherwise 
#image uploads dont wok
if not os.path.isdir("static/usersUploaded"):
    os.mkdir("static/usersUploaded")

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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
socketio = SocketIO(app, max_http_buffer_size=16 * 1024 * 1024)

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
    send({'username': 'System', 'message': 'Admin wiped the message database! (refresh to remove this message)', 'date': epoch_to_dd_mm_yyyy(), 'isCustom': "no"}, broadcast=True)

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

def banUser(username):
    #Used for banning users to prevent VPN usage

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT UUID FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    print("The result", result[0])
    f = open('blacklistUUID.db',"a")
    f.write(result[0]+"\n")
    f.close()

sounds={
    "hellNaw":'"hellNaw"',
    "clang":'"clang"',
    "mew":'"mew"',
    "boom":'"boom"',
    "whatDaDogDoin":'"whatDaDogDoin"',
    "pluh":'"pluh"',
    "gay":'"gay"'
}
fonts={
    "Helvetica":"'Custom1'",
    "Normal":"'Normal'",
    "RobotoMono":"'Custom3'",
    "SourceCodePro":"'Custom4'",
    "ComicSans":"'Custom2'"
}
def handleCommands(args):
    input = args[0]
    print(len(args))
    if input == '/help':
        if len(args) == 1:
            args = None
        send_js(f'''const chatBox = document.getElementById("chat-box");
            const messageElement = document.createElement("p");
            messageElement.classList.add("chat-message")
            const systemName = document.createElement("span");
            const systemMessage = document.createElement("span");
            systemName.classList.add("username", "system");
            systemName.innerHTML = "System: "
            systemMessage.classList.add("message");
            systemMessage.innerHTML = "{"The current list of commands are: /help, /emojis, /emojiList, /play, /playList, /font and /changePwd for specific help use /help (command)" if args is None else "Syntax is /changePwd (NewPassword)" if args[1] == "changePwd" or args[1]=='/changePwd' else 'Syntax is /play (soundName), example /play hellNaw' if args[1]=='/play' or args[1]=='play' else 'Syntax is /font (FontName), example /font RobotoMono' if args[1]=="/font" or args[1]=="font" else "That command doesn't exist or doesn't have any help related to it." if args is None or args != '' else None} "
            messageElement.appendChild(systemName);
            messageElement.appendChild(systemMessage);
            chatBox.appendChild(messageElement);''', sid=request.sid)
    elif input == '/emojis':
        send_js('''const chatBox = document.getElementById("chat-box");
            const messageElement = document.createElement("p");
            messageElement.classList.add("chat-message")
            const systemName = document.createElement("span");
            const systemMessage = document.createElement("span");
            systemName.classList.add("username", "system");
            systemName.innerHTML = "System: "
            systemMessage.classList.add("message");
            systemMessage.innerHTML = "To use emojis it's like discord, so it's :skull: to see a list of popular emojis use /emojiList"
            messageElement.appendChild(systemName);
            messageElement.appendChild(systemMessage);
            chatBox.appendChild(messageElement);''', sid=request.sid)
    elif input == '/emojiList':
        send_js('''const chatBox = document.getElementById("chat-box");
            const messageElement = document.createElement("p");
            messageElement.classList.add("chat-message")
            const systemName = document.createElement("span");
            const systemMessage = document.createElement("span");
            systemName.classList.add("username", "system");
            systemName.innerHTML = "System: "
            systemMessage.classList.add("message");
            systemMessage.innerHTML = "To use emojis it's like discord, so it's :skull: to see a list of popular emojis use /emojiList"
            messageElement.appendChild(systemName);
            messageElement.appendChild(systemMessage);
            chatBox.appendChild(messageElement);''', sid=request.sid)
    elif input == '/changePwd': #Currently does not work (too tired too fix atm)
        #success = change_password(args[1], args[2])
        send_js('''const chatBox = document.getElementById("chat-box");
            const messageElement = document.createElement("p");
            messageElement.classList.add("chat-message")
            const systemName = document.createElement("span");
            const systemMessage = document.createElement("span");
            systemName.classList.add("username", "system");
            systemName.innerHTML = "System: "
            systemMessage.classList.add("message");
            systemMessage.innerHTML = "Sorry change password doesn't work at the moment contact admin to change your password"
            messageElement.appendChild(systemName);
            messageElement.appendChild(systemMessage);
            chatBox.appendChild(messageElement);''', sid=request.sid)
        """
        send_js(f'''const chatBox = document.getElementById("chat-box");
            const messageElement = document.createElement("p");
            messageElement.classList.add("chat-message")
            const systemName = document.createElement("span");
            const systemMessage = document.createElement("span");
            systemName.classList.add("username", "system");
            systemName.innerHTML = "System: "
            systemMessage.classList.add("message");
            systemMessage.innerHTML = "{f'Successfully changed password to {args}' if success else f'Failed to change the password to {args}' }"
            messageElement.appendChild(systemName);
            messageElement.appendChild(systemMessage);
            chatBox.appendChild(messageElement);''', sid=request.sid)"""
    elif input == '/wipe':
        if args[1] == 'AdminKey':
            clear_messages()        
        else:
            send_js('''const chatBox = document.getElementById("chat-box");
                const messageElement = document.createElement("p");
                messageElement.classList.add("chat-message")
                const systemName = document.createElement("span");
                const systemMessage = document.createElement("span");
                systemName.classList.add("username", "system");
                systemName.innerHTML = "System: "
                systemMessage.classList.add("message");
                systemMessage.innerHTML = "Sorry but that key just isn't right. Perhaps you're not an admin and don't have the access key"
                messageElement.appendChild(systemName);
                messageElement.appendChild(systemMessage);
                chatBox.appendChild(messageElement);''', sid=request.sid)
    elif input == "/font":
        if args[1] in fonts:
            send_js(f"""changeFont({fonts[args[1]]});localStorage.setItem('font', {fonts[args[1]]});""", sid=request.sid)

    elif input == '/playList':
        send_js('''const chatBox = document.getElementById("chat-box");
            const messageElement = document.createElement("p");
            messageElement.classList.add("chat-message")
            const systemName = document.createElement("span");
            const systemMessage = document.createElement("span");
            systemName.classList.add("username", "system");
            systemName.innerHTML = "System: "
            systemMessage.classList.add("message");
            systemMessage.innerHTML = "Current list of fonts are: 'Helvetica', 'RobotoMono', 'SourceCodePro', 'Normal' and 'ComicSans'"
            messageElement.appendChild(systemName);
            messageElement.appendChild(systemMessage);
            chatBox.appendChild(messageElement);''', sid=request.sid)
    
    elif input == '/play':
        if args[1] in sounds:
            send_js(f"""playAudio({sounds[args[1]]})""")
        else:
            if re.match(r'(https?://.*\.(?:mp3|ogg))', args[1]):#
                send_js(f'''playAudio('custom', "{args[1]}")''')

    elif input == '/playList':
        send_js('''const chatBox = document.getElementById("chat-box");
            const messageElement = document.createElement("p");
            messageElement.classList.add("chat-message")
            const systemName = document.createElement("span");
            const systemMessage = document.createElement("span");
            systemName.classList.add("username", "system");
            systemName.innerHTML = "System: "
            systemMessage.classList.add("message");
            systemMessage.innerHTML = "Current list of sounds are: 'hellNaw', 'clang', 'gay', 'pluh', 'whatDaDogDoin', 'boom' and 'mew'"
            messageElement.appendChild(systemName);
            messageElement.appendChild(systemMessage);
            chatBox.appendChild(messageElement);''', sid=request.sid)
    elif input == '/destroyAll':
        if args[1] == "AdminKey":
            wipeEverything()
        else:
            send_js('''const chatBox = document.getElementById("chat-box");
                const messageElement = document.createElement("p");
                messageElement.classList.add("chat-message")
                const systemName = document.createElement("span");
                const systemMessage = document.createElement("span");
                systemName.classList.add("username", "system");
                systemName.innerHTML = "System: "
                systemMessage.classList.add("message");
                systemMessage.innerHTML = "Sorry but that key just isn't right"
                messageElement.appendChild(systemName);
                messageElement.appendChild(systemMessage);
                chatBox.appendChild(messageElement);''', sid=request.sid)
    elif input == '/ban':
        if args[1] == 'AdminKey':
            banUser(args[2])
            emit('userToBan', args[2])
    else:
        send_js('''const chatBox = document.getElementById("chat-box");
            const messageElement = document.createElement("p");
            messageElement.classList.add("chat-message")
            const systemName = document.createElement("span");
            const systemMessage = document.createElement("span");
            systemName.classList.add("username", "system");
            systemName.innerHTML = "System: "
            systemMessage.classList.add("message");
            systemMessage.innerHTML = "Sorry I don't believe that is a command, perhaps check your spelling?"
            messageElement.appendChild(systemName);
            messageElement.appendChild(systemMessage);
            chatBox.appendChild(messageElement);''', sid=request.sid)

#Ban a user
@socketio.on('handleIP')
def handleIP():
    ip = request.remote_addr
    with open("blacklist.db", 'a') as f:
        f.write(f"\n{ip}")
        f.close()
    send_js(f'''location.reload();''', sid=request.sid)

#Handle user image upload
@socketio.on('imageUpload')
def handle_user_upload(imageData):
    imageType = imageData[1]
    username = imageData[2]
    date = epoch_to_dd_mm_yyyy()
    randomImageName = get_random_string(40)

    if imageType == 'png':
        imageDataU = imageData[0][len("data:image/png;base64,"):]
        image = base64.b64decode(imageDataU)
        f = open(f"static/usersUploaded/{randomImageName}.png", "wb")
        f.write(image)
        f.close()

        message = f'<img src="../static/usersUploaded/{randomImageName}.png" alt="{username}"/>'

    elif imageType == 'jpg':
        imageDataU = imageData[0][len("data:image/jpg;base64,"):]
        image = base64.b64decode(imageDataU)
        f = open(f"static/usersUploaded/{randomImageName}.jpg", "wb")
        f.write(image)
        f.close()

        message = f'<img src="../static/usersUploaded/{randomImageName}.jpg" alt="{username}"/>'

    elif imageType == 'jpeg':
        imageDataU = imageData[0][len("data:image/jpg;base64,"):]
        image = base64.b64decode(imageDataU)
        f = open(f"static/usersUploaded/{randomImageName}.jpeg", "wb")
        f.write(image)
        f.close()

        message = f'<img src="../static/usersUploaded/{randomImageName}.jpeg" alt="{username}"/>'

    elif imageType == 'webp':
        imageDataU = imageData[0][len("data:image/webp;base64,"):]
        image = base64.b64decode(imageDataU)
        f = open(f"static/usersUploaded/{randomImageName}.webp", "wb")
        f.write(image)
        f.close()

        message = f'<img src="../static/usersUploaded/{randomImageName}.webp" alt="{username}">'
    
    add_message(username, message, date)
    send({'username': username, 'message': message, 'date': date}, broadcast=True)

@socketio.on('message')
def handle_message(message_data):
    username = message_data['username']
    lowerUser = username.lower()
    message = message_data['message']
    UUID = message_data['UUID']
    date = epoch_to_dd_mm_yyyy()
    trimmedMessage = message.split()

    #Validating UUID because someone could fake their username
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT UUID FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()

    #checking if user is banned
    f = open('blacklistUUID.db')
    Blacklist = f.read().splitlines()

    if UUID in Blacklist:
        send_js('''const chatBox = document.getElementById("chat-box");
            const messageElement = document.createElement("p");
            messageElement.classList.add("chat-message")
            const systemName = document.createElement("span");
            const systemMessage = document.createElement("span");
            systemName.classList.add("username", "system");
            systemName.innerHTML = "System: "
            systemMessage.classList.add("message");
            systemMessage.innerHTML = "You are banned ;P, and now we are going to reban this new IP ;) "
            messageElement.appendChild(systemName);
            messageElement.appendChild(systemMessage);
            chatBox.appendChild(messageElement);''', sid=request.sid)
        emit('userToBan', username)
        
        return

    if result:
        uuid = result[0]
        print("Users UUID", UUID)
        print("Database UUID", uuid)
        if UUID == uuid:

            if lowerUser in hardBannedNames:
                send_js('''alert("This is a reserved name, sorry.")''', sid=request.sid)
            elif trimmedMessage[0].startswith("/"):
                message = message.split()
                handleCommands(message)

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
        else:
                send_js('''const chatBox = document.getElementById("chat-box");
                    const messageElement = document.createElement("p");
                    messageElement.classList.add("chat-message")
                    const systemName = document.createElement("span");
                    const systemMessage = document.createElement("span");
                    systemName.classList.add("username", "system");
                    systemName.innerHTML = "System: "
                    systemMessage.classList.add("message");
                    systemMessage.innerHTML = "Error: UUID mismatch, likely because you tried to use a custom name, please contact the admin if not"
                    messageElement.appendChild(systemName);
                    messageElement.appendChild(systemMessage);
                    chatBox.appendChild(messageElement);''', sid=request.sid)
    else:
        send_js('''const chatBox = document.getElementById("chat-box");
            const messageElement = document.createElement("p");
            messageElement.classList.add("chat-message")
            const systemName = document.createElement("span");
            const systemMessage = document.createElement("span");
            systemName.classList.add("username", "system");
            systemName.innerHTML = "System: "
            systemMessage.classList.add("message");
            systemMessage.innerHTML = "Error: No UUID matched with provided username, perhaps the users database was wiped and you haven't logged out? If not contact admin "
            messageElement.appendChild(systemName);
            messageElement.appendChild(systemMessage);
            chatBox.appendChild(messageElement);''', sid=request.sid)

def user_on_mobile() -> bool:

    user_agent = request.headers.get("User-Agent")
    user_agent = user_agent.lower()
    phones = ["android", "iphone"]

    if any(x in user_agent for x in phones):
        return True
    return False

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

    f = open('blacklist.db')
    Blacklist = f.read().splitlines()
    ip_address = request.remote_addr
    f.close()
    if ip_address in Blacklist:
        return render_template("UhOhYoureBanned.html")
    else:
        if user_on_mobile():
            return render_template("indexMobile.html", messages=newMessageList)
        else:
            return render_template("index.html", messages=newMessageList)


@app.route("/Login")
def Login():
    if user_on_mobile():
        return render_template("LoginMobile.html")
    else:
        return render_template("Login.html")


@app.route("/PrivacyPolicy")
def PrivacyPolicy():
    return render_template("PrivacyPolicy.html")

@app.errorhandler(404)
def resource_not_found(e):
    return render_template("404.html")

def create_table_accounts():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      username TEXT NOT NULL UNIQUE, 
                      password TEXT NOT NULL,
                      agreement TEXT NOT NULL,
                      UUID TEXT NOT NULL)''')
    conn.commit()
    conn.close()

create_table_accounts ()

@socketio.on('OnConnect')
def connected(username):
    print(username)
    send_js(f'''showNotification("{username} has connected!")''')

@socketio.on('register')
def register(data):
    username = data['username']
    password = data['password']
    agreement = data['agreed']
    UUID = data['UUID']
    Dusername = username.lower()
    Dusername = Dusername.strip()
    Dpassword = bool(re.search(r"\s", password))

    if Dpassword:
        emit('registration_response', {'message': 'Password can not contain spaces', 'colour': 'red'})
    else:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        existing_user = cursor.fetchone()
        if Dusername in hardBannedNames:
            emit('registration_response', {'message': 'Reserved username.', 'colour': 'red'})
        elif existing_user:
            emit('registration_response', {'message': 'Username already exists.', 'colour': 'red'})
        elif agreement != "yes":
            emit('registration_response', {'message': 'Please agree to the privacy policy and consent service.', 'colour': 'red'})
        else:
            # Hashing password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("INSERT INTO users (username, password, agreement, UUID) VALUES (?, ?, ?, ?)", (username, hashed_password, agreement, UUID))
            conn.commit()
            conn.close()
            emit('registration_response', {'message': 'Registration successful', 'colour': 'green'})
            send_js(f'''localStorage.setItem('username', "{username}");localStorage.setItem('UUID', "{UUID}");localStorage.setItem('LoggedIn', 1);window.location.href = "../"''', sid=request.sid)

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
    cursor.execute("SELECT UUID FROM users WHERE username=?", (username,))
    UUID=cursor.fetchone()
    conn.close()
    if hashed_password and bcrypt.checkpw(password.encode('utf-8'), hashed_password[0]):
        if agreed[0] == 'yes':
            send_js(f'''localStorage.setItem("username", "{username}");localStorage.setItem("UUID", "{UUID[0]}");localStorage.setItem("LoggedIn", 1);window.location.href = "../"''', sid=request.sid)
            emit('login_response', {'message': 'Success!', 'colour': 'red'}) 
        else:
           emit('login_response', {'message': 'Account has not agreed to privacy policy, please contact Admin or create new account', 'colour': 'red'}) 
    else:
        emit('login_response', {'message': 'Invalid username or password', 'colour': 'red'})


if __name__ == "__main__":
    init_db()
    context = ('local.pem', 'local.key')
    socketio.run(app, debug=True, host='0.0.0.0',port=443, ssl_context=context)