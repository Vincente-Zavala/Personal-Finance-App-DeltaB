// Fetches balances from server and calls updateAccountBalances
function fetchAccountBalances() {
    fetch("/updateaccounts/")  // make sure this URL matches your urls.py
        .then(res => res.json())
        .then(data => {
            if (data.status === "ok" && data.balances) {
                updateAccountBalances(data.balances);
            }
        })
        .catch(err => console.error("Error fetching balances:", err));
}
