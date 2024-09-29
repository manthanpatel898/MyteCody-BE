# src/app/subscription/routes.py

from flask_jwt_extended import current_user, jwt_required
from flask_smorest import Blueprint
from src.app.subscription.schema import Wallet
from src.app.subscription.services import create_billing_session, create_payment_intent, verify_subscription

subscription_bp = Blueprint("subscription", __name__, url_prefix="/api/subscription", description="Subscription API")

@subscription_bp.route("/create-payment-intent", methods=["GET"])
@jwt_required()
def create_intent():
    """
    Create a payment intent.

    This function takes a JSON object containing the payment information and
    creates a payment intent using the Stripe API.

    Returns:
        The result of the create_payment_intent function.
    """
    user = current_user
    return create_payment_intent(user["_id"])

@subscription_bp.route("/verify-subscription", methods=["GET"])
@jwt_required()
def verify_subscription_route():
    """
    Verify the subscription status.

    This function takes a JSON object containing the customer information and
    verifies the subscription status using the Stripe API.

    Returns:
        The result of the verify_subscription function.
    """
    user = current_user
    return verify_subscription(user["_id"])


@subscription_bp.route("/create-billing-session", methods=["GET"])
@jwt_required()
def billing_session():
    """
    Create a billing session.

    This function takes a JSON object containing the customer information and
    creates a billing session using the Stripe API.

    Returns:
        The result of the create_billing_session function.
    """
    user = current_user
    return create_billing_session(user["_id"])