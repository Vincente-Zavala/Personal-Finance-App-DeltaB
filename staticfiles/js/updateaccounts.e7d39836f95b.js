function updateAccountBalances(balances) {
    for (const [accountId, balance] of Object.entries(balances)) {
        const elem = document.querySelector(`.account-item[data-account-id='${accountId}'] .account-balance`);
        if (elem) elem.textContent = `$${balance.toFixed(2)}`;
    }
}