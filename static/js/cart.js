const increaseButtons = document.querySelectorAll(".increase-quantity");
const decreaseButtons = document.querySelectorAll(".decrease-quantity");

increaseButtons.forEach((button) => {
    button.addEventListener("click", (event) => {
        event.preventDefault();
        const currentItem = event.target.closest(".cart-item");
        const quantityElement = currentItem.querySelector(".item-quantity");
        const priceElement = currentItem.querySelector(".cart-item-price");
        const pricePerItem = parseFloat(priceElement.getAttribute("data-price"));
        const currentQuantity = parseInt(quantityElement.textContent);

        quantityElement.textContent = currentQuantity + 1;
        updateCartItemPrice(priceElement, pricePerItem, currentQuantity + 1);
    });
});

decreaseButtons.forEach((button) => {
    button.addEventListener("click", (event) => {
        event.preventDefault();
        const currentItem = event.target.closest(".cart-item");
        const quantityElement = currentItem.querySelector(".item-quantity");
        const priceElement = currentItem.querySelector(".cart-item-price");
        const pricePerItem = parseFloat(priceElement.getAttribute("data-price"));
        const currentQuantity = parseInt(quantityElement.textContent);

        if (currentQuantity > 1) {
            quantityElement.textContent = currentQuantity - 1;
            updateCartItemPrice(priceElement, pricePerItem, currentQuantity - 1);
        }
    });
});

function updateCartItemPrice(priceElement, pricePerItem, quantity) {
    const totalPrice = (pricePerItem * quantity).toFixed(2);
    priceElement.textContent = "$" + totalPrice;
}

function updateCartCount() {
    var cartCount = document.querySelector('.cart-count');
    fetch('{% url "fetch-cart-count" %}')
        .then(response => response.json())
        .then(data => {
            cartCount.textContent = data.cart_count;
        });
}

updateCartCount();