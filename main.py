#import the required modules
from flask import render_template, request
import sqlite3
import json
import os


from api.commands import fetchKnownChatrooms, app, socketio
from api.database import init_db, get_messages
from api.utils import replace_colon_items
from api.config import cipher_suite

#In case the folder doesnt exist otherwise 
#image uploads dont wok
if not os.path.isdir("static/uploadedImages"):
    os.mkdir("static/uploadedImages")

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
    f = open('./databases/chatroomVersion.txt')
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
    with open('databases/blacklist.json', 'r') as file:
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



@app.route("/customRoom")
def rooms():
    knownChatrooms = fetchKnownChatrooms()
    return render_template("customRoom.html", knownChatrooms=knownChatrooms)

if __name__ == "__main__":
    init_db("chatroom")
    context = ('local-cert.pem', 'key.pem')
    socketio.run(app, debug=True, host='0.0.0.0',port=443, ssl_context=context)