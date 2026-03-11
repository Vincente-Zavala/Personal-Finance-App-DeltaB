document.addEventListener('DOMContentLoaded', function() {
    const guestBtn = document.getElementById('guestLoginBtn');
    if (guestBtn) {
        guestBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const config = document.getElementById('demo-config');
            const loginForm = document.getElementById('loginForm');
            
            const usernameInput = loginForm.querySelector('input[name="username"]');
            const passwordInput = loginForm.querySelector('input[name="password"]');

            usernameInput.value = config.dataset.username; 
            passwordInput.value = config.dataset.password;

            loginForm.submit();
        });
    }
});