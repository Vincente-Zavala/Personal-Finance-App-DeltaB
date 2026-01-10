document.addEventListener("DOMContentLoaded", () => {
    fetch(TRANSACTIONS_API_URL, {
        credentials: "same-origin"
    })
    .then(res => {
        if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
        }
        return res.json();
    })
    .then(data => {
        const tbody = document.getElementById("allTransactionsBody");
        tbody.innerHTML = "";

        data.transactions.forEach(tx => {
            const tr = document.createElement("tr");
            tr.classList.add("transaction-row");
            tr.dataset.type = tx.type;

            tr.innerHTML = `
                <td class="editcol" hidden></td>
                <td>${tx.date}</td>
                <td class="category-cell">${tx.type}</td>
                <td>${tx.category}</td>
                <td class="text-truncate" style="max-width:400px;" title="{{ transaction.note }}">${tx.note}</td>
                <td>${tx.account}</td>
                <td class="text-end fw-semibold text-primary">$${tx.amount}</td>
            `;

            tbody.appendChild(tr);
        });
    })
    .catch(err => {
        console.error("Transaction load failed:", err);
        document.getElementById("loadingRow").innerText =
            "Failed to load transactions";
    });
});
