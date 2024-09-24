"""COMMON FUNCTIONS USED IN THE PROJECT"""

import os
from flask import jsonify
from dotenv import load_dotenv
from flask_jwt_extended import jwt_required, current_user
# from src.app.utils.constants import AI_Model, temperature, max_tokens
from cryptography.fernet import Fernet
from bson import ObjectId
import hashlib
import base64
from src.app.proposal.schema import ProposalUsageSchema
from src.db import db
import openai
import datetime

proposal_usage_collection = db["proposal_usage"]
wallet_collection = db["wallet"]

proposal_usage_schema = ProposalUsageSchema()
load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")


def log_proposal_usage(user_id, proposal_id, tokens_used):
    """Logs the usage of a proposal."""
    current_time = datetime.datetime.utcnow().isoformat()  # Convert datetime to ISO format

    proposal_usage = {
        "user_id": str(user_id),
        "proposal_id": str(proposal_id),
        "model_calls": 1,
        "tokens_used": tokens_used,
        "created_at": current_time,
        "updated_at": current_time
    }

    # Validate the data using the schema
    errors = proposal_usage_schema.validate(proposal_usage)
    if errors:
        raise ValueError(f"Invalid data: {errors}")

    proposal_usage_collection.update_one(
        {"user_id": ObjectId(user_id), "proposal_id": ObjectId(proposal_id)},
        {
            "$inc": {
                "model_calls": 1,
                "tokens_used": tokens_used
            },
            "$setOnInsert": {
                "user_id": ObjectId(user_id),
                "proposal_id": ObjectId(proposal_id),
                "created_at": current_time
            },
            "$set": {
                "updated_at": current_time  # Always update the updated_at field
            }
        },
        upsert=True
    )

    # Check if the user has a wallet
    wallet_record = wallet_collection.find_one({"user_id": ObjectId(user_id)})
    if wallet_record:
        # Update the wallet collection if the wallet record exists
        wallet_collection.update_one(
            {"user_id": ObjectId(user_id)},
            {
                "$inc": {
                    "availableTokens": -tokens_used,
                    "consumedTokens": tokens_used
                },
                "$set": {
                    "updated_at": current_time  # Update the updated_at field in wallet
                }
            }
        )

def log_token_usage(proposal_id, user_id, utilized_tokens):
    try:
        log_entry = {
            "proposal_id": ObjectId(proposal_id),
            "user_id": ObjectId(user_id),
            "utilized_tokens": utilized_tokens,
            "created_at": datetime.datetime.now()
        }
        db.token_usages_logs.insert_one(log_entry)
    except Exception as e:
        print(f"Error logging token usage: {e}")
        # Handle the exception as needed

# Decrypt the openApiKey
def decrypt_open_api_key(encrypted_key, encryption_key):
    fernet = Fernet(encryption_key)
    decrypted_key = fernet.decrypt(encrypted_key).decode()
    return decrypted_key

# Generate a key for encryption based on the email address
def generate_hash_key(email):
    email = email.strip().lower()
    hash_object = hashlib.sha256(email.encode())
    hash_key = hash_object.digest()[:32]  # Use the first 32 bytes
    fernet_key = base64.urlsafe_b64encode(hash_key)
    return fernet_key

# Retrieve and decrypt the openApiKey from the database
def get_open_api_key(user_id):
    try:
        user = db.users.find_one({"_id": ObjectId(user_id)})
        encryption_key = generate_hash_key(user['email'])

        if not user or "open_api_key" not in user:
            raise ValueError("Open API Key not found for user")

        encrypted_key = user["open_api_key"]
        decrypted_key = decrypt_open_api_key(encrypted_key, encryption_key)
        print("🚀 ~ decrypted_key:", decrypted_key)

        return {"message": "Open API Key retrieved successfully", "open_api_key": decrypted_key}
    except ValueError as ve:
        print("Validation Error:", ve)
        response = jsonify({"error": str(ve)})
        response.status_code = 400
        return response
    except Exception as e:
        print("Error in retrieving Open API Key", e)
        response = jsonify({"error": "Internal Server Error"})
        response.status_code = 500
        return response
    
# def generate_prompt_response(context, assistant, message):
#     """Generate a response to a prompt using OpenAI's GPT-3.5 model."""
#     user =current_user["_id"]
#     OPENAI_API_KEY = get_open_api_key(user)["open_api_key"]
#     prompt_template = [
#         ("system", context),
#         ("assistant", assistant),
#         ("human", message),
#     ]

