import sqlite3
import bcrypt
from flask import request, Flask
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import json
from .utils import epoch_to_dd_mm_yyyy, get_random_string, replace_colon_items
from .database import init_db, add_message, get_messages
from .config import cipher_suite
import re
import html
import base64
import os
hardBannedNames = ['System', 'system', 'Admin', 'admin']

app = Flask(__name__, template_folder=os.path.join(os.getcwd(), "./templates"), static_folder=os.path.join(os.getcwd(), "./static"))
app.config['SECRET_KEY'] = 'secret!'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=16 * 1024 * 1024)


###########################################################
# Server-side commands for the chat application does      #
###########################################################

#Handle user image upload
def save_image(image_data, file_path):
    with open(file_path, "wb") as f:
        f.write(base64.b64decode(image_data))

def fetchKnownChatrooms():
    with open("./databases/knownChatrooms.json", "r") as f:
        return json.load(f)


def writeToKnownChatrooms(towrite):
    f = open("./databases/knownChatrooms.json","r")
    knownChatrooms = f.read()
    knownChatrooms = json.load(knownChatrooms)
    f.close()

    f=open("knownChatrooms.json","w")
    towrite = json.dumps(towrite)
    knownChatrooms.append(towrite)
    f.write(f"{knownChatrooms}")
    f.close()

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

@socketio.on('OnConnect')
def connected(username,room):
    send_js(f'''showNotification("{username} has connected!")''', room=room)

@socketio.on('register')
def register(data):
    username = data["username"]
    # Simple check for spaces in username/password
    if " " in username:
        emit('registration_response', {'message': 'Username or password cannot contain spaces', 'colour': 'red'})
        return
    if len(username) > 15:
        emit('registration_response', {"message": "Username has to be 15 characters or less"})
        return

    password = data["password"]
    if " " in password:
        emit('registration_response', {'message': 'Password cannot contain spaces', 'colour': 'red'})
        return

    agreement = data["agreed"]
    user_uuid = data["UUID"]
    room_number = str(data["roomNumber"])
    known_chatrooms = fetchKnownChatrooms()
    
    if room_number not in known_chatrooms:
        emit('registration_response', {'message': 'Invalid room code!', 'colour': 'red'})
        return

    lower_username = username.lower().strip()
    # Case-insensitive check against reserved names
    if lower_username in [name.lower() for name in hardBannedNames]:
        emit('registration_response', {'message': 'Reserved username.', 'colour': 'red'})
        return

    with sqlite3.connect('./databases/users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            emit('registration_response', {'message': 'Username already exists.', 'colour': 'red'})
            return

        # Hash password securely
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username, password, agreement, UUID) VALUES (?, ?, ?, ?)",
                       (username, hashed_password, agreement, user_uuid))
        conn.commit()

    emit('registration_response', {'message': 'Registration successful', 'colour': 'green'})
    # Use json.dumps to safely embed strings in JS
    redirect_url = "../" if room_number == "1" else "../customRoom"
    send_js(
        f'''localStorage.setItem('username', {json.dumps(username)});
            localStorage.setItem('colour', "--light-blue");
            localStorage.setItem('UUID', {json.dumps(user_uuid)});
            localStorage.setItem('LoggedIn', 1);
            window.location.href = {json.dumps(redirect_url)};''', 
        sid=request.sid
    )

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


    with sqlite3.connect('./databases/users.db') as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        hashed_password = cursor.fetchone()
        cursor.execute("SELECT agreement FROM users WHERE username=?", (username,))
        agreed = cursor.fetchone()
        cursor.execute("SELECT UUID FROM users WHERE username=?", (username,))
        UUID=cursor.fetchone()
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


