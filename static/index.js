//Webpage stuff (not on server)
userFont = localStorage.getItem('font') || 'Normal'
document.body.style.fontFamily = userFont

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

// Submit the form when Enter is pressed in the message input field
messageInput.addEventListener("keydown", function(event) {
    if ((event.key === "Enter" && !event.shiftKey) || event.keyCode === 13) {
        event.preventDefault();

        var username = setUsername;
        const message = messageInput.value;
        username = username.trim()
    if (message && ! username){
        alert("You need a username.")
    } else if (!bannedNames.includes(username) && username && message && username != 'Admin' && username != 'admin'){
        socket.emit('message', {'username': username, 'message': message, 'UUID': UUID});
        messageInput.value = "";
    } if (bannedNames.includes(username)){
        alert("This is a reserved name, sorry.")
    }
    }
});

bannedNames = ['System', 'system']

sendbutton.addEventListener('click', function(event) {
    var username = setUsername;
    const message = messageInput.value;
    username = username.trim()

    if (message && ! username){
        alert("You need a username.")
    } else if (!bannedNames.includes(username) && username && message && username != 'Admin' && username != 'admin'){
        socket.emit('message', {'username': username, 'message': message, 'UUID': UUID});
        messageInput.value = "";
    } if (bannedNames.includes(username)){
    alert("This is a reserved name, sorry.")
}
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
    const messageElement = document.createElement("p");
    const systemName = document.createElement("span");
    const systemMessage = document.createElement("span");
    messageElement.classList.add("chat-message");
    systemName.classList.add("username", "system");
    systemName.innerHTML = "System: "
    systemMessage.classList.add("message");
    systemMessage.innerHTML = `Welcome ${setUsername}, use /help for a list of commands.`
    messageElement.appendChild(systemName);
    messageElement.appendChild(systemMessage);
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
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

//All the custom sounds, idk
customAudios = {
    "hellNaw" : new Audio('static/HELLNAW.ogg'),
    "clang" : new Audio('static/clang.mp3'),
    "mew" : new Audio('static/mew.mp3'),
    "boom" : new Audio('static/boom.mp3'),
    "pluh" : new Audio('static/pluh.mp3'),
    "whatDaDogDoin" : new Audio('static/whatDaDogDoin.mp3'),
    "gay" : new Audio('static/gay.mp3')
}

function playAudio(type,url=""){
    if (type != "custom"){
        customAudios[type].play()}
    else {
        console.log(url)
        new Audio(url).play()
    }
}
function changeFont(type,url){
    if (type !="custom"){
        document.body.style.fontFamily = type
    }
}
socket.on('userToBan', function(data){
    if (data == setUsername){
        socket.emit("handleIP")
}})