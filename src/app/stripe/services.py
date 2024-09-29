from flask import jsonify,request
import stripe
import os
import datetime
from bson import ObjectId
from pymongo import MongoClient
from marshmallow import ValidationError
from src.app.user.services import UserNotFoundError
from src.app.utils.constants import DEFAULT_TOKENS_AT_SUBSCRIPTION
from src.app.utils.messages import CUSTOMER_SESSION, USER_NOT_FOUND, WEBHOOK_RECEIVED
from src.db import db
from src.app.subscription.schema import OrderSchema, SubscriptionSchema
from pymongo.errors import PyMongoError

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def stripe_webhook(data):
    """
    Handle the Stripe webhook.

    This function is responsible for handling the Stripe webhook events.

    Args:
        data (bytes): The request data from the webhook.

    Returns:
        str: The result of the webhook event handling.
    """
    payload = data.decode("utf-8")
    sig_header = request.headers.get("Stripe-Signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except ValueError as e:
        # Invalid payload
        return jsonify({"error": str(e)}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify({"error": str(e)}), 400

    # Handle the event
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]

        # Find the user in the database from customer ID
        # user = User.find_by_stripe_customer_id(payment_intent["customer"])
        # Find the user in the database from customer ID
        user = db.users.find_one({"stripe_customer_id": payment_intent["customer"]})

        if not user:
            return jsonify({"error": "USER_NOT_FOUND"}), 404

        wallet = db.wallet.find_one({"user_id": ObjectId(user["_id"])})

        if not wallet:
            return jsonify({"error": "WALLET_NOT_FOUND"}), 404



        # Attach the payment method to the user
        payment_method = stripe.PaymentMethod.attach(
            payment_intent["payment_method"], customer=user["stripe_customer_id"]
        )

        stripe.Customer.modify(
            payment_intent["customer"],
            invoice_settings={"default_payment_method": payment_method["id"]},
        )
        if payment_intent["invoice"] is not None:
            db.transactions.insert_one(
                {
                    "user_id": user["_id"],
                    "amount": payment_intent["amount"],
                    "currency": payment_intent["currency"],
                    "status": payment_intent["status"],
                    "payment_method": payment_intent["payment_method"],
                    # "product_name": payment_intent["items"]["plan"]["nickname"]
                    "created_at": datetime.datetime.now(),
                }
            )

        # Log wallet order
        if payment_intent.get("metadata") and payment_intent["metadata"].get("wallet_type") == "wallet":
            tokens = int(payment_intent["metadata"]["tokens"])
            db.wallet_orders.insert_one(
                {
                    "user_id": ObjectId(payment_intent["metadata"]["user_id"]),
                    "tokens": tokens,
                    "wallet_id": wallet["_id"],
                    "amount": payment_intent["amount"],
                    "currency": payment_intent["currency"],
                    "status": payment_intent["status"],
                    "payment_intent": payment_intent["id"],
                    "created_at": datetime.datetime.now(),
                }
            )
            # Update wallet tokens and set updated_at
            db.wallet.update_one(
                {"_id": wallet["_id"]},
                {
                    "$inc": {
                        "availableTokens": tokens,
                        "totalPurchasedTokens": tokens,
                        "amountPaid": payment_intent["amount"],
                    },
                    "$set": {
                        "updated_at": datetime.datetime.now()
                    }
                }
            )

    if event["type"] == "customer.subscription.created":
        subscription = event["data"]["object"]
        # user = User.find_by_stripe_customer_id(subscription["customer"])
        user = db.users.find_one({"stripe_customer_id": subscription["customer"]})

        if not user:
            return (
                jsonify({"error": USER_NOT_FOUND}),
                404,
            )

        subscription_end_date = datetime.datetime.fromtimestamp(
            subscription.get("current_period_end", "")
        )

        if subscription_end_date is not None or subscription_end_date != "":
            formatted_date = subscription_end_date.strftime("%b %d, %Y")
        else:
            formatted_date = ""

        # Update the user's subscription status
        db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "subscription_status": subscription["status"],
                    "product_name": subscription["items"]["data"][0].plan.nickname,
                    "subscription_end_date": formatted_date,
                    "subscription_interval": subscription["items"]["data"][0]["price"][
                        "recurring"
                    ]["interval"]
                    + "ly",
                }
            },
        )

        # if subscription.get("status") == "active":
        #     db.wallet.update_one(
        #         {"user_id": ObjectId(user["_id"])},
        #         {
        #             "$inc": {"availableTokens": DEFAULT_TOKENS_AT_SUBSCRIPTION},
        #             "$set": {"updated_at": datetime.datetime.now()},
        #         },
        #         upsert=True
        #     )
        # else:
        #     # Handle the case where the subscription is not active
        #     # You can log an error, raise an exception, or simply pass
        #     print("Subscription is not active. Wallet update is skipped.")


    if event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        # user = User.find_by_stripe_customer_id(subscription["customer"])
        user = db.users.find_one({"stripe_customer_id": subscription["customer"]})

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Update the user's subscription status
        db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "subscription_status": "deleted",
                    "subscription_end_date": "",
                    "subscription_interval": "",
                }
            },
        )
    if event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        user = db.users.find_one({"stripe_customer_id": invoice["customer"]})
        
        if user:
            # Notify user about the failed payment, etc.
            return jsonify({"message": "Payment failed"}), 200

    if event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        # Handle failed payment intent
        handle_failed_payment_intent(payment_intent)

    if event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        # user = User.find_by_stripe_customer_id(subscription["customer"])
        user = db.users.find_one({"stripe_customer_id": subscription["customer"]})
        if not user:
            return jsonify({"error": "User not found"}), 404
        wallet = db.wallet.find_one({"user_id": ObjectId(user["_id"])})
        subscription_end_date = datetime.datetime.fromtimestamp(
            subscription.get("current_period_end", "")
        )

        if subscription_end_date is not None or subscription_end_date != "":
            formatted_date = subscription_end_date.strftime("%b %d, %Y")
        else:
            formatted_date = ""
        if subscription["cancel_at_period_end"]:
            # Update the user's subscription status
            db.users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "subscription_status": "canceled",
                        "subscription_end_date": formatted_date,
                        "subscription_interval": "",
                    }
                },
            )
        else:
            # Update the user's subscription status
            db.users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "subscription_status": subscription["status"],
                        "product_name": subscription["items"]["data"][0].plan.nickname,
                        "subscription_end_date": formatted_date,
                        "subscription_interval": subscription["items"]["data"][0][
                            "price"
                        ]["recurring"]["interval"]
                        + "ly",
                    }
                },
            )

            # Update wallet tokens and set updated_at
            db.wallet.update_one(
                {"_id": wallet["_id"]},
                {
                    "$inc": {
                        "availableTokens": DEFAULT_TOKENS_AT_SUBSCRIPTION,
                    },
                    "$set": {
                        "updated_at": datetime.datetime.now()
                    }
                }
            )


    return jsonify(
        {
            "message": WEBHOOK_RECEIVED,
            "data": {"event": event["type"]},
        }
    )


