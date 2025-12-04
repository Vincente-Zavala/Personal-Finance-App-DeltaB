function showDuplicateModal(duplicates) {
    const tbody = document.querySelector("#duplicateTable tbody");
    tbody.innerHTML = ""; // clear old rows

    duplicates.forEach(tx => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${tx.date}</td>
            <td>${tx.amount}</td>
            <td>${tx.account}</td>
            <td>${tx.note}</td>
        `;
        tbody.appendChild(row);
    });

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('duplicateModal'));
    modal.show();

    document.getElementById("confirmImport").onclick = function() {
        // Call backend to import anyway
        fetch("/import_transactions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ transactions: duplicates })
        }).then(() => {
            modal.hide();
            alert("Transactions imported anyway.");
        });
    };
}

// Example: after submitting a transaction
fetch("/check_transaction", {
    method: "POST",
    body: JSON.stringify(transactionData),
    headers: { "Content-Type": "application/json" }
})
.then(res => res.json())
.then(data => {
    if (data.status === "duplicates_found") {
        showDuplicateModal(data.duplicates);
    } else {
        alert("Transaction imported!");
    }
});
