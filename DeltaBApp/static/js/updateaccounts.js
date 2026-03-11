function updateAccountBalances(balances) {
    console.log("Within updateAccountBalances");
    for (const [accountId, balance] of Object.entries(balances)) {
        const elem = document.querySelector(`.account-item[data-account-id='${accountId}'] .account-balance`);
        if (elem) elem.textContent = `$${balance.toFixed(2)}`;
    }
}

function fetchAccountBalances() {
    fetch("/updateaccounts/")
        .then(res => res.json())
        .then(data => {
            if (data.status === "ok" && data.balances) {
                updateAccountBalances(data.balances);
            }
        })
        .catch(err => console.error("Error fetching balances:", err));
}
