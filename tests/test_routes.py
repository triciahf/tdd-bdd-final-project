######################################################################
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
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory


# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    #
    # ADD YOUR TEST CASES HERE
    #

    def test_get_product(self):
        """Test to get a product"""
        test_product = self._create_products()[0]
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_found = response.get_json()
        self.assertEqual(product_found["name"], test_product.name)
        self.assertEqual(product_found["description"], test_product.description)
        self.assertEqual(Decimal(product_found["price"]), test_product.price)
        self.assertEqual(product_found["available"], test_product.available)
        self.assertEqual(product_found["category"], test_product.category.name)

    def test_get_product_not_found(self):
        """Test to get a product that is not in the db"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        logging.debug(f"data: {data}")
        self.assertIn("No product found with id 0", data["message"])

    def test_update_product(self):
        """Test to update a prodduct"""
        test_product = self._create_products()[0]
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_found = response.get_json()
        new_description = "new description PHF"
        product_found["description"] = new_description
        update_product_response = self.client.put(f"{BASE_URL}/{test_product.id}", json=product_found)
        self.assertEqual(update_product_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_product_response.get_json()["description"], new_description)

    def test_update_a_product_not_found(self):
        """Test to delete a product that is not in the database"""
        test_product = self._create_products()[0]
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product_found = response.get_json()
        new_description = "new description PHF"
        product_found["description"] = new_description
        update_product_response = self.client.put(f"{BASE_URL}/0", json=product_found)
        self.assertEqual(update_product_response.status_code, status.HTTP_404_NOT_FOUND)
        data = update_product_response.get_json()
        logging.debug(f"data: {data}")
        self.assertIn("No product found with id 0", data["message"])

    def test_delete_a_product(self):
        """Test to delete a product from the database"""
        test_product = self._create_products(5)[0]
        count = self.get_product_count()
        response_delete = self.client.delete(f"{BASE_URL}/{test_product.id}")
        logging.debug(f"response_delete: {response_delete}")
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response_delete.data), 0)
        self.assertEqual(self.get_product_count(), count-1)

    def test_delete_a_product_not_found(self):
        """Test to delete a product from the database product not found error"""
        self._create_products(5)
        response_delete = self.client.delete(f"{BASE_URL}/0")
        logging.debug(f"response_delete: {response_delete}")
        self.assertEqual(response_delete.status_code, status.HTTP_404_NOT_FOUND)
        data = response_delete.get_json()
        logging.debug(f"data: {data}")
        self.assertIn("No product found with id 0", data["message"])

    def test_list_all(self):
        """Test to list all products"""
        self._create_products(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.get_json()
        self.assertEqual(len(response_data), 5)

    def test_list_by_name(self):
        """Test to list products by a name"""
        products = self._create_products(5)
        name = products[0].name
        logging.debug(f"name: {name}")
        name_count = 0
        for product in products:
            logging.debug(f"product.name: {product.name}")

            if product.name == name:
                logging.debug("product found")
                name_count = name_count + 1
            logging.debug(f"name_count {name_count}")
        response = self.client.get(f"{BASE_URL}?name={name}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        products_found = response.get_json()
        self.assertEqual(len(products_found), name_count)
        for product in products_found:
            self.assertEqual(product["name"], name)

    def test_list_by_catgory(self):
        """Test to list products by a category"""
        products = self._create_products(5)
        category = products[0].category
        logging.debug(f"category: {category}")
        category_count = 0
        for product in products:
            logging.debug(f"product.category: {product.category}")

            if product.category == category:
                logging.debug("product found")
                category_count = category_count + 1
            logging.debug(f"category_count {category_count}")
        response = self.client.get(f"{BASE_URL}?category={category.name}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        products_found = response.get_json()
        self.assertEqual(len(products_found), category_count)
        for product in products_found:
            self.assertEqual(product["category"], category.name)

    def test_list_by_availability(self):
        """Test to list products by the availability"""
        products = self._create_products(10)
        availability = products[0].available
        logging.debug(f"availability: {availability}")
        availability_count = 0
        for product in products:
            logging.debug(f"product.available: {product.available}")
            logging.debug(f"product.name: {product.name}")

            if product.available == availability:
                logging.debug("product found")
                availability_count = availability_count + 1
            logging.debug(f"availability_count {availability_count}")
        response = self.client.get(f"{BASE_URL}?available={availability}")

        logging.debug(f"response: {response.get_json()}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        products_found = response.get_json()
        self.assertEqual(len(products_found), availability_count)
        for product in products_found:
            self.assertEqual(product["available"], availability)

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""

        response = self.client.get(BASE_URL)
        logging.debug(f"response: {response}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
