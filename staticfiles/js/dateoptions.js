document.addEventListener("DOMContentLoaded", function () {
    const monthbutton = document.getElementById("monthbutton");
    const custombutton = document.getElementById("custombutton");
    const monthyearsection = document.getElementById("monthyearsection");
    const customsection = document.getElementById("customsection");
  
    // Show month/year by default
    monthyearsection.style.display = "block";
    customsection.style.display = "none";
  
    monthbutton.addEventListener("click", function () {
      monthbutton.classList.add("active");
      custombutton.classList.remove("active");
      monthyearsection.classList.remove("d-none");
      customsection.classList.add("d-none");
    });
    
    custombutton.addEventListener("click", function () {
      custombutton.classList.add("active");
      monthbutton.classList.remove("active");
      monthyearsection.classList.add("d-none");
      customsection.classList.remove("d-none");
    });
    
  });
  