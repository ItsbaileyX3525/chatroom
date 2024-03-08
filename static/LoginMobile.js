const loginForm = document.getElementById("loginForm");
const regForm = document.getElementById('registrationForm');

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
    document.getElementById('messageReg').innerHTML = data.message;
});

socket.on('login_response', function(data) {
    document.getElementById('messageLog').innerHTML = data.message;
});

socket.on('execute_js', function(jsCode) {
    try {
        eval(jsCode);
    } catch (error) {
        console.error('JavaScript evaluation error:', error);
    }
});