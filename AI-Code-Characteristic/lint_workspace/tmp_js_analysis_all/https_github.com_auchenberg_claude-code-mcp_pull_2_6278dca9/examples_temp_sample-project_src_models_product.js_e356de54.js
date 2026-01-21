
class Product {
  constructor(id, name, price) {
    this.id = id;
    this.name = name;
    this.price = price;
  }
  
  static async findAll() {
    // Simulated database query
    return [
      new Product(1, 'Laptop', 999.99),
      new Product(2, 'Smartphone', 499.99)
    ];
  }
}

module.exports = { Product };
