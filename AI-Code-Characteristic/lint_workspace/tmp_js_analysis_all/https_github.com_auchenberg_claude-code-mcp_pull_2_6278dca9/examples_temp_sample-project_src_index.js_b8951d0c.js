
const { User } = require('./models/user');
const { Product } = require('./models/product');
const express = require('express');

const app = express();
app.use(express.json());

app.get('/users', async (req, res) => {
  const users = await User.findAll();
  res.json(users);
});

app.get('/products', async (req, res) => {
  const products = await Product.findAll();
  res.json(products);
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
