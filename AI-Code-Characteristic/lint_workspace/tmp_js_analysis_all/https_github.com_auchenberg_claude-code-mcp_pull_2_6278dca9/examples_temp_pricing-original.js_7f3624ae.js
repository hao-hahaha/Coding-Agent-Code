
function calculatePrice(product, quantity) {
  return product.price * quantity;
}

function applyTax(price, taxRate) {
  return price * (1 + taxRate);
}

module.exports = {
  calculatePrice,
  applyTax
};
