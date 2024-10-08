from flask import jsonify, make_response
import stripe
import os
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import MongoClient
from marshmallow import ValidationError
from src.app.utils.messages import CUSTOMER_SESSION, USER_NOT_FOUND
from src.db import db
from src.app.subscription.schema import OrderSchema, SubscriptionSchema
from pymongo.errors import PyMongoError

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def fetch_stripe_products():
    """
    Fetch products and prices from Stripe and return a structured response.

    Returns:
        dict: A dictionary containing the product data or an error message in a standard format.
    """
    try:
        # Fetch all products and prices from Stripe
        products = stripe.Product.list()
        prices = stripe.Price.list()

        product_data = []

        # Iterate through each product and match its price
        for product in products['data']:
            # Find the associated price for the product
            price_data = next((price for price in prices['data'] if price['product'] == product['id']), None)

            # Append product information along with price details
            product_data.append({
                "id": product['id'],
                "name": product['name'],
                "description": product.get('description', ''),
                "price": price_data['unit_amount'] / 100 if price_data else 0,  # Convert price to dollars
                "priceId": price_data['id'] if price_data else None
            })

        # Return a success response
        return make_response(
            status="success",
            message="Stripe products fetched successfully",
            data=product_data,
            status_code=200
        )

    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        # Return a Stripe error response
        return make_response(
            status="error",
            message="Error fetching Stripe products",
            data=None,
            status_code=500
        )

    except Exception as e:
        print(f"Unexpected error: {e}")
        # Return a generic error response for unexpected exceptions
        return make_response(
            status="error",
            message="An unexpected error occurred",
            data=None,
            status_code=500
        )

def create_checkout_session(price_id, user_id):
    """
    Create a Stripe checkout session for a subscription.

    Parameters:
        price_id (str): The Stripe price ID for the subscription.
        user_id (str): The ID of the user who is subscribing.

    Returns:
        dict: A structured response with the session data or an error message.
    """
    base_url = os.getenv("BASE_URL", "http://localhost:5000")
    success_path = '/api/subscription/checkout-success'
    cancel_path = '/cancel'

    success_url = f'{base_url}{success_path}?session_id={{CHECKOUT_SESSION_ID}}'
    cancel_url = f'{base_url}{cancel_path}'

    # Ensure the URLs are within Stripe's limits
    if len(success_url) > 200 or len(cancel_url) > 200:
        return make_response(
            status="error",
            message="URL length exceeds Stripe's limit of 200 characters",
            data=None,
            status_code=400
        )

    try:
        # Create the Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'user_id': user_id}
        )

        # Return success response
        return make_response(
            status="success",
            message="Checkout session created successfully",
            data={"session": session},
            status_code=200
        )

    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        # Return Stripe error response
        return make_response(
            status="error",
            message="Error creating Stripe checkout session",
            data=None,
            status_code=500
        )

    except Exception as e:
        print(f"Unexpected error: {e}")
        # Return unexpected error response
        return make_response(
            status="error",
            message="An unexpected error occurred",
            data=None,
            status_code=500
        )


