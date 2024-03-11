//Webpage stuff (not on server)
userFont = localStorage.getItem('font') || 'Normal'
document.documentElement.style.setProperty('--font-family:', userFont);

//Server stuff (on server)
const socket = io.connect('https://' + document.domain + ":443");
const chatBox = document.getElementById("chat-box");
const messageInput = document.getElementById('messageInput')
const sendbutton = document.getElementById("sendButton")
const setUsername = localStorage.getItem("username");
const UUID = localStorage.getItem('UUID')
const loggedin = localStorage.getItem('LoggedIn');

socket.on('message', function(data) {
    const messageElement = document.createElement("p");
    const UsernameDisplay = document.createElement("span");
    const UsernameMessage = document.createElement("span");
    const date = document.createElement("span");
    const chatBox = document.getElementById("chat-box");
    messageElement.classList.add("chat-message");
    UsernameDisplay.classList.add("username");
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

cmds = {
    "/help": show_help,
    "/emojis": get_emojis,
    "/emojiList": emoji_list,
    "/font": change_font,
    "/fontList": font_list,
    "/playList": sound_list,
}


// Submit the form when Enter is pressed in the message input field
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
        socket.emit('message', {'username': username, 'message': message, 'UUID': UUID});
        messageInput.value = "";}
}});



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
    socket.emit('message', {'username': username, 'message': message, 'UUID': UUID});
    messageInput.value = "";}
})
socket.on('execute_js', function(jsCode) {
    try {
        console.log(jsCode)
        eval(jsCode)
        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (error) {
        console.error('JavaScript evaluation error:', error);
    }
});
function showNotification(message) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.style.display = 'block';

    setTimeout(function() {
        notification.style.display = 'none';
    }, 3000);
}
function Logout(){
    localStorage.clear()
    window.location.href = '../Login'
}
addEventListener("DOMContentLoaded", (event) => {
    socket.emit('OnConnect', setUsername)
    send_system_message(`Welcome ${setUsername}, use /help for a list of commands.`)
});
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
discordNotifaction = new Audio('static/noti.ogg')
function notifyUser(){
    if (!document.hasFocus()) {
        discordNotifaction.duration = 0;
        discordNotifaction.play();
}}


function playAudio(type,url=""){
    if (type != "custom"){
        customAudios[type].play()}
    else {
        console.log(url)
        new Audio(url).play()
    }
}
function changeFont(type){
    const root = document.querySelector(':root');
    root.style.setProperty('--font-family', type);
}