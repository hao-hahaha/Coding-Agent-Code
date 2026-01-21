
const assert = require('assert');
const { User } = require('../src/models/user');
const { Product } = require('../src/models/product');

describe('User', () => {
  it('should return all users', async () => {
    const users = await User.findAll();
    assert(Array.isArray(users));
    assert(users.length > 0);
  });
});

describe('Product', () => {
  it('should return all products', async () => {
    const products = await Product.findAll();
    assert(Array.isArray(products));
    assert(products.length > 0);
  });
});
