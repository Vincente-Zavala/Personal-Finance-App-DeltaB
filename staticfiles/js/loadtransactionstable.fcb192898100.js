document.addEventListener("DOMContentLoaded", () => {
    fetch("/api/transactions/")
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById("allTransactionsBody");
            tbody.innerHTML = "";

            data.transactions.forEach(tx => {
                const tr = document.createElement("tr");
                tr.classList.add("transaction-row");
                tr.dataset.type = tx.category_type;

                tr.innerHTML = `
                    <td class="editcol" hidden>
                        <input type="checkbox" value="${tx.id}">
                    </td>
                    <td>${tx.date}</td>
                    <td class="category-cell">${tx.type}</td>
                    <td>${tx.category}</td>
                    <td class="text-truncate" title="${tx.note}">
                        ${tx.note}
                    </td>
                    <td>${tx.account}</td>
                    <td class="text-end fw-semibold text-primary">
                        $${tx.amount}
                    </td>
                `;

                tbody.appendChild(tr);
            });
        })
        .catch(err => {
            console.error(err);
            document.getElementById("loadingRow").innerText =
                "Failed to load transactions";
        });
});
