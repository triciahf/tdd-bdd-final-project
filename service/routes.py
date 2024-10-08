######################################################################
# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
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

# spell: ignore Rofrano jsonify restx dbname
"""
Product Store Service with UI
"""
import logging
from flask import jsonify, request, abort
from flask import url_for  # noqa: F401 pylint: disable=unused-import
from service.models import Product, Category
from service.common import status  # HTTP Status Codes
from . import app


logger = logging.getLogger("flask.app")


######################################################################
# H E A L T H   C H E C K
######################################################################
@app.route("/health")
def healthcheck():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="OK"), status.HTTP_200_OK


######################################################################
# H O M E   P A G E
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    logger.debug("home page")
    return app.send_static_file("index.html")


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


######################################################################
# C R E A T E   A   N E W   P R O D U C T
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    """
    Creates a Product
    This endpoint will create a Product based the data in the body that is posted
    """

    app.logger.info("Request to Create a Product...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Processing: %s", data)
    product = Product()
    product.deserialize(data)
    product.create()
    app.logger.info("Product with new id [%s] saved!", product.id)

    message = product.serialize()

    #
    # Uncomment this line of code once you implement READ A PRODUCT
    #
    location_url = url_for("get_products", product_id=product.id, _external=True)

    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# L I S T   A L L   P R O D U C T S
######################################################################

#
# PLACE YOUR CODE TO LIST ALL PRODUCTS HERE
#
@app.route("/products", methods=["GET"])
def list_products():
    """List products"""
    logger.info("Listing products")

    product_list = []
    name = request.args.get("name")
    category = request.args.get("category")
    availability = request.args.get("available")
    if name:
        logger.info(f"listing products with name {name}")
        products = Product.find_by_name(name)
    elif category:
        logger.info(f"listing products with category {category}")
        category_enum = getattr(Category, category.upper())
        products = Product.find_by_category(category_enum)
    elif availability:
        logger.info(f"listing products with availability {availability}")
        products = Product.find_by_availability(availability)
    else:
        logger.info("listing all products")
        products = Product.all()

    for product in products:
        product_list.append(product.serialize())
    return product_list, status.HTTP_200_OK

######################################################################
# R E A D   A   P R O D U C T
######################################################################


@app.route("/products/<int:product_id>", methods=["GET"])
def get_products(product_id):
    """
    Get a product by its id
    """
    logger.info(f"Getting product {product_id}")
    product_found = Product.find(product_id)
    if not product_found:
        abort(status.HTTP_404_NOT_FOUND, f"No product found with id {product_id}")
    logger.info(f"product retrieved {product_found}")
    return product_found.serialize(), status.HTTP_200_OK

######################################################################
# U P D A T E   A   P R O D U C T
######################################################################


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    """
    Updates a product
    """
    app.logger.info("Request to Update a Product...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info(f"Processing: {data}")
    product_found = Product.find(product_id)
    if not product_found:
        abort(status.HTTP_404_NOT_FOUND, f"No product found with id {product_id}")
    product_found_deserializable = product_found.deserialize(data)
    product_found_deserializable.update()
    return product_found_deserializable.serialize(), status.HTTP_200_OK


####################################################
# D E L E T E   A   P R O D U C T
######################################################################


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """
    Deletes a product
    """
    app.logger.info("Request to Delete a Product...")

    product_found = Product.find(product_id)
    if not product_found:
        abort(status.HTTP_404_NOT_FOUND, f"No product found with id {product_id}")
    product_found.delete()
    return "", status.HTTP_204_NO_CONTENT
