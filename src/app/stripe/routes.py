# src/app/subscription/routes.py
from flask import request, jsonify, redirect, url_for
from flask_jwt_extended import current_user, get_jwt_identity, jwt_required
from flask_smorest import Blueprint
import stripe
from src import db
from src.app.stripe.services import stripe_webhook, stripe_webhook_wallet

stripe_bp = Blueprint("stripe", __name__, url_prefix="/stripe", description="stripe API")

@stripe_bp.route("/webhook", methods=["POST"])
def webhook():
    """
    Handle the Stripe webhook.

    This function is responsible for handling the Stripe webhook events.
    It calls the stripe_webhook function with the request data and returns the result.

    Returns:
        The result of the stripe_webhook function.
    """
    return stripe_webhook(request.data)

@stripe_bp.route("/webhook/wallet", methods=["POST"])
def webhook_wallet():
    """
    Handle the Stripe webhook.

    This function is responsible for handling the Stripe webhook events.
    It calls the stripe_webhook function with the request data and returns the result.

    Returns:
        The result of the stripe_webhook function.
    """
    return stripe_webhook_wallet(request.data)