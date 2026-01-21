
function calculateTotal(items) {
  let total = 0;
  for (let i = 0; i < items.length; i++) {
    total += items[i].price;
  }
  return total;
}

// This function has several issues:
// 1. No input validation
// 2. No handling for missing price property
// 3. No handling for non-numeric prices
function applyDiscount(total, discountCode) {
  if (discountCode === 'SAVE10') {
    return total * 0.9;
  } else if (discountCode === 'SAVE20') {
    return total * 0.8;
  }
  return total;
}

module.exports = {
  calculateTotal,
  applyDiscount
};
