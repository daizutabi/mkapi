const documentButtons = document.querySelectorAll(".mkapi-document-toggle");

documentButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const element = button.parentElement.parentElement.nextElementSibling;
    let isInvisible = element.style.display === "none";
    element.style.display = isInvisible ? "block" : "none";
    button.textContent = isInvisible ? "[-]" : "[+]";
  });
});

const sectionButtons = document.querySelectorAll(".mkapi-section-toggle");

sectionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const element = button.parentElement.parentElement.nextElementSibling;
    let isInvisible = element.style.display === "none";
    element.style.display = isInvisible ? "block" : "none";
    button.textContent = isInvisible ? "[-]" : "[+]";
  });
});

const parentButtons = document.querySelectorAll(".mkapi-parent-toggle");

parentButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const elements = document.querySelectorAll(".mkapi-object-parent");
    let isVisible = elements[0].style.display === "inline";

    elements.forEach((element) => {
      element.style.display = isVisible ? "none" : "inline";
    });
  });
});
