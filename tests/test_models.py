# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #
    def test_read_a_product(self):
        """Test to read a product"""
        product = ProductFactory()
        logging.debug(f"product: {product}")
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        product_found = Product.find(product.id)
        self.assertEqual(product_found.name, product.name)
        self.assertEqual(product_found.description, product.description)
        self.assertEqual(Decimal(product_found.price), product.price)
        self.assertEqual(product_found.available, product.available)
        self.assertEqual(product_found.category, product.category)

    def test_update_a_product(self):
        """Test to update a product"""
        product = ProductFactory()
        logging.debug(f"product: {product}")
        product.id = None
        product.create()
        logging.debug(f"product: {product}")
        self.assertIsNotNone(product.id)
        new_description = "New description from PHF"
        product.description = new_description
        # Assert that it was assigned an id and shows up in the database
        product_id = product.id
        product.update()
        self.assertEqual(product.id, product_id)
        self.assertEqual(product.description, new_description)

        products = Product.all()
        self.assertEqual(len(products), 1)
        product_found = products[0]
        self.assertEqual(product_found.name, product.name)
        self.assertEqual(product_found.description, product.description)
        self.assertEqual(Decimal(product_found.price), product.price)
        self.assertEqual(product_found.available, product.available)
        self.assertEqual(product_found.category, product.category)

    def test_delete_a_product(self):
        """Test to delete a product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertEqual(len(Product.all()), 1)
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """Test to list all products"""
        products = Product.all()
        self.assertEqual(len(products), 0)
        for i in range(5):
            product = ProductFactory()
            product.id = None
            product.create()
        self.assertEqual(len(Product.all()), 5)

    def test_find_product_by_name(self):
        """Test to find a product by name"""

        for i in range(5):
            product = ProductFactory()
            product.id = None
            product.create()
        products = Product.all()

        first_product = products[0]
        name = first_product.name
        count = 0
        for item in products:
            if item.name == name:
                count = count + 1
        products_found = Product.find_by_name(name)

        self.assertEqual(products_found.count(), count)
        for product_found in products_found:
            self.assertEqual(product_found.name, name)

    def test_find_product_by_availability(self):
        """Test to find a product by availability"""
        for i in range(10):
            product = ProductFactory()
            product.id = None
            product.create()
        products = Product.all()

        first_product = products[0]
        availability = first_product.available
        count = 0
        for item in products:
            if item.available == availability:
                count = count + 1
        products_found = Product.find_by_availability(availability)

        self.assertEqual(products_found.count(), count)
        for product_found in products_found:
            self.assertEqual(product_found.available, availability)

    def test_find_by_category(self):
        """Test to find a products by category"""
        for i in range(10):
            product = ProductFactory()
            product.id = None
            product.create()
        products = Product.all()

        first_product = products[0]
        category = first_product.category
        count = 0
        for item in products:
            if item.category == category:
                count = count + 1
        products_found = Product.find_by_category(category)

        self.assertEqual(products_found.count(), count)
        for product_found in products_found:
            self.assertEqual(product_found.category, category)