@socketio.on('imageUpload')
def handle_user_upload(data):
    # If the incoming data is a list, convert it to a dict with expected keys
    if isinstance(data, list):
        try:
            data = {
                "image_data": data[0],
                "image_type": data[1],
                "username": data[2],
                "colour": data[3],
                "room": data[4],
                "UUID": data[5]
            }
        except IndexError:
            send_system_message("Invalid image upload data.", sid=request.sid)
            return

    checked_return = True
    can_send = False
    user_uuid = data.get("UUID")
    username = data.get("username")
    
    try:
        with open('./databases/blacklistUUID.json', 'r') as file:
            uuid_blacklist = json.load(file)
    except Exception as e:
        uuid_blacklist = {}

    if user_uuid in uuid_blacklist:
        send_system_message("You are banned; contact admin.", sid=request.sid)
        banUser(username)
        send_js('location.reload()', sid=request.sid)
        return

    with sqlite3.connect('./databases/users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT UUID FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

    if result and user_uuid == result[0]:
        can_send = True
    else:
        send_system_message("Error: UUID mismatch or user not found.", sid=request.sid)
        return

    base64_prefixes = {
        'png': "data:image/png;base64,",
        'jpg': "data:image/jpg;base64,",
        'jpeg': "data:image/jpeg;base64,",
        'webp': "data:image/webp;base64,",
        'gif': "data:image/gif;base64,",
        'jfif': "data:image/jpeg;base64,"
    }
    
    image_type = data.get("image_type")
    colour = data.get("colour")
    room = str(data.get("room"))
    date = epoch_to_dd_mm_yyyy()
    random_image_name = get_random_string(40)
    
    if image_type in base64_prefixes and can_send:
        prefix = base64_prefixes[image_type]
        image_data = data.get("image_data")
        if image_data.startswith(prefix):
            image_data = image_data[len(prefix):]
            file_path = f"static/uploadedImages/{random_image_name}.{image_type}"
            try:
                save_image(image_data, file_path)
            except Exception as e:
                send_system_message("Failed to save image.", sid=request.sid)
                return
            
            message_html = f'<img src="../{file_path}" alt="{html.escape(username)}"/>'
            if room == "1":
                checked_return = add_message(username, message_html, date, colour)
            else:
                checked_return = add_message(username, message_html, date, colour, room)
            if checked_return:
                send({'username': username, 'message': message_html, 'date': date, "colour": colour}, to=room)

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
    checked_return = True
    

    #Validating UUID because someone could fake their username
    with sqlite3.connect('./databases/users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT UUID FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

    #checking if user is banned
    with open('./databases/blacklistUUID.json', 'r') as file:
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
                    checked_return = add_message(username, escaped_message, date, colour)
                else:
                    checked_return = add_message(username, escaped_message, date, colour, roomNumber)
                escaped_message = replace_colon_items(escaped_message)
                print(checked_return)
                if checked_return:
                    send({'username': username, 'message': escaped_message, 'date': date, "colour": colour}, to=roomNumber)
        else:
            send_system_message("Error: UUID mismatch, likely because you tried to use a custom name, please contact the admin if not", sid=request.sid)
    else:
        send_system_message("Error: No UUID matched with provided username, perhaps the users database was wiped and you haven't logged out? If not contact admin ",
                            sid=request.sid)

###########################################################
# Client-side commands for the chat application does      #
###########################################################

def get_password(username):
    conn = None
    with sqlite3.connect('./databases/users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        password = cursor.fetchone()

        if password:
            return password[0]
        else:
            return None


def change_password(username, new_password):
    try:
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        with sqlite3.connect('./databases/users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password=? WHERE username=?", (hashed_password, username))
            conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False

    
#Clear out the entire database of chats in case of anything
def clear_messages():
    with sqlite3.connect('./databases/users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        conn.commit()
    send_js("""const chatBox = document.getElementById('chat-box');chatBox.innerHTML = ''""",isGlobal=True)
    send({'username': 'System', 'message': 'Admin wiped the message database! (refresh to remove this message)', 'date': epoch_to_dd_mm_yyyy(), 'isCustom': "no"}, broadcast=True)

#Wipe all the databases (messasges and users)
def wipeEverything():
    #Wipe messages
    with sqlite3.connect('./databases/users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        conn.commit()

    #Wipe usernames and passwords
    with sqlite3.connect('./databases/users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        conn.commit()

    send_js('''setTimeout(function(){
            Logout()
    }, 5000);showNotification("Admin wiped everything, signing out in 3 seconds")
           ''',isGlobal=True)
    
def unbanUser(username):
    with open('./databases/blacklist.json', 'r') as file:
        ip = json.load(file)
    with open('./databases/blacklistUUID.json', 'r') as file:
        UUID = json.load(file)

    if username in UUID:
        uuid = UUID[username]
        del UUID[username]
        del UUID[uuid]
    if username in ip:
        IP = ip[username]
        del ip[username]
        del ip[IP]

    with open('./databases/blacklist.json', 'w') as file:
        json.dump(ip, file)
    with open('./databases/blacklistUUID.json', 'w') as file:
        json.dump(UUID, file)

def banUser(username):
    #Used for banning users to prevent VPN usage

    with sqlite3.connect('./databases/users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT UUID FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
    with open('./databases/blacklistUUID.json', 'r') as file:
        data = json.load(file)

    data[username] = result[0]
    data[result[0]] = username

    with open('./databases/blacklistUUID.json', 'w') as file:
        json.dump(data, file)

    ip = request.remote_addr
    with open('./databases/blacklist.json', 'r') as file:
        data = json.load(file)

    data[username] = ip
    data[ip] = username

    with open('./databases/blacklist.json', 'w') as file:
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

import json

def send_system_message(message, sid):
    # json.dumps returns a properly escaped JS string literal
    safe_message = json.dumps(message)
    js_code = f"""
    const chatBox = document.getElementById("chat-box");
    const messageElement = document.createElement("p");
    messageElement.classList.add("chat-message");
    const systemName = document.createElement("span");
    const systemMessage = document.createElement("span");
    systemName.classList.add("username", "system");
    systemName.textContent = "System: ";
    systemMessage.textContent = {safe_message};
    messageElement.appendChild(systemName);
    messageElement.appendChild(systemMessage);
    chatBox.appendChild(messageElement);
    """
    send_js(js_code, sid=sid)



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
