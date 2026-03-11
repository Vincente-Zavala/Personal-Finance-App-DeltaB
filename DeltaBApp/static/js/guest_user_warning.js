document.addEventListener('DOMContentLoaded', function() {
    const isDemoUser = document.body.getAttribute('data-is-demo') === 'true';

    const isWhitelisted = (url) => {
        const allowedPaths = [
            "all-transactions",
            "budget"
        ];
        const urlString = String(url);
        return allowedPaths.some(path => urlString.includes(path));
    };

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
        document.addEventListener('submit', function(event) {
            const method = event.target.method ? event.target.method.toUpperCase() : 'GET';
            const action = event.target.action || "";
            const isAuthAction = action.includes('login') || action.includes('logout');

            if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) && !isAuthAction && !isWhitelisted(action)) {
                event.preventDefault();
                showDemoWarning();
            }
        }, true);

        const { fetch: originalFetch } = window;
        window.fetch = async (...args) => {
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