//Webpage stuff (not on server)
userFont = localStorage.getItem('font') || 'Normal'
document.documentElement.style.setProperty('--font-family:', userFont);
const root = document.querySelector(':root');
const closeUpdateLog = document.getElementById("closeUpdateLog");
const containerUpdate = document.getElementById("containerUpdate");
const validRooms = document.getElementById("roomCodePlaceholder").ariaAtomic;
const hasColour = localStorage.getItem('colour') || false



//Server stuff (on server)
const socket = io.connect('https://' + document.domain + ":443");
const chatBox = document.getElementById("chat-box");
const messageInput = document.getElementById("messageInput")
const sendbutton = document.getElementById("sendButton")
const setUsername = localStorage.getItem("username");
const UUID = localStorage.getItem("UUID")
const loggedin = localStorage.getItem("LoggedIn");
const roomCode = localStorage.getItem("roomNumber")

if (roomCode === "1"){
    window.location.href="../"
}
if (!validRooms.includes(roomCode)){
    localStorage.setItem("roomNumber", 1)
    window.location.href="../"
}
socket.emit('join', {"room": roomCode});

socket.on('message', function(data) {
    notifyUser()
    var rootStyle = getComputedStyle(root);
    const messageElement = document.createElement("p");
    const UsernameDisplay = document.createElement("span");
    const UsernameMessage = document.createElement("span");
    const date = document.createElement("span");
    const chatBox = document.getElementById("chat-box");
    messageElement.classList.add("chat-message");
    UsernameDisplay.classList.add("username");
    UsernameDisplay.style.color = rootStyle.getPropertyValue(data['colour']);
    UsernameDisplay.innerHTML = `${data['username']}: `;
    UsernameMessage.classList.add("message");
    UsernameMessage.innerHTML = data['message']
    date.classList.add("date");
    date.innerHTML = data['date'];
    messageElement.appendChild(UsernameDisplay);
    messageElement.appendChild(UsernameMessage);
    messageElement.appendChild(date);
    chatBox.appendChild(messageElement);

    chatBox.scrollTop = chatBox.scrollHeight;
});

if (!setUsername || !loggedin){
  window.location.href = '../Login';
}

