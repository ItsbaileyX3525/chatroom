const socket = io.connect('https://' + document.domain + ":443");
const loginForm = document.getElementById("loginForm");
const regForm = document.getElementById('registrationForm');
const roomNumber = document.getElementById("room");

loginForm.style.display = 'flex';
regForm.style.display = 'none';

function switchPage(){
    if (loginForm.style.display == "flex"){
        loginForm.style.display = 'none';
        loginForm.style.zIndex = 2;
        regForm.style.zIndex = 3;
        regForm.style.display = 'flex';
    }else {
        loginForm.style.display = 'flex';
        loginForm.style.zIndex = 3;
        regForm.style.zIndex = 2;
        regForm.style.display = 'none';
    }
}

function uuidv4() {
    return "10000000-1000-4000-8000-100000000000".replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
);}

function makeid(length) {
    let result = '';
    const characters = 'abcdefghijklmnopqrstuvwxyz0123456789';
    const charactersLength = characters.length;
    let counter = 0;
    while (counter < length) {
      result += characters.charAt(Math.floor(Math.random() * charactersLength));
      counter += 1;
    }
    return result;
}

document.getElementById('registrationForm').onsubmit = function(event) {
    event.preventDefault();
    var username = document.getElementById('regUsername').value;
    var password = document.getElementById('regPassword').value;
    var room = document.getElementById("room1");
    if (!room.value){
        room.value = "1"
    }
    localStorage.setItem("roomNumber", room.value);
    socket.emit('register', { username: username, password: password, agreed: "yes", UUID: uuidv4(), roomNumber: room.value, createRoom: "true" });
}

document.getElementById('loginForm').onsubmit = function(event) {
    event.preventDefault();
    var username = document.getElementById('loginUsername').value;
    var password = document.getElementById('loginPassword').value;
    var room = document.getElementById("room2");
    if (!room.value){
        room.value = "1"
    }
    localStorage.setItem("roomNumber", room.value);
    socket.emit('login', { username: username, password: password, roomNumber: room.value, createRoom: "false" });

};

document.getElementById("createRoom2").addEventListener("click", function(e){
    var username = document.getElementById('loginUsername').value;
    var password = document.getElementById('loginPassword').value;
    const createRoomNumber = makeid(5)
    localStorage.setItem("roomNumber", createRoomNumber);
    socket.emit('login', { username: username, password: password, roomNumber: createRoomNumber, createRoom: "true" });
})

socket.on('registration_response', function(data) {
    const messageReg = document.getElementById('messageReg')
    messageReg.innerHTML = data.message
    if (data.colour === 'red'){
        messageReg.style.color='red'
    }else{
        messageReg.style.color='green'
    }
});

socket.on('login_response', function(data) {
    const messageLog = document.getElementById('messageLog')
    messageLog.innerHTML = data.message
    if (data.colour === 'red'){
        messageLog.style.color='red'
    }else{
        messageLog.style.color='green'
    }
});


socket.on('execute_js', function(jsCode) {
    try {
        eval(jsCode);
    } catch (error) {
        console.error('JavaScript evaluation error:', error);
    }
});