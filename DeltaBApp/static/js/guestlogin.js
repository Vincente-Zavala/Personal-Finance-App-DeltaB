document.addEventListener('DOMContentLoaded', function() {
    const guestBtn = document.getElementById('guestLoginBtn');
    if (guestBtn) {
        guestBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 1. Grab the bridge element
            const config = document.getElementById('demo-config');
            const loginForm = document.getElementById('loginForm');
            
            const usernameInput = loginForm.querySelector('input[name="username"]');
            const passwordInput = loginForm.querySelector('input[name="password"]');

            // 2. Pull the values from the data attributes
            usernameInput.value = config.dataset.username; 
            passwordInput.value = config.dataset.password;

            // 3. Automated submission
            loginForm.submit();
        });
    }
});