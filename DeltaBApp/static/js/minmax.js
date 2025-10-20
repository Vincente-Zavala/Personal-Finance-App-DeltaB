document.addEventListener("DOMContentLoaded", function () {
    const exactRadio = document.getElementById("exactoption");
    const minmaxRadio = document.getElementById("minmaxoption");
    const exactInput = document.getElementById("exactinput");
    const minmaxInputs = document.getElementById("minmaxinput");
  
    function toggleInputs() {
      if (exactRadio.checked) {
        exactInput.hidden = false;
        minmaxInputs.hidden = true;
      } else {
        exactInput.hidden = true;
        minmaxInputs.hidden = false;
      }
    }
  
    toggleInputs();
    exactRadio.addEventListener("change", toggleInputs);
    minmaxRadio.addEventListener("change", toggleInputs);
  });