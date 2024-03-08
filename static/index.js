//Webpage stuff (not on server)
userFont = localStorage.getItem('font') || 'Normal'
document.body.style.fontFamily = userFont

//Server stuff (on server)
const socket = io.connect('https://' + document.domain + ":443");
const chatBox = document.getElementById("chat-box");
socket.on('message', function(data) {
    const messageElement = document.createElement("p");
    messageElement.innerHTML = `<strong style="color: rgb(198, 201, 204);">${data.username}:</strong> <span style="color: rgb(198, 201, 204);">${data.message}</span><span style="color: rgb(198, 201, 204);translate:transformY(20px); font-size: 12px;opacity:.2">${data.date}</span>`;
    chatBox.appendChild(messageElement);

    // Scroll to the bottom of the chat box to show the latest message
    chatBox.scrollTop = chatBox.scrollHeight;
});

const messageInput = document.getElementById('messageInput')
const sendbutton = document.getElementById("sendButton")
const setUsername = localStorage.getItem("username");
const UUID = localStorage.getItem('UUID')
const loggedin = localStorage.getItem('LoggedIn');

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
        eval(jsCode);
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
    messageElement.classList.add("chat-message");
    messageElement.innerHTML = `<span class="username system">System:</span><span class="message"> welcome ${setUsername}, use /help for a list of commands.</span>`;chatBox.appendChild(messageElement);
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