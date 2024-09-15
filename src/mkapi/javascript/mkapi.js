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

const itemsButtons = document.querySelectorAll(".mkapi-section-toggle");

itemsButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const element = button.parentElement.nextElementSibling;
    let isInvisible = element.style.display === "none";
    element.style.display = isInvisible ? "block" : "none";
  });
});
