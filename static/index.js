//Webpage stuff (not on server)
userFont = localStorage.getItem('font') || 'Normal'
document.documentElement.style.setProperty('--font-family:', userFont);
const root = document.querySelector(':root');
const closeUpdateLog = document.getElementById("closeUpdateLog");
const containerUpdate = document.getElementById("containerUpdate");
const seenUpdate = localStorage.getItem("ClosedUpdates1")

if(seenUpdate === "true"){
    containerUpdate.style.display = "none"
}

closeUpdateLog.addEventListener("click", function(e){
    containerUpdate.style.display = "none"
    localStorage.setItem("ClosedUpdates1", true)
})

//Server stuff (on server)
const socket = io.connect('https://' + document.domain + ":443");
const chatBox = document.getElementById("chat-box");
const messageInput = document.getElementById("messageInput")
const sendbutton = document.getElementById("sendButton")
const setUsername = localStorage.getItem("username");
const UUID = localStorage.getItem("UUID")
const loggedin = localStorage.getItem("LoggedIn");
const roomCode = localStorage.getItem("roomNumber")
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
    "Dblue": "--dark-blue",
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
            msg = 'Syntax is /play (soundName), example /play hellNaw'}
        else if (args[0]==="/font" || args[0]==="font"){
            msg = 'Syntax is /font (FontName), example /font RobotoMono' }
        else{
            msg = "That command doesn't exist or doesn't have any help related to it." }}
    else{
        msg = "The current list of commands are: /help, /emojis, /emojiList, /play, /playList, /font, /fontList and /changePwd for specific help use /help (command)"}
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

//All the commands that the client can run
cmds = {
    "/help": show_help,
    "/emojis": get_emojis,
    "/emojiList": emoji_list,
    "/font": change_font,
    "/fontList": font_list,
    "/colour": change_colour,
    "/color": change_colour, //Cause americans are stinky and don't know how to spell colour
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
        socket.emit('message', {'username': username, 'message': message, 'UUID': UUID, 'colour': localStorage.getItem("colour"), "roomNumber": roomCode});
        messageInput.value = "";}
}});


//Mainly used for mobile users cuz they can't press enter to send the message
sendbutton.addEventListener('click', function(e) {
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
    socket.emit('message', {'username': username, 'message': message, 'UUID': UUID, 'colour': localStorage.getItem("colour"), "roomNumber": roomCode});
    messageInput.value = "";}
})

//Why are you reading this, anyways this code evals code sent from the server
socket.on('execute_js', function(jsCode) {
    try {
        console.log(jsCode)
        eval(jsCode)
        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (error) {
        console.error('JavaScript evaluation error:', error);
    }
});

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
addEventListener("DOMContentLoaded", (event) => {
    socket.emit('OnConnect', setUsername)
    send_system_message(`Welcome ${setUsername}, use /help for a list of commands.`)
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
    }
    const reader = new FileReader();

    reader.onload = function (e) {
        const base64Image = e.target.result;
        socket.emit("imageUpload", [base64Image, imageType, setUsername])
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
function playAudio(type,url=""){
    if (type != "custom"){
        customAudios[type].play()}
    else {
        console.log(url)
        new Audio(url).play()
    }
}

//Would you believe me if I said this function makes you the admin of the server?
function changeFont(type){
    root.style.setProperty('--font-family', type);
}