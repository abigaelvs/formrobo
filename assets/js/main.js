var button = document.querySelectorAll(".delete-button");
var strong = document.getElementById("modal-strong");
var modalDelete = document.getElementById("modal-delete");

button.forEach(b => {
    b.addEventListener("click", () => {
        strong.textContent = b.getAttribute("data-name")
        modalDelete.href = b.getAttribute("data-href");
    })
})