def handle_successful_payment(session_id, user_id):
    """
    Handle successful payment and create an order and subscription.

    Parameters:
        session_id (str): The Stripe session ID.
        user_id (str): The ID of the user.

    Returns:
        (dict): A JSON response with a message and status.
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if 'subscription' not in session:
            return make_response(
                status="error",
                message="No subscription found in session",
                data=None,
                status_code=400
            )
        
        subscription_id = session.subscription
        subscription = stripe.Subscription.retrieve(subscription_id)

        if not subscription['items'].data:
            return make_response(
                status="error",
                message="No items found in subscription",
                data=None,
                status_code=400
            )
        
        product_id = subscription['items'].data[0].price.product
        product = stripe.Product.retrieve(product_id)

        payment_intent_id = session.payment_intent if 'payment_intent' in session else session.setup_intent
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id) if payment_intent_id else None

        order_data = {
            'payment_status': subscription.status,
            'user_id': ObjectId(user_id),
            'plan': product.name,
            'amount': subscription['items'].data[0].price.unit_amount / 100,
            'charges': subscription['items'].data[0].price.unit_amount / 100,
            'payment_intent': payment_intent_id,
            'payment_info': session,
            'purchased_date': datetime.now()
        }

        try:
            order = OrderSchema().load(order_data)
        except ValidationError as err:
            return make_response(
                status="error",
                message="Order validation error",
                data=err.messages,
                status_code=400
            )

        order_id = db.orders.insert_one(order).inserted_id

        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)

        subscription_data = {
            'order_id': order_id,
            'start_date': start_date,
            'end_date': end_date,
            'user_id': ObjectId(user_id)
        }

        try:
            subscription_entry = SubscriptionSchema().load(subscription_data)
        except ValidationError as err:
            return make_response(
                status="error",
                message="Subscription validation error",
                data=err.messages,
                status_code=400
            )

        subscription_id = db.subscriptions.insert_one(subscription_entry).inserted_id

        db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'subscription_id': subscription_id}})

        return make_response(
            status="success",
            message="Payment successful and subscription created",
            data=None,
            status_code=200
        )
    
    except stripe.error.StripeError as e:
        return make_response(
            status="error",
            message=str(e),
            data=None,
            status_code=500
        )
    
    except Exception as e:
        return make_response(
            status="error",
            message="An unexpected error occurred",
            data=None,
            status_code=500
        )

def create_payment_intent(user_id):
    """
    Create a payment intent using Stripe.

    Parameters:
        user_id (str): The ID of the user.

    Returns:
        (dict): A JSON response with client secret or error.
    """
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        intent = stripe.CustomerSession.create(
            customer=user["stripe_customer_id"],
            components={"pricing_table": {"enabled": True}},
        )

        return make_response(
            status="success",
            message="Customer session created",
            data={"client_secret": intent.client_secret},
            status_code=200
        )
    
    except stripe.error.StripeError as e:
        return make_response(
            status="error",
            message=str(e),
            data=None,
            status_code=400
        )
    

def verify_subscription(user_id):
    """
    Verify the subscription status of a user.

    Parameters:
        user_id (str): The ID of the user.

    Returns:
        (dict): A JSON response with the subscription status.
    """
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return make_response(
                status="error",
                message="User not found",
                data=None,
                status_code=404
            )

        if user.get("subscription_status") is None or user.get("subscription_status") == "deleted":
            return make_response(
                status="success",
                message="Subscription status fetched",
                data={"status": "inactive"},
                status_code=200
            )

        return make_response(
            status="success",
            message="Subscription status fetched",
            data={"status": user["subscription_status"], "product_name": user["product_name"]},
            status_code=200
        )

    except Exception as e:
        return make_response(
            status="error",
            message="An unexpected error occurred",
            data=None,
            status_code=500
        )


def create_billing_session(user_id):
    """
    Create a billing portal session for the user.

    Parameters:
        user_id (str): The ID of the user.

    Returns:
        (dict): A JSON response with the billing portal URL or error message.
    """
    try:
        con = stripe.billing_portal.Configuration.create(
            business_profile={
                "privacy_policy_url": "https://example.com/privacy",
                "terms_of_service_url": "https://example.com/terms",
            },
            features={
                "customer_update": {"enabled": False},
                "invoice_history": {"enabled": True},
                "payment_method_update": {"enabled": True},
                "subscription_cancel": {"enabled": True},
                "subscription_update": {
                    "products": [
                        {
                            "prices": [os.getenv("STRIPE_PRICE_1_ID")],
                            "product": os.getenv("STRIPE_PRODUCT_1_ID"),
                        }
                    ],
                    "enabled": True,
                    "default_allowed_updates": ["price"],
                },
            },
        )

        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return make_response(
                status="error",
                message="User not found",
                data=None,
                status_code=404
            )

        session = stripe.billing_portal.Session.create(
            customer=user["stripe_customer_id"],
            configuration=con.id,
            return_url="https://example.com/account",
        )

        return make_response(
            status="success",
            message="Billing portal created",
            data={"url": session.url},
            status_code=200
        )

    except stripe.error.StripeError as e:
        return make_response(
            status="error",
            message=str(e),
            data=None,
            status_code=400
        )
    
    except Exception as e:
        return make_response(
            status="error",
            message="An unexpected error occurred",
            data=None,
            status_code=500
        )
