const formType = document.getElementById("inputtype");
const sections = document.querySelectorAll(
"#categoryfields, #categorytypefields, #accountfields, #accounttypefields, #institutionfields"
);

if (formType) {
formType.addEventListener("change", function() {
    
    sections.forEach(section => section.style.display = "none");

    if (this.value) {
    const section = document.getElementById(this.value + "fields");
    if (section) section.style.display = "block";
    }
});
}