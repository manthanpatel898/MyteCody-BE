from flask import request
from flask_jwt_extended import jwt_required, current_user
from flask_smorest import Blueprint
from src.app.wallet.services import attach_payment_method_service, fetch_payment_methods_service, get_wallet_info_service, recharge_wallet_service

wallet_bp = Blueprint("wallet", __name__, url_prefix="/wallet", description="Wallet API")

@wallet_bp.route("/info", methods=["GET"])
@jwt_required()
def get_wallet_info():
    """
    API endpoint to get user's wallet information.
    
    Returns:
        (dict): A standard JSON response with wallet information or error message.
    """
    user = current_user
    return get_wallet_info_service(user["_id"])

@wallet_bp.route("/recharge", methods=["POST"])
@jwt_required()
def recharge_wallet():
    """
    API endpoint to recharge user's wallet.

    Body:
        amount (float): The amount to recharge the wallet with.

    Returns:
        (dict): A standard JSON response with payment intent or error message.
    """
    user = current_user
    amount = request.json.get('amount')
    return recharge_wallet_service(user["_id"], amount)

@wallet_bp.route("/payment-methods", methods=["GET"])
@jwt_required()
def get_payment_methods():
    """
    API endpoint to fetch user's payment methods from Stripe.
    
    Returns:
        (dict): A standard JSON response with payment methods or error message.
    """
    user = current_user
    return fetch_payment_methods_service(user["_id"])

@wallet_bp.route("/attach-payment-method", methods=["POST"])
@jwt_required()
def add_payment_method():
    """
    API endpoint to attach a new payment method to the user.

    Body:
        paymentMethodId (str): The Stripe payment method ID.

    Returns:
        (dict): A standard JSON response with attached payment method or error message.
    """
    user = current_user
    payment_method_id = request.json.get('paymentMethodId')
    return attach_payment_method_service(user["_id"], payment_method_id)