#     model = ChatOpenAI(model=AI_Model, max_tokens=max_tokens, temperature=temperature, api_key=OPENAI_API_KEY)  # type: ignore

#     response = model.invoke(prompt_template)

#     output_parser = StrOutputParser()
#     data = output_parser.parse(response.content)  # type: ignore

#     data = data[len("```json") :] if data.startswith("```json") else data
#     data = data.replace("```", "") if data.endswith("```") else data
#     return data

model_call_counter = 0

def generate_text_json(system_context, assistant_context, initial_prompt,user_id, proposal_id):
    # openai_client = OpenAI(api_key=OPENAI_API_KEY)

    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=14000,
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": system_context},
            {"role": "assistant", "content": assistant_context},
            {"role": "user", "content": initial_prompt}
        ]
    )


    tokens_used = response.usage.total_tokens
    log_proposal_usage(user_id, proposal_id, tokens_used)
    log_token_usage(user_id, proposal_id, tokens_used)
    
    return response.choices[0].message.content

def generate_text(system_context, assistant_context, initial_prompt,user_id, proposal_id):
    # openai_client = OpenAI(api_key=OPENAI_API_KEY)
    openai.api_key = api_key

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=14000,

        messages=[
            {"role": "system", "content": system_context},
            {"role": "assistant", "content": assistant_context},
            {"role": "user", "content": initial_prompt}
        ]
    )

    tokens_used = response.usage.total_tokens
    log_proposal_usage(user_id, proposal_id, tokens_used)
    log_token_usage(user_id, proposal_id, tokens_used)
    return response.choices[0].message.content

def generate_text_json_with_4o(system_context, assistant_context, initial_prompt,user_id, proposal_id):
    # openai_client = OpenAI(api_key=OPENAI_API_KEY)
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        # model="gpt-4o",
        # temperature=0.1,
        # max_tokens=3000,
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=14000,
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": system_context},
            {"role": "assistant", "content": assistant_context},
            {"role": "user", "content": initial_prompt}
        ]
    )

    tokens_used = response.usage.total_tokens
    log_proposal_usage(user_id, proposal_id, tokens_used)
    log_token_usage(user_id, proposal_id, tokens_used)
    
    return response.choices[0].message.content
def generate_text_with_4o(system_context, assistant_context, initial_prompt,user_id, proposal_id):
    # openai_client = OpenAI(api_key=OPENAI_API_KEY)
    openai.api_key = api_key

    response = openai.ChatCompletion.create(
        # model="gpt-4o",
        # temperature=0.1,
        # max_tokens=3000,
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=14000,
        messages=[
            {"role": "system", "content": system_context},
            {"role": "assistant", "content": assistant_context},
            {"role": "user", "content": initial_prompt}
        ]
    )

    tokens_used = response.usage.total_tokens
    log_proposal_usage(user_id, proposal_id, tokens_used)
    log_token_usage(user_id, proposal_id, tokens_used)
    
    return response.choices[0].message.content

def generate_text_with_4o_for_conversation(system_context, assistant_context, initial_prompt,user_id, proposal_id):
    # openai_client = OpenAI(api_key=OPENAI_API_KEY)
    openai.api_key = api_key

    response = openai.ChatCompletion.create(
        model="gpt-4o-2024-08-06",
        temperature=0.1,
        max_tokens=3000,

        messages=[
            {"role": "system", "content": system_context},
            {"role": "assistant", "content": assistant_context},
            {"role": "user", "content": initial_prompt}
        ]
    )

    tokens_used = response.usage.total_tokens
    log_proposal_usage(user_id, proposal_id, tokens_used)
    log_token_usage(user_id, proposal_id, tokens_used)
    
    return response.choices[0].message.content

def get_open_api_tokens():
    openai.api_key = api_key

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=14000,
            messages=[
                {"role": "system", "content": "Welcome to the chat. How can I assist you today?"},
                {"role": "assistant", "content": "I can help you with various tasks. What do you need?"},
                {"role": "user", "content": "How many tokens have I used?"}
            ]
        )

        # Extract the total number of tokens from the response
        total_tokens = response.usage.total_tokens

        return total_tokens
    
    except Exception as e:
        print(f"Error fetching token info: {e}")
        raise

def voice_to_text(file_data):
    openai.api_key = api_key

    try:
        response = openai.Audio.transcribe(
            model="whisper-1",
            file=file_data
        )

        return response.get('text', '')
    
    except Exception as e:
        print(f"Error fetching token info: {e}")
        raise
