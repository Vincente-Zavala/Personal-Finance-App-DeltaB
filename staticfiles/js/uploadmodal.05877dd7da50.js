// ===============================
//  Upload Wizard (Fully Working)
// ===============================

document.addEventListener("DOMContentLoaded", () => {

    // ---------------------------------------
    // CSRF Helper
    // ---------------------------------------
    function getCSRF() {
        const cookie = document.cookie.split("; ").find(row => row.startsWith("csrftoken="));
        return cookie ? cookie.split("=")[1] : "";
    }
    const csrfToken = getCSRF();



    // =======================================
    // 1. UPLOAD FILE
    // =======================================
    function uploadFile() {
        const fileInput = document.getElementById("uploadfile");
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("uploadfile", file);

        fetch("/uploadfile/", {
            method: "POST",
            headers: { "X-CSRFToken": csrfToken },
            body: formData
        })
        .then(r => r.json())
        .then(data => {
            if (!data.success) {
                alert("Upload failed.");
                return;
            }

            // Populate dropdowns
            populateMappingModal(data.columns);
            populateAccountDropdown(data.accounts);

            // Switch modals
            hideModal("#uploadfilemodal");
            showModal("#mapcolumns");
        })
        .catch(err => {
            console.error(err);
            alert("Upload error.");
        });
    }



    // Attach upload handler
    const uploadInput = document.getElementById("uploadfile");
    if (uploadInput) {
        uploadInput.addEventListener("change", uploadFile);
    }

    const uploadButton = document.getElementById("uploadfile_button");
    if (uploadButton) {
        uploadButton.addEventListener("click", (e) => {
            e.preventDefault();
            uploadFile();
        });
    }




    // =======================================
    // 2. MAP COLUMNS STEP
    // =======================================
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
                    populatePolarityModal(data.sample);
                    hideModal("#mapcolumns");
                    showModal("#accountpolarity");
                }

                else if (data.status === "preview_ready") {
                    loadUploadPreview();
                }

                else {
                    alert(data.error || "Mapping failed.");
                }
            });
        });
    }



    // =======================================
    // 3. SELECT ACCOUNT POLARITY (if needed)
    // =======================================
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
                    hideModal("#accountpolarity");
                    loadUploadPreview();
                } else {
                    alert(data.error);
                }
            });
        });
    }




    // =======================================
    // 4. SHOW PREVIEW TABLE
    // =======================================
    function loadUploadPreview() {
        fetch("/getpreview/")
        .then(r => r.json())
        .then(data => {
            populatePreviewTable(data.transactions);
            showModal("#uploadpreview");
        })
        .catch(err => console.error(err));
    }




    // =======================================
    // Helper Functions
    // =======================================
    function populateMappingModal(columns) {
        const selects = document.querySelectorAll(".column-select");

        selects.forEach(sel => {
            sel.innerHTML = `<option disabled selected>Select Column</option>`;
            columns.forEach(col => {
                sel.innerHTML += `<option value="${col}">${col}</option>`;
            });
        });
    }

    function populateAccountDropdown(accounts) {
        const accountSelect = document.getElementById("accountselection");
        accountSelect.innerHTML = `<option disabled selected>Select Account</option>`;

        accounts.forEach(acc => {
            accountSelect.innerHTML += `<option value="${acc.id}">${acc.name}</option>`;
        });
    }

    function populatePolarityModal(sample) {
        document.getElementById("polarity_date").innerText = sample.date;
        document.getElementById("polarity_note").innerText = sample.note;
        document.getElementById("polarity_amount").innerText = sample.amount;
        document.getElementById("polarity_account").innerText = sample.account;
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


    // Bootstrap Modal helpers
    function showModal(selector) {
        const modalEl = document.querySelector(selector);
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }

    function hideModal(selector) {
        const modalEl = document.querySelector(selector);
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
    }

});
