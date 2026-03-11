// guest_user_warning.js

document.addEventListener('DOMContentLoaded', function() {
    const isDemoUser = document.body.getAttribute('data-is-demo') === 'true';

    // Helper: Define URLs that the Demo user IS allowed to POST to
    const isWhitelisted = (url) => {
        const allowedPaths = [
            "all-transactions",
            "budget"
        ];
        const urlString = String(url);
        return allowedPaths.some(path => urlString.includes(path));
    };

    // Helper function for a consistent, nice-looking popup
    const showDemoWarning = () => {
        Swal.fire({
            title: 'Demo Mode',
            text: 'Changes are not saved in the guest preview.',
            icon: 'warning',
            background: '#191C24',
            color: '#fff',
            confirmButtonColor: '#00ab89',
            confirmButtonText: 'Confirm',
        });
    };

    if (isDemoUser) {
        // --- INTERCEPT STANDARD FORM SUBMITS ---
        document.addEventListener('submit', function(event) {
            const method = event.target.method ? event.target.method.toUpperCase() : 'GET';
            // Use 'action' here because that's what forms use
            const action = event.target.action || "";
            const isAuthAction = action.includes('login') || action.includes('logout');

            // FIX: Changed 'requestUrl' to 'action' to match the variable defined above
            if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) && !isAuthAction && !isWhitelisted(action)) {
                event.preventDefault();
                showDemoWarning();
            }
        }, true);

        // --- INTERCEPT AJAX/FETCH REQUESTS ---
        const { fetch: originalFetch } = window;
        window.fetch = async (...args) => {
            // Fetch uses 'args[0]' for the URL
            const requestUrl = args[0] instanceof Request ? args[0].url : args[0];
            const options = args[1] || {};
            const method = options.method ? options.method.toUpperCase() : 'GET';

            if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) && !isWhitelisted(requestUrl)) {
                showDemoWarning();
                
                const activeEl = document.activeElement;
                if (activeEl && activeEl.type === 'checkbox') {
                    activeEl.checked = !activeEl.checked;
                }

                return Promise.reject("Demo mode: Post blocked");
            }
            return originalFetch(...args);
        };
    }
});