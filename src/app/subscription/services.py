from flask import jsonify
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
    try:
        products = stripe.Product.list()
        prices = stripe.Price.list()

        product_data = []
        for product in products['data']:
            price_data = next((price for price in prices['data'] if price['product'] == product['id']), None)
            product_data.append({
                "id": product['id'],
                "name": product['name'],
                "description": product.get('description', ''),
                "price": price_data['unit_amount'] / 100 if price_data else 0,
                "priceId": price_data['id'] if price_data else None
            })

        return {"data": product_data, "status": 200}
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        return {"error": str(e), "status": 500}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"error": "An unexpected error occurred", "status": 500}

def create_checkout_session(price_id, user_id):
    base_url = os.getenv("BASE_URL", "http://localhost:5000")
    success_path = '/api/subscription/checkout-success'
    cancel_path = '/cancel'

    success_url = f'{base_url}{success_path}?session_id={{CHECKOUT_SESSION_ID}}'
    cancel_url = f'{base_url}{cancel_path}'

    # Ensure the URLs are within Stripe's limits
    if len(success_url) > 200 or len(cancel_url) > 200:
        raise ValueError("URL length exceeds Stripe's limit of 200 characters")

    try:
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
        print("session created",session
              )
        return session
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        return {"error": str(e), "status": 500}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"error": "An unexpected error occurred", "status": 500}

def handle_successful_payment(session_id,user_id):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if 'subscription' not in session:
            print("No subscription found in session")  # Debugging statement
            return {"error": "No subscription found in session"}, 400
        
        subscription_id = session.subscription
        subscription = stripe.Subscription.retrieve(subscription_id)

        # user_id = session.metadata['user_id']
        if not subscription['items'].data:
            print("No items found in subscription")  # Debugging statement
            return {"error": "No items found in subscription"}, 400
        
        product_id = subscription['items'].data[0].price.product
        product = stripe.Product.retrieve(product_id)

        # Get the payment_intent or setup_intent from the session
        payment_intent_id = session.payment_intent if 'payment_intent' in session else session.setup_intent
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id) if payment_intent_id else None

        # Create an order
        order_data = {
            'payment_status': subscription.status,
            'user_id': ObjectId(user_id),
            'plan': product.name,
            'amount': subscription['items'].data[0].price.unit_amount / 100,
            'charges': subscription['items'].data[0].price.unit_amount / 100,
            # 'discount': 0,  # Assuming no discount is applied
            'payment_intent': payment_intent_id,
            'payment_info': session,
            'purchased_date': datetime.now()
        }

        try:
            order = OrderSchema().load(order_data)
        except ValidationError as err:
            print(f"Order validation error: {err.messages}")
            return {"error": "Order validation error", "details": err.messages}, 400

        order_id = db.orders.insert_one(order).inserted_id

        # Create a subscription entry in the database
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)  # Assuming a 30-day subscription

        subscription_data = {
            'order_id': order_id,
            'start_date': start_date,
            'end_date': end_date,
            'user_id': ObjectId(user_id)
        }

        try:
            subscription_entry = SubscriptionSchema().load(subscription_data)
        except ValidationError as err:
            print(f"Subscription validation error: {err.messages}")
            return {"error": "Subscription validation error", "details": err.messages}, 400

        subscription_id = db.subscriptions.insert_one(subscription_entry).inserted_id

        # Update the user with the subscription ID
        db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'subscription_id': subscription_id}})

        return {"message": "Payment successful and subscription created", "status": 200}
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        return {"error": str(e), "status": 500}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"error": "An unexpected error occurred", "status": 500}

def create_payment_intent(user_id):
    """
    Create a payment intent.

    This function takes a JSON object containing the payment information and
    creates a payment intent using the Stripe API.

    Args:
        data (dict): A dictionary containing the payment information.

    Returns:
        tuple: A tuple containing a JSON response and an HTTP status code.

    Raises:
        None
    """
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        intent = stripe.CustomerSession.create(
            customer=user["stripe_customer_id"],
            components={"pricing_table": {"enabled": True}},
        )

        return (
            jsonify(
                {
                    "message": CUSTOMER_SESSION,
                    "status":200,
                    "data": {"client_secret": intent.client_secret},
                }
            ),
            200,
        )
    except stripe.error.StripeError as e:
        return jsonify({"errors": {"error": str(e)}}), 400
    

def verify_subscription(user_id):
    """
    Verify the subscription status.

    This function verifies the subscription status of the user.

    Args:
        data (dict): A dictionary containing the user's email.

    Returns:
        tuple: A tuple containing a JSON response and an HTTP status code.
    """
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return (
            jsonify({"errors": {"error": USER_NOT_FOUND}}),
            404,
        )

    if (
        user.get("subscription_status") is None
        or user.get("subscription_status") == "deleted"
    ):
        return (
            jsonify(
                {
                    "message": "subscription_status",
                    "data": {"status": "inactive"},
                }
            ),
            200,
        )

    return (
        jsonify(
            {
                "message": "subscription_status",
                "data": {"status": user["subscription_status"], "product_name":user["product_name"]},
            }
        ),
        200,
    )


def create_billing_session(user_id):
    """
    Create a billing portal session.

    This function creates a billing portal session for the user.

    Args:
        data (dict): A dictionary containing the user's email.

    Returns:
        tuple: A tuple containing a JSON response and an HTTP status code.
    """
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
                    },
                    # {
                    #     "prices": [os.getenv("STRIPE_PRICE_2_ID")],
                    #     "product": os.getenv("STRIPE_PRODUCT_2_ID"),
                    # },
                ],
                "enabled": True,
                "default_allowed_updates": ["price"],
            },
        },
    )

    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return (
            jsonify({"errors": {"error":"user_not_found"}}),
            404,
        )

    session = stripe.billing_portal.Session.create(
        customer=user["stripe_customer_id"],
        configuration=con.id,
        return_url="https://example.com/account",
    )

    return (
        jsonify(
            {
                "message": "billing_portal_created",
                "data": {"url": session.url},
            }
        ),
        200,
    )