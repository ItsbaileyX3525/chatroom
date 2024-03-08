const container = document.getElementById('container');
const registerBtn = document.getElementById('register');
const loginBtn = document.getElementById('login');


registerBtn.addEventListener('click', ()=>{
    container.classList.add('active');
} )

loginBtn.addEventListener('click', ()=>{
    container.classList.remove('active');
} )

document.getElementById('registrationForm').onsubmit = function(event) {
    event.preventDefault();
    var username = document.getElementById('regUsername').value;
    var password = document.getElementById('regPassword').value;
    socket.emit('register', { username: username, password: password, agreed: "yes" });

}

document.getElementById('loginForm').onsubmit = function(event) {
    event.preventDefault();
    var username = document.getElementById('loginUsername').value;
    var password = document.getElementById('loginPassword').value;
    socket.emit('login', { username: username, password: password });

};

const socket = io.connect('https://' + document.domain + ":2096");

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