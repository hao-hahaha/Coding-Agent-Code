
function calculatePrice(product, quantity) {
  if (!product || typeof product.price !== 'number') {
    throw new Error('Invalid product');
  }
  if (typeof quantity !== 'number' || quantity <= 0) {
    throw new Error('Invalid quantity');
  }
  return product.price * quantity;
}

function applyTax(price, taxRate) {
  if (typeof price !== 'number' || price < 0) {
    throw new Error('Invalid price');
  }
  if (typeof taxRate !== 'number' || taxRate < 0) {
    throw new Error('Invalid tax rate');
  }
  return price * (1 + taxRate);
}

function calculateTotal(items, taxRate = 0) {
  const subtotal = items.reduce((total, item) => {
    return total + calculatePrice(item.product, item.quantity);
  }, 0);
  
  return applyTax(subtotal, taxRate);
}

module.exports = {
  calculatePrice,
  applyTax,
  calculateTotal
};