def stripe_webhook_wallet(data):
    # payload = data.decode("utf-8")
    # sig_header = request.headers.get("Stripe-Signature")
    # try:
    #     event = stripe.Webhook.construct_event(
    #         payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
    #     )
    # except ValueError as e:
    #     # Invalid payload
    #     return jsonify({"error": str(e)}), 400
    # except stripe.error.SignatureVerificationError as e:
    #     # Invalid signature
    #     return jsonify({"error": str(e)}), 400

    # # Handle the event
    # if event["type"] == "payment_intent.succeeded":
    #     print('event["data"]',event["data"])
    #     payment_intent = event["data"]["object"]

    #     # Find the user in the database from customer ID
    #     # user = User.find_by_stripe_customer_id(payment_intent["customer"])
    #     user = db.users.find_one({"stripe_customer_id": payment_intent["customer"]})
    #     wallet = db.wallet.find_one({"user_id":payment_intent["metadata"]["user_id"]})
    #     if not user:
    #         return (
    #             jsonify({"error": USER_NOT_FOUND}),
    #             404,
    #         )

    #     # Attach the payment method to the user
    #     payment_method = stripe.PaymentMethod.attach(
    #         payment_intent["payment_method"], customer=user["stripe_customer_id"]
    #     )

    #     stripe.Customer.modify(
    #         payment_intent["customer"],
    #         invoice_settings={"default_payment_method": payment_method["id"]},
    #     )
    #     if payment_intent["metadata"]["type"] === "wallet"
    #         db.waller_orders.insert_one({
    #             "user_id": payment_intent["metadata"]["user_id"],
    #             "tokens": payment_intent["metadata"]["tokens"],
    #             "wallet_id": wallet._id,
    #             "amount": payment_intent["amount"],
    #             "currency": payment_intent["currency"],
    #             "status": payment_intent["status"],

    #         })    
    return jsonify(
        {
            "message": WEBHOOK_RECEIVED,
            "data": "test",
        }
    )


def handle_failed_payment_intent(payment_intent):
    """
    Handle a failed payment intent.

    Args:
        payment_intent (dict): The Stripe payment intent object.

    Returns:
        None
    """
    customer_id = payment_intent.get("customer")
    amount = payment_intent.get("amount")
    currency = payment_intent.get("currency")
    error_message = payment_intent.get("last_payment_error", {}).get("message", "Unknown error")

    # Find the user in the database from customer ID
    user = db.users.find_one({"stripe_customer_id": customer_id})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Log the failed payment attempt
    db.failed_payments.insert_one(
        {
            "user_id": user["_id"],
            "amount": amount,
            "currency": currency,
            "status": "failed",
            "error_message": error_message,
            "created_at": datetime.datetime.now(),
        }
    )

    # Optionally, send a notification to the user about the failed payment
    # notify_user_of_failed_payment(user, amount, currency, error_message)

    # You could also choose to update the user's subscription status, revoke access, etc.
