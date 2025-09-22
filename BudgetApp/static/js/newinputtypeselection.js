    // Hide Field Input
    const formType = document.getElementById("inputtype");
    const sections = document.querySelectorAll(
    "#categoryfields, #categorytypefields, #accountfields, #accounttypefields"
    );

    if (formType) {
    formType.addEventListener("change", function() {
        // HIDE ALL
        sections.forEach(section => section.style.display = "none");

        // SHOW MATCHING ElEMENTS
        if (this.value) {
        const section = document.getElementById(this.value + "fields");
        if (section) section.style.display = "block";
        }
    });
    }