import os
from bson import ObjectId
import stripe
from src.app.healper.response import make_response
from src.app.utils.messages import MISSING_PARAMETERS, PAYMENT_INTENT_CREATED, PAYMENT_METHOD_ATTACHED_SUCCESS, PAYMENT_METHODS_FETCHED_SUCCESS, UNEXPECTED_ERROR, USER_NOT_FOUND, WALLET_INFO_FETCHED_SUCCESS, WALLET_NOT_FOUND
from src.db import db

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def get_wallet_info_service(user_id):
    """
    Service to get the user's wallet information.

    Parameters:
        user_id (str): The ID of the user.

    Returns:
        (dict): A standard response JSON using make_response.
    """
    try:
        wallet = db.wallet.find_one({"user_id": ObjectId(user_id)})

        if wallet:
            # Convert ObjectId to string for JSON serialization
            wallet["_id"] = str(wallet["_id"])
            wallet["user_id"] = str(wallet["user_id"])
            print('wallet',wallet)
            return make_response(
                status="success",
                message=WALLET_INFO_FETCHED_SUCCESS,
                data=wallet,
                status_code=200
            )
        else:
            return make_response(
                status="error",
                message=WALLET_NOT_FOUND,
                data=None,
                status_code=404
            )

    except Exception as e:
        return make_response(
            status="error",
            message=UNEXPECTED_ERROR,
            data=None,
            status_code=500
        )

def calculate_tokens(amount):
    """
    Helper function to calculate the tokens based on the amount.

    Parameters:
        amount (float): The recharge amount.

    Returns:
        int: The number of tokens corresponding to the amount.
    """
    tokens_per_dollar = 10000000 / 19.99
    return int(round(amount * tokens_per_dollar))

def recharge_wallet_service(user_id, amount):
    """
    Service to recharge the user's wallet.

    Parameters:
        user_id (str): The ID of the user.
        amount (float): The amount to recharge.

    Returns:
        (dict): A standard response JSON using make_response.
    """
    try:
        tokens = calculate_tokens(float(amount))
        amount_in_cents = int(float(amount) * 100)
        
        user = db.users.find_one({"_id": ObjectId(user_id)})

        if not user:
            return make_response(
                status="error",
                message=USER_NOT_FOUND,
                data=None,
                status_code=404
            )

        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency='cad',
            customer=user["stripe_customer_id"],
            metadata={'user_id': str(user_id), 'tokens': tokens, "wallet_type": "wallet"}
        )

        return make_response(
            status="success",
            message=PAYMENT_INTENT_CREATED,
            data={"payment_intent": intent},
            status_code=200
        )

    except stripe.error.StripeError as e:
        return make_response(
            status="error",
            message=str(e),
            data=None,
            status_code=400
        )

def fetch_payment_methods_service(user_id):
    """
    Service to fetch the user's payment methods from Stripe.

    Parameters:
        user_id (str): The ID of the user.

    Returns:
        (dict): A standard response JSON using make_response.
    """
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})

        if not user:
            return make_response(
                status="error",
                message=USER_NOT_FOUND,
                data=None,
                status_code=404
            )

        payment_methods = stripe.PaymentMethod.list(customer=user["stripe_customer_id"], type="card")

        return make_response(
            status="success",
            message=PAYMENT_METHODS_FETCHED_SUCCESS,
            data={"payment_methods": payment_methods},
            status_code=200
        )

    except stripe.error.StripeError as e:
        return make_response(
            status="error",
            message=str(e),
            data=None,
            status_code=400
        )

def attach_payment_method_service(user_id, payment_method_id):
    """
    Service to attach a payment method to the user's Stripe account.

    Parameters:
        user_id (str): The ID of the user.
        payment_method_id (str): The ID of the Stripe payment method to attach.

    Returns:
        (dict): A standard response JSON using make_response.
    """
    try:
        if not user_id or not payment_method_id:
            return make_response(
                status="error",
                message=MISSING_PARAMETERS,
                data=None,
                status_code=400
            )

        user = db.users.find_one({"_id": ObjectId(user_id)})

        if not user:
            return make_response(
                status="error",
                message=USER_NOT_FOUND,
                data=None,
                status_code=404
            )

        payment_method = stripe.PaymentMethod.attach(payment_method_id, customer=user["stripe_customer_id"])

        stripe.Customer.modify(
            user["stripe_customer_id"],
            invoice_settings={'default_payment_method': payment_method_id}
        )

        return make_response(
            status="success",
            message=PAYMENT_METHOD_ATTACHED_SUCCESS,
            data={"paymentMethod": payment_method},
            status_code=200
        )

    except stripe.error.StripeError as e:
        return make_response(
            status="error",
            message=str(e),
            data=None,
            status_code=400
        )