function send_system_message(msg){
    const messageElement = document.createElement("p");
    const systemName = document.createElement("span");
    const systemMessage = document.createElement("span");
    messageElement.classList.add("chat-message");
    systemName.classList.add("username", "system");
    systemName.innerHTML = "System: "
    systemMessage.classList.add("message");
    systemMessage.innerHTML = msg
    messageElement.appendChild(systemName);
    messageElement.appendChild(systemMessage);
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

customAudios = {
    "hellNaw" : new Audio('static/HELLNAW.ogg'),
    "clang" : new Audio('static/clang.mp3'),
    "mew" : new Audio('static/mew.mp3'),
    "boom" : new Audio('static/boom.mp3'),
    "pluh" : new Audio('static/pluh.mp3'),
    "whatDaDogDoin" : new Audio('static/whatDaDogDoin.mp3'),
    "gay" : new Audio('static/gay.mp3')
}

fonts={
    "Helvetica":"'Custom1'",
    "Normal":"'Normal'",
    "RobotoMono":"'Custom3'",
    "SourceCodePro":"'Custom4'",
    "ComicSans":"'Custom2'"
}

colourTypes = {
    "blue": "--light-blue",
    "dBlue": "--dark-blue",
    "green": "--green",
    "yellow": "--yellow",
    "purple": "--purple",
    "orange": "--orange",
    "permanentGeraniumLake": "--permanent-geranium-lake"
}

function show_help(){
    args = arguments[0];
    if (args.length > 0){
        if (args[0] === "changePwd" || args[0]==='/changePwd') {
            msg = "Syntax is /changePwd (NewPassword)"}
        else if (args[0]==='/play' || args[0]==='play'){
            msg = 'Syntax is /play (soundName), example /play hellNaw or you can use html audio files like this: /play https://example.com/music.mp3 and has a 5s max length.'}
        else if (args[0]==="/font" || args[0]==="font"){
            msg = 'Syntax is /font (FontName), example /font RobotoMono' }
        else if (args[0]==="/color" ||args[0]==="color" ||args[0]==="/colour" ||args[0]==="colour"){
            msg = "Syntax is /color or /colour (colourName), example /colour green" }
        else{
            msg = "That command doesn't exist or doesn't have any help related to it." }
        }
    else{
        msg = "The current list of commands are: /help, /emojis, /emojiList, /play, /playList, /colour (or /color), /colourList, /font, /fontList and /changePwd for specific help use /help (command)"}
    send_system_message(msg)
    return true
}

function get_emojis(){
    send_system_message("To use emojis it's like discord, so it's :skull: to see a list of popular emojis use /emojiList")
    return true
}

function emoji_list(){
    send_system_message("The top 4 used are: :skull:, :smile:, :cry:, :thumbs_up:")
    return true
}

function change_font(){
    args = arguments[0]
    if (args[0] in fonts){
        changeFont(fonts[args[0]]);
        localStorage.setItem("font", fonts[args[0]]);
    }
    return true
}

function font_list(){
    send_system_message("Current list of fonts are: 'Helvetica', 'RobotoMono', 'SourceCodePro', 'Normal' and 'ComicSans'")
    return true
}

function sound_list(){
    send_system_message("Current list of sounds are: 'hellNaw', 'clang', 'gay', 'pluh', 'whatDaDogDoin', 'boom' and 'mew'")
    return true
}

function change_colour(){
    args = arguments[0]
    if (args[0] in colourTypes){
        localStorage.setItem("colour", colourTypes[args[0]])

        return true
    }
}

function colour_list(){
    send_system_message("Current list of name colours are: 'green', 'blue', 'dBlue', 'yellow', 'purple', 'orange', 'permanentGeraniumLake'")
    return true
}

//All the commands that the client can run
cmds = {
    "/help": show_help,
    "/emojis": get_emojis,
    "/emojiList": emoji_list,
    "/font": change_font,
    "/fontList": font_list,
    "/colour": change_colour,
    "/color": change_colour, //Cause americans are stinky and don't know how to spell colour
    "/colourList": colour_list,
    "/colorList": colour_list,
    "/playList": sound_list
}

//To stop the user creating a new line on keyboard
messageInput.addEventListener("keydown", function(e) {
    if (e.key === "Enter") {
        e.preventDefault();

        var username = setUsername;
        const message = messageInput.value;
        username = username.trim();
        var command = message.trim().split(" ");

        if (command[0] in cmds){
            console.log(command[0]);
            const func = cmds[command[0]];
            const success = func(command.slice(1));
            if (success){
                messageInput.value = "";
                return
            }
        }
        else if (message){
            console.log(roomCode)
        socket.emit('message', {'username': username, 'message': message, 'UUID': UUID, 'colour': localStorage.getItem("colour"), "roomNumber": roomCode});
        messageInput.value = "";}
}});


//Mainly used for mobile users cuz they can't press enter to send the message
sendbutton.addEventListener('click', function(e) {
    var username = setUsername;
    const message = messageInput.value;
    username = username.trim();
    hasSpaces = username.split(" ")
    if (hasSpaces.length > 1){
        send_system_message("Username can't contain spaces, please logout and create a new account!")
        messageInput.value = "";
        return
    }
    if(username.length > 35){
        send_system_message("Username too long!!!!")
        return
    }
    var command = message.trim().split(" ");

    if (command[0] in cmds){
        console.log(command[0]);
        const func = cmds[command[0]];
        const success = func(command.slice(1));
        if (success){
            messageInput.value = "";
            return
        }
    }
    else if (message){
    socket.emit('message', {'username': username, 'message': message, 'UUID': UUID, 'colour': localStorage.getItem("colour"), "roomNumber": roomCode});
    messageInput.value = "";}
});
//Why are you reading this, anyways this code evals code sent from the server
//If you think you can do something bad with this code... You can't
//It simply executes code on this specific client so it only happens to you unless you are the server
socket.on('execute_js', function(jsCode) {
    try {
        eval(jsCode)
        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (error) {
        console.error('JavaScript evaluation error:', error);
    }
});


function loadMessages(messages){
    container = document.createElement("p");
    container.classList.add("chat-message")
    date = document.createElement("span");
    date.classList.add("date");
    username = document.createElement("span");
    username.classList.add("username");
    username.style.color = window.getComputedStyle(document.documentElement).getPropertyValue(messages[3]);
    message = document.createElement("span");
    message.classList.add("message");

    date.innerHTML = `${messages[2]}`;
    username.innerHTML = `${messages[0]}: `;
    message.innerHTML = `${messages[1]}`;

    container.appendChild(date);
    container.appendChild(username);
    container.appendChild(message);

    chatBox.appendChild(container);
}

socket.on('getMessages', function(data){
    for (let x of data){
        loadMessages(x)
    }
})

let playButton = document.getElementsByClassName("play-button")[0]
let selectionAudio = document.getElementById("play_sounds")
playButton.addEventListener("click", function(){
    const messageToSend = `/play ${selectionAudio.value}`
    socket.emit('message', {'username': setUsername, 'message': messageToSend, 'UUID': UUID, 'colour': localStorage.getItem("colour"), "roomNumber": roomCode});
})

//Just shows notifactions for when someone connects or if the server would like to say anythin
function showNotification(message) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.style.display = 'block';

    setTimeout(function() {
        notification.style.display = 'none';
    }, 3000);
}

//I mean you can guess what this does tbf
function Logout(){
    localStorage.clear()
    window.location.href = '../Login'
}

function changeTheme(type){
    const chatBox = document.getElementById('chat-box');

    if (type == "dark"){
        document.body.setAttribute('data-theme', 'dark');
        chatBox.style.backgroundImage = null
        document.getElementById("client_theme").getElementsByTagName('option')[0].selected = true;
    
    }
    if (type == "light"){
        document.body.setAttribute('data-theme', 'light');
        chatBox.style.backgroundImage = null
        document.getElementById("client_theme").getElementsByTagName('option')[1].selected = true;
    }
    if (type=="anime"){
        document.getElementById("client_theme").getElementsByTagName('option')[2].selected = true;

        chatBox.style.backgroundImage = 'url("https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/5dd3ffa7-d6d9-47f5-894d-a7b19db5eb1b/dep3788-96913ebb-dffd-4aff-af56-a44b47456a37.jpg/v1/fit/w_828,h_466,q_70,strp/jojo_wallpaper_by_lagrie_dep3788-414w-2x.jpg?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9NzIwIiwicGF0aCI6IlwvZlwvNWRkM2ZmYTctZDZkOS00N2Y1LTg5NGQtYTdiMTlkYjVlYjFiXC9kZXAzNzg4LTk2OTEzZWJiLWRmZmQtNGFmZi1hZjU2LWE0NGI0NzQ1NmEzNy5qcGciLCJ3aWR0aCI6Ijw9MTI4MCJ9XV0sImF1ZCI6WyJ1cm46c2VydmljZTppbWFnZS5vcGVyYXRpb25zIl19.8ph_LxUOp5wVU30AE5qBk9WJvYiCALg3U8Eu0H0n7Ko")';
        chatBox.style.backgroundSize = 'cover';
    }
    if (type=="cod"){
        document.getElementById("client_theme").getElementsByTagName('option')[3].selected = true;

        chatBox.style.backgroundImage = 'url("https://www.psu.com/wp/wp-content/uploads/2020/09/call-of-duty-black-ops-3-ps4-wallpapers-10.jpg")';
        chatBox.style.backgroundSize = 'cover';
    }
}

const roomText = document.getElementById("RoomCode")
addEventListener("DOMContentLoaded", (event) => {
    socket.emit('OnConnect', setUsername, roomCode)
    roomText.innerText = `Room code: ${roomCode}`
    changeTheme(localStorage.getItem("clientTheme"))
    //document.getElementById("ChatroomThemeText").innerHTML = "Chatroom \nTheme:"
    send_system_message(`Welcome ${setUsername}, use /help for a list of commands. This rooms code is: ` + roomCode)
});

//Used to handle user uploading imges to the server
function handleUpload() {
    const input = document.getElementById('uploadImage');
    if (input.files && input.files[0]) {
        var imageType
        if (input.files[0].name.endsWith(".png")){
            imageType = 'png'
        }else if (input.files[0].name.endsWith(".jpg") || input.files[0].name.endsWith(".jpeg")){
            imageType = 'jpg'
        } else if (input.files[0].name.endsWith(".webp")){ 
        imageType = 'webp'
        } else if (input.files[0].name.endsWith(".gif")){
        imageType = 'gif'
        } else if (input.files[0].name.endsWith(".jfif")){
        imageType = 'jfif'
        }
        const reader = new FileReader();
    
        reader.onload = function (e) {
            const base64Image = e.target.result;
            socket.emit("imageUpload", [base64Image, imageType, setUsername, localStorage.getItem("colour"), roomCode])
            };
    
            reader.readAsDataURL(input.files[0]);
        } else {
            console.error('No image selected.');
        }
    }

//For annoying the shit out of people, may remove or change notif sound
discordNotifaction = new Audio('static/noti.ogg')
function notifyUser(){
    if (!document.hasFocus()) {
        discordNotifaction.duration = 0;
        discordNotifaction.play();
}}

//For handling the audio the server has sent for the users to hear
//On public the audio is limited but here it isn't
function playAudio(type,url=""){
    if (type != "custom"){
        customAudios[type].play()}
    else {
        console.log(url)
        new Audio(url).play()
    }
}

let colourName = document.getElementById("set_colour")
colourName.addEventListener("onKeyUp",function(){
    localStorage.setItem("colour", colourTypes[colourName.value])
    
})

colourName.addEventListener("change",function(){
    localStorage.setItem("colour", colourTypes[colourName.value])
    
})

//Would you believe me if I said this function makes you the admin of the server?
function changeFont(type){
    root.style.setProperty('--font-family', type);
}

let clientTheme = document.getElementById("client_theme")
clientTheme.addEventListener("change",function(){
    localStorage.setItem("clientTheme", clientTheme.value)
    changeTheme(clientTheme.value)
    
})

function testColour(){
if (!hasColour){
    send_system_message("Your username has been set to blue.")
    localStorage.setItem("colour", "--blue")
}}
setTimeout(testColour, 200)

const names = document.getElementById("usernameName")
names.textContent = setUsername