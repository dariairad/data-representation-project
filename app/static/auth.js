// Handle Registration Form Submission
document.getElementById('register-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;

    fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Registration failed');
        }
        return response.json();
    })
    .then(data => {
        alert(data.message);
        window.location.href = '/auth'; // Redirect to the auth page
    })
    .catch(error => {
        console.error('Error:', error);
        alert("Registration failed. Please try again.");
    });
});

// Handle Login Form Submission
document.getElementById('login-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Login failed');
        }
        return response.json();
    })
    .then(data => {
        if (data.access_token) {
            // Store the access token and redirect to index page
            localStorage.setItem('jwtToken', data.access_token);
            window.location.href = '/'; // Redirect to the index page
        } else {
            alert(data.msg);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("Login failed. Please check your credentials.");
    });
});
