// ============================
//  Upload Wizard (AJAX)
// ============================

document.addEventListener("DOMContentLoaded", () => {

    function uploadFile() {
        const fileInput = document.getElementById("uploadfile");
        const file = fileInput.files[0];
        if (!file) return;
    
        const formData = new FormData();
        formData.append("uploadfile", file);
    
        // get CSRF token
        const csrf = document.querySelector("[name=csrfmiddlewaretoken]").value;
    
        fetch("/uploadfile/", {
            method: "POST",
            headers: {
                "X-CSRFToken": csrf
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert("Upload failed.");
                return;
            }
    
            // Populate columns
            const columns = data.columns;
            const accounts = data.accounts;
    
            const dateSelect = document.getElementById("dateselection");
            const noteSelect = document.getElementById("noteselection");
            const amountSelect = document.getElementById("amountselection");
            const accountSelect = document.getElementById("accountselection");
    
            [dateSelect, noteSelect, amountSelect].forEach(select => {
                select.innerHTML = `<option value="" disabled selected>Select Column</option>`;
                columns.forEach(col => {
                    select.innerHTML += `<option value="${col}">${col}</option>`;
                });
            });
    
            // Populate accounts
            accountSelect.innerHTML = `<option value="" disabled selected>Select Account</option>`;
            accounts.forEach(acc => {
                accountSelect.innerHTML += `<option value="${acc.id}">${acc.name}</option>`;
            });
    
            // Close upload modal, open map columns modal
            const uploadModal = bootstrap.Modal.getInstance(document.getElementById("uploadfile"));
            uploadModal.hide();
    
            const mapColumnsModal = new bootstrap.Modal(document.getElementById("mapcolumns"));
            mapColumnsModal.show();
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Error uploading file.");
        });
    }
    

    // ----------------------------
    // 2. Submit Column Mapping
    // ----------------------------
    const mapForm = document.getElementById("mapcolumns_form");
    if (mapForm) {
        mapForm.addEventListener("submit", function (e) {
            e.preventDefault();

            let formData = new FormData(mapForm);

            fetch("/adduploaddata/", {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken },
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === "require_polarity") {
                    // Fill polarity modal with sample row
                    populatePolarityModal(data.sample);
                    showModal("#accountpolarity");
                }
                else if (data.status === "preview_ready") {
                    loadUploadPreview();
                }
                else {
                    alert(data.error);
                }
            });
        });
    }


    // ----------------------------
    // 3. Polarity Selection
    // ----------------------------
    const polarityForm = document.getElementById("accountpolarity_form");
    if (polarityForm) {
        polarityForm.addEventListener("submit", function (e) {
            e.preventDefault();

            let formData = new FormData(polarityForm);

            fetch("/setpolarity/", {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken },
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === "ok") {
                    loadUploadPreview();
                } else {
                    alert(data.error);
                }
            });
        });
    }



    // ----------------------------
    // Load Upload Preview
    // ----------------------------
    function loadUploadPreview() {
        fetch("/getpreview/")
        .then(r => r.json())
        .then(data => {
            populatePreviewTable(data.transactions);
            showModal("#uploadpreview");
        });
    }


    // ============================
    // Helper Functions
    // ============================


    function populateMappingModal(columns) {
        const selects = document.querySelectorAll(".column-select");

        selects.forEach(sel => {
            sel.innerHTML = `<option disabled selected>Select Column</option>`;
            columns.forEach(col => {
                sel.innerHTML += `<option value="${col}">${col}</option>`;
            });
        });
    }


    function populatePolarityModal(sample) {
        document.getElementById("polarity_date").innerText     = sample.date;
        document.getElementById("polarity_note").innerText     = sample.note;
        document.getElementById("polarity_amount").innerText   = sample.amount;
        document.getElementById("polarity_account").innerText  = sample.account;
    }


    function populatePreviewTable(rows) {
        let table = document.getElementById("preview_table_body");
        table.innerHTML = "";

        rows.forEach(tx => {
            table.innerHTML += `
                <tr>
                    <td>${tx.date}</td>
                    <td>${tx.type}</td>
                    <td>${tx.category}</td>
                    <td>${tx.note}</td>
                    <td>${tx.account}</td>
                    <td class="text-end">$${tx.amount}</td>
                </tr>
            `;
        });
    }


    function showModal(selector) {
        const modal = new bootstrap.Modal(document.querySelector(selector));
        modal.show();
    }


    function getCSRF() {
        const cookieValue = document.cookie
            .split("; ")
            .find(row => row.startsWith("csrftoken="));
        return cookieValue ? cookieValue.split("=")[1] : "";
    }

});
