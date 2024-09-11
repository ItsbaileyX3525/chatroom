#import the required modules
from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import sqlite3
from cryptography.fernet import Fernet
import bcrypt
import time
import json
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
with open('key.env', 'r') as f:
    key = f.read()
    key.encode()


cipher_suite = Fernet(key) #setting up the cipher with the key
encoded_text = cipher_suite.encrypt(b"Hello stackoverflow!") #Used to encrpyt text
decoded_text = cipher_suite.decrypt(encoded_text) #Used to decrypt 

def read_list_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
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
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=16 * 1024 * 1024)

hardBannedNames = ['System', 'system', 'Admin', 'admin']

# Initialize the SQLite database
def init_db(name):
    conn = sqlite3.connect(f"{name}.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, message TEXT, date TEXT, colour TEXT)''')
    conn.commit()
    conn.close()

# Function to get all messages from the database
def get_messages(name):
    conn = None
    try:
        conn = sqlite3.connect(f"{name}.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, message, date, colour FROM messages ORDER BY id ASC")
        messages = cursor.fetchall()
        conn.close()
    finally:
        if conn:
            conn.close()
    return messages


@socketio.on('send_js_code')
def send_js(js_code, room=None, sid=None, isGlobal=False):
    if isGlobal:
        emit('execute_js', js_code, broadcast=True)
    elif room!=None:
        emit('execute_js', js_code, to=str(room))
    elif sid!=None:
        emit('execute_js', js_code, room=sid)
    else:
        print("unable to send js anywhere, code: ", js_code)


def get_password(username):
    conn = None
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        password = cursor.fetchone()
    finally:
        if conn:
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
    send_js("""const chatBox = document.getElementById('chat-box');chatBox.innerHTML = ''""",isGlobal=True)
    send({'username': 'System', 'message': 'Admin wiped the message database! (refresh to remove this message)', 'date': epoch_to_dd_mm_yyyy(), 'isCustom': "no"}, broadcast=True)

#Wipe all the databases (messasges and users)
def wipeEverything():
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
           ''',isGlobal=True)


# Function to add a new message to the database
def add_message(username, message, date, colour, room=False):
    message = str.encode(message);username = str.encode(username);
    message = cipher_suite.encrypt(message)
    username = cipher_suite.encrypt(username)
    if room:
        conn = sqlite3.connect(f"{room}.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (username, message, date, colour) VALUES (?, ?, ?, ?)", (username, message, date, colour))
        conn.commit()
        conn.close()
    else:
        conn = sqlite3.connect("chatroom.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (username, message, date, colour) VALUES (?, ?, ?, ?)", (username, message, date, colour))
        conn.commit()
        conn.close()

def unbanUser(username):
    with open('blacklist.json', 'r') as file:
        ip = json.load(file)
    with open('blacklistUUID.json', 'r') as file:
        UUID = json.load(file)

    if username in UUID:
        uuid = UUID[username]
        del UUID[username]
        del UUID[uuid]
    if username in ip:
        IP = ip[username]
        del ip[username]
        del ip[IP]

    with open('blacklist.json', 'w') as file:
        json.dump(ip, file)
    with open('blacklistUUID.json', 'w') as file:
        json.dump(UUID, file)

def banUser(username):
    #Used for banning users to prevent VPN usage

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT UUID FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    with open('blacklistUUID.json', 'r') as file:
        data = json.load(file)

    data[username] = result[0]
    data[result[0]] = username

    with open('blacklistUUID.json', 'w') as file:
        json.dump(data, file)

    ip = request.remote_addr
    with open('blacklist.json', 'r') as file:
        data = json.load(file)

    data[username] = ip
    data[ip] = username

    with open('blacklist.json', 'w') as file:
        json.dump(data, file)


sounds={
    "hellNaw":'"hellNaw"',
    "clang":'"clang"',
    "mew":'"mew"',
    "boom":'"boom"',
    "whatDaDogDoin":'"whatDaDogDoin"',
    "pluh":'"pluh"',
    "gay":'"gay"'
}

def send_system_message(message, sid):
    send_js(f'''const chatBox = document.getElementById("chat-box");
        const messageElement = document.createElement("p");
        messageElement.classList.add("chat-message")
        const systemName = document.createElement("span");
        const systemMessage = document.createElement("span");
        systemName.classList.add("username", "system");
        systemName.innerHTML = "System: "
        systemMessage.classList.add("message");
        systemMessage.innerHTML = "{message}"
        messageElement.appendChild(systemName);
        messageElement.appendChild(systemMessage);
        chatBox.appendChild(messageElement);''', sid=sid)


def change_pwd(props={},room="1",*args):
    success = change_password(props["username"],args[0])
    if success:
        send_system_message(f'Successfully changed password to {args[0]}' if success else f'Failed to change the password to {args[0]}', sid=request.sid)

def wipe(props={},room="1",*args):
    if args[0] == 'AdminKey':
        clear_messages()        
    else:
        send_system_message("Sorry but that key just isn't right. Perhaps you're not an admin and don't have the access key", sid=request.sid)

def play_sound(props={},room="1",*args):
    if args[0] in sounds:
        send_js(f"""playAudio({sounds[args[0]]})""", room)
    else:
        if re.match(r'(https?://.*\.(?:mp3|ogg))', args[0]):#
            send_js(f'''playAudio('custom', "{args[0]}")''',room)


def destroy_all(props={},room="1",*args):
    if args[0] == "AdminKey":
        wipeEverything()
    else:
        send_system_message("Sorry but that key just isn't right", sid=request.sid)

def ban(props={},room="1",*args):
    if args[0] == 'AdminKey':
        banUser(args[1])
        
def unban(props={},room="1",*args):
    if args[0] == 'AdminKey':
        unbanUser(args[1])

cmds = {
    "/changePwd": change_pwd,
    "/wipe": wipe,
    "/play": play_sound,
    "/destroyAll": destroy_all,
    "/ban": ban,
    "/unban": unban
}
    

def handleCommands(args,username, room):
    cmd_name = args.pop(0)
    if cmd_name in cmds:
        f = cmds[cmd_name]
        props = {"username":username}
        f(props, room, *args)
    else:
        send_system_message("Sorry I don't believe that is a command, perhaps check your spelling?", sid=request.sid)

#Handle user image upload
def save_image(image_data, file_path):
    with open(file_path, "wb") as f:
        f.write(base64.b64decode(image_data))

@socketio.on('imageUpload')
def handle_user_upload(imageData):
    canSend = False
    UUID = imageData[5]
    username = imageData[6]
    with open('blacklistUUID.json', 'r') as file:
        UUIDCheck = json.load(file)

    if UUID in UUIDCheck:
        send_system_message("You are banned ;P, and now we are going to reban this new IP ;) ", sid=request.sid)
        banUser(username)
        send_js('''location.reload()''',sid=request.sid)
        
        return

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT UUID FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()


    if result:
        uuid = result[0]
        if UUID == uuid:
            canSend=True
        else:
            send_system_message("Error: UUID mismatch, likely because you tried to use a custom name, please contact the admin if not", sid=request.sid)
    else:
        send_system_message("Error: No UUID matched with provided username, perhaps the users database was wiped and you haven't logged out? If not contact admin ",
                            sid=request.sid)

    base64_prefixes = {
        'png': "data:image/png;base64,",
        'jpg': "data:image/jpg;base64,",
        'jpeg': "data:image/jpeg;base64,",
        'webp': "data:image/webp;base64,",
        'gif': "data:image/gif;base64,",
        'jfif': "data:image/jpeg;base64,"
    }
    
    imageType = imageData[1]
    username = imageData[2]
    colour = imageData[3]
    room = str(imageData[4])
    date = epoch_to_dd_mm_yyyy()
    randomImageName = get_random_string(40)
    
    if imageType in base64_prefixes and canSend:
        prefix = base64_prefixes[imageType]
        imageDataU = imageData[0][len(prefix):]
        file_path = f"static/usersUploaded/{randomImageName}.{imageType}"
        
        save_image(imageDataU, file_path)
        
        message = f'<img src="../{file_path}" alt="{username}"/>'
        
        if room == "1":
            add_message(username, message, date, colour)
        else:
            add_message(username, message, date, colour, room)
            
        send({'username': username, 'message': message, 'date': date, "colour": colour}, to=room)

@socketio.on('message')
def handle_message(message_data):
    username = message_data['username']
    if len(username) > 15:
        send_system_message("Username has to be 15 chars or less.", sid=request.sid)
        return
    lowerUser = username.lower()
    message = message_data['message']
    if len(message) > 240:
        send_system_message("Message is farrrrr too long. You can't send that, sorry", sid=request.sid)
        return
    UUID = message_data['UUID']
    roomNumber = str(message_data['roomNumber'])
    date = epoch_to_dd_mm_yyyy()
    colour = message_data['colour']
    trimmedMessage = message.split()

    

    #Validating UUID because someone could fake their username
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT UUID FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    #checking if user is banned
    with open('blacklistUUID.json', 'r') as file:
        UUIDCheck = json.load(file)

    if UUID in UUIDCheck:
        send_system_message("You are banned ;P, and now we are going to reban this new IP ;) ", sid=request.sid)
        banUser(username)
        send_js('''location.reload()''',sid=request.sid)
        
        return

    if result:
        uuid = result[0]
        if UUID == uuid:

            if lowerUser in hardBannedNames:
                send_js('''alert("This is a reserved name, sorry.")''', sid=request.sid)
            elif trimmedMessage[0].startswith("/"):
                message = message.split()
                handleCommands(message,username,room=roomNumber)
            
            else:
                escaped_message = html.escape(message)
                if roomNumber == "1":
                    add_message(username, escaped_message, date, colour)
                else:
                    print("The colours:",colour)
                    add_message(username, escaped_message, date, colour, roomNumber)
                escaped_message = replace_colon_items(escaped_message)
                send({'username': username, 'message': escaped_message, 'date': date, "colour": colour}, to=roomNumber)
        else:
            send_system_message("Error: UUID mismatch, likely because you tried to use a custom name, please contact the admin if not", sid=request.sid)
    else:
        send_system_message("Error: No UUID matched with provided username, perhaps the users database was wiped and you haven't logged out? If not contact admin ",
                            sid=request.sid)

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
    messages = get_messages("chatroom")
    f = open('chatroomVersion.txt')
    version=f.read()
    f.close()
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
                Dcolour = message[3]
                newMessageList.append((Dusername, Dmessage, Ddate, Dcolour))

        # Read the JSON data from the file
    with open('blacklist.json', 'r') as file:
        data = json.load(file)

    ip_address = request.remote_addr

    ipFound = False
    for value in data.values():
        if value == ip_address:
            ipFound = True
            break


    if ipFound:
        return render_template("UhOhYoureBanned.html")
    else:
        return render_template("index.html", messages=newMessageList, version=version)


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
 
create_table_accounts()

@socketio.on('OnConnect')
def connected(username,room):
    send_js(f'''showNotification("{username} has connected!")''', room=room)

@socketio.on('register')
def register(data):
    username = data["username"]
    hasSpaces = username.split(" ")
    if len(hasSpaces) > 1:
        emit('registration_response', {'message': 'Username or password cannot contain spaces', 'colour': 'red'})
        return
    if len(username) > 15:
        emit('registration_response', {"message": "Username has to be 15 characters or less"})
        return
    password = data["password"]
    agreement = data["agreed"]
    UUID = data["UUID"]
    roomNumber = str(data["roomNumber"])
    knownChatrooms = fetchKnownChatrooms()
    Dusername = username.lower()
    Dusername = Dusername.strip()
    Dpassword = bool(re.search(r"\s", password))

    if not roomNumber in knownChatrooms:
        emit('registration_response', {'message': 'Invalid room code!', 'colour': 'red'})
        return


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
        else:
            # Hashing password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("INSERT INTO users (username, password, agreement, UUID) VALUES (?, ?, ?, ?)", (username, hashed_password, agreement, UUID))
            conn.commit() 
            emit('registration_response', {'message': 'Registration successful', 'colour': 'green'})
            if roomNumber == "1":
                send_js(f'''localStorage.setItem('username', "{username}");localStorage.setItem('colour', "--light-blue");localStorage.setItem('UUID', "{UUID}");localStorage.setItem('LoggedIn', 1);window.location.href = "../"''', sid=request.sid)
            else:
                send_js(f'''localStorage.setItem('username', "{username}");localStorage.setItem('colour', "--light-blue");localStorage.setItem('UUID', "{UUID}");localStorage.setItem('LoggedIn', 1);window.location.href = "../customRoom"''', sid=request.sid)
    conn.close()

@socketio.on('joinRoom')
def joinRoom(data):
    knownRooms = fetchKnownChatrooms()
    roomToJoin =  str(data["joinRoom"])
    if not roomToJoin in knownRooms:
        if len(roomToJoin) == 5:
            init_db(roomToJoin)
            writeToKnownChatrooms(roomToJoin)


@socketio.on('login')
def login(data):
    username = data['username']
    hasSpaces = username.split(" ")
    if len(hasSpaces) > 1:
        emit('login_response', {'message': 'Username or password cannot contain spaces', 'colour': 'red'})
        return
    if len(username) > 15:
        emit('login_response', {"message": "Username has to be 15 characters or less", 'colour': 'red'})
        return
    password = data['password']
    roomNumber = str(data["roomNumber"])
    createRoom = data["createRoom"]
    knownChatrooms = fetchKnownChatrooms()
    if createRoom == "true":
        init_db(roomNumber)
        writeToKnownChatrooms(roomNumber)
    else:
        if not roomNumber in knownChatrooms:
            emit('login_response', {'message': 'Invalid room code!', 'colour': 'red'})
            return


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
            if roomNumber == "1":
                send_js(f'''localStorage.setItem("username", "{username}");localStorage.setItem("UUID", "{UUID[0]}");localStorage.setItem("LoggedIn", 1);window.location.href = "../"''', sid=request.sid)
            else:
                send_js(f'''localStorage.setItem("username", "{username}");localStorage.setItem("UUID", "{UUID[0]}");localStorage.setItem("LoggedIn", 1);window.location.href = "../customRoom"''', sid=request.sid)
            emit('login_response', {'message': 'Success!', 'colour': 'green'}) 
        else:
           emit('login_response', {'message': 'Account has not agreed to privacy policy, please contact Admin or create new account', 'colour': 'red'}) 
    else:
        emit('login_response', {'message': 'Invalid username or password', 'colour': 'red'})


#Playground for experiments

def fetchKnownChatrooms():
    f = open("knownChatrooms.txt", "r")
    knownChatrooms = f.read()
    f.close()
    return eval(knownChatrooms)

def writeToKnownChatrooms(towrite):
    f = open("knownChatrooms.txt","r")
    knownChatrooms = f.read()
    knownChatrooms = eval(knownChatrooms)
    f.close()

    f=open("knownChatrooms.txt","w")
    knownChatrooms.append(towrite)
    f.write(f"{knownChatrooms}")
    f.close()

@app.route("/customRoom")
def rooms():
    knownChatrooms = fetchKnownChatrooms()
    return render_template("customRoom.html", knownChatrooms=knownChatrooms)

@socketio.on('join')
def on_join(data):
    room = str(data['room'])
    join_room(room)
    if room == "1":
        send_js("""console.log("Your in the public room!")""", room)
    else:
        send_js(f"""console.log("Your in a custom room! roomCode: {room}")""", room)
        newMessageList = [] 
        messages = get_messages(room)
        if messages:
            for message in messages:
                if len(message) >= 4:
                    Dusername = message[0]
                    Dusername = cipher_suite.decrypt(Dusername)
                    Dusername = Dusername.decode()
                    Dmessage = message[1]
                    Dmessage = cipher_suite.decrypt(Dmessage)
                    Dmessage = Dmessage.decode()
                    Dmessage = replace_colon_items(Dmessage)
                    Ddate = message[2]
                    Dcolour = message[3]
                    print("Ye color is: ",Dcolour)
                    newMessageList.append((Dusername, Dmessage, Ddate, Dcolour))
            emit("getMessages", newMessageList)

@socketio.on('leave')
def on_leave(data):
    room = str(data['room'])
    leave_room(room)

if __name__ == "__main__":
    init_db("chatroom")
    context = ('local.pem', 'local.key')
    socketio.run(app, debug=True, host='0.0.0.0',port=443, ssl_context=context)