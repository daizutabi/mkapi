const buttons = document.querySelectorAll(".mkapi-parent-toggle");

buttons.forEach((button) => {
  button.addEventListener("click", () => {
    const elements = document.querySelectorAll(".mkapi-object-parent");
    let isVisible = elements[0].style.display === "inline";

    elements.forEach((element) => {
      element.style.display = isVisible ? "none" : "inline";
    });

    buttons.forEach((btn) => {
      btn.title = isVisible ? "Show Class Name" : "Hide Class Name";
    });
  });
});
