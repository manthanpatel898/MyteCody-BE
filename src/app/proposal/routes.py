from flask_smorest import Blueprint
from src.app.auth.schema import StandardResponseSchema
from src.app.proposal.schema import AddEpicSchema, AddStorySchema, AddTaskSchema, ChatPayload, DeleteEpicSchema, DeleteStorySchema, DeleteTaskSchema, SaveStep1Prompt, UpdateBusinessVerticalSchema, UpdateEpicSchema, UpdateStakeHoldersSchema, UpdateStorySchema, UpdateTaskSchema
from src.app.proposal.services import add_new_epic, add_new_story, add_new_task, chat_conversation, delete_epic_by_id, delete_existing_story, delete_existing_task, delete_proposal, fetch_epics, fetch_stories_by_epic_and_stakeholder, fetch_tasks_by_story, generate_epics, generate_proposal_details, generate_story_basedon_epics, generate_tasks_basedon_stories, generateDetailReport, get_business_vertical, get_conversation, get_project_vision, get_revenue_model, get_stakeholders, save_conversation, save_project_vision, update_business_vertical, update_existing_epic, update_existing_story, update_existing_task, update_stakeholders
from flask_jwt_extended import jwt_required, current_user

proposals = Blueprint("proposal", __name__, url_prefix="/api/proposal", description="Proposal API")

@proposals.route('/generate/conversation', methods=['POST'])
@proposals.arguments(ChatPayload)
@proposals.response(201, StandardResponseSchema)
@jwt_required()
def user_chat_conversation(args):
    """CONVERSATION FOR GATHERING PROJECT REQUIREMENTS"""
    user = current_user  # Assuming `current_user` is injected via JWT
    print("🚀 ~ user:", user)
    return chat_conversation(args, user_id=user["_id"])
    

@proposals.route("/get/conversation/<string:proposal_id>", methods=["GET"])
# @proposals.response(201, StandardResponseSchema)
@jwt_required()
def get_project_conversation(proposal_id):
    """
    API Endpoint to get the conversation for a specific proposal.
    
    This route retrieves the conversation for a given proposal ID for the authenticated user.
    """
    user = current_user  # Assumes current_user is retrieved from JWT
    return get_conversation(user_id=user["_id"], proposal_id=proposal_id)

@proposals.route("/generate/conversation/save/<string:proposal_id>", methods=["POST"])
@proposals.response(201, StandardResponseSchema)
@jwt_required()
def save_chat_conversation(proposal_id):
    """
    API Endpoint to save the user conversation for a specific proposal.

    This route triggers the background save of the conversation for the given proposal ID.
    """
    user = current_user  # Get the current authenticated user from JWT
    return save_conversation(user_id=user["_id"], proposal_id=proposal_id)

@proposals.route("/get/projectVision/<string:proposal_id>", methods=["GET"])
# @proposals.response(201, StandardResponseSchema)
@jwt_required()
def get_user_project_vision(proposal_id):
    """
    API Endpoint to get the project vision for a specific proposal.

    Parameters:
        proposal_id (str): The ID of the proposal whose project vision is being retrieved.

    Returns:
        (dict): A response containing the project vision or an error message.
    """
    user = current_user  # Get the current authenticated user from JWT
    return get_project_vision(user_id=user["_id"], proposal_id=proposal_id)

@proposals.route("/save/vision", methods=["POST"])
@proposals.arguments(SaveStep1Prompt, location="json")
@proposals.response(201, StandardResponseSchema)
@jwt_required()
def save_step1_prompt(body):
    """
    API Endpoint to save the user's project vision for step 1.

    Parameters:
        body (dict): The payload containing project vision and proposal information.

    Returns:
        (dict): A response indicating the status of the operation, along with the project vision data.
    """
    user = current_user  # Get the current authenticated user from JWT
    return save_project_vision(payload=body, user_id=user["_id"])

@proposals.route("/get/businessVertical/<string:proposal_id>", methods=["GET"])
@jwt_required()
def get_user_business_vertical(proposal_id):
    """
    API Endpoint to get the business vertical for a specific proposal.

    Parameters:
        proposal_id (str): The ID of the proposal whose business vertical is being retrieved.

    Returns:
        (dict): A response containing the business vertical or an error message.
    """
    user = current_user  # Get the current authenticated user from JWT
    return get_business_vertical(user_id=user["_id"], proposal_id=proposal_id)

@proposals.route("/update/businessVertical", methods=["POST"])
@proposals.arguments(UpdateBusinessVerticalSchema, location="json")
@proposals.response(201, StandardResponseSchema)
@jwt_required()
def update_existing_business_vertical(body):
    """
    API Endpoint to update the business vertical for step 2.

    Parameters:
        body (dict): JSON payload containing the proposal ID and the new business vertical data.

    Returns:
        (dict): A JSON response indicating the success or failure of the update.
    """
    user = current_user  # Get the current authenticated user from JWT
    return update_business_vertical(payload=body, user_id=user["_id"])


@proposals.route("/get/stakeholders/<string:proposal_id>", methods=["GET"])
@jwt_required()
def featch_stackholders(proposal_id):
    """
    API Endpoint to fetch stakeholders for step 3 in the proposal process.

    Parameters:
        proposal_id (str): The ID of the proposal whose stakeholders are being retrieved.

    Returns:
        (dict): A JSON response containing the stakeholders or an error message.
    """
    user = current_user  # Get the current authenticated user from JWT
    return get_stakeholders(proposal_id, user_id=user["_id"])


@proposals.route("/update/stakeholders", methods=["POST"])
@proposals.arguments(UpdateStakeHoldersSchema, location="json")
@jwt_required()
def update_business_users(payload):
    """
    API Endpoint to update stakeholders for step 3 in the proposal process.

    Parameters:
        payload (dict): The JSON payload containing the proposal ID and stakeholders.

    Returns:
        (dict): A JSON response indicating the success or failure of the update operation.
    """
    user = current_user  # Get the current authenticated user from JWT
    return update_stakeholders(payload=payload, user_id=user["_id"])

@proposals.route("/get/revenuemodel/<string:proposal_id>", methods=["GET"])
@jwt_required()
def fetch_revenue_model(proposal_id):
    """
    API Endpoint to fetch the revenue model for step 4 in the proposal process.

    Parameters:
        proposal_id (str): The ID of the proposal whose revenue model is being retrieved.

    Returns:
        (dict): A JSON response containing the revenue model or an error message.
    """
    user = current_user  # Get the current authenticated user from JWT
    return get_revenue_model(proposal_id, user_id=user["_id"])

@proposals.route("/generate/epics/<string:proposal_id>", methods=["POST"])
@jwt_required()
def epics_generate(proposal_id):
    """
    API Endpoint to generate epics for step 5 of the proposal process.

    Parameters:
        proposal_id (str): The ID of the proposal for which epics are being generated.

    Returns:
        (dict): A JSON response indicating the success or failure of the epic generation operation.
    """
    user = current_user  # Get the current authenticated user from JWT
    return generate_epics(proposal_id=proposal_id, user_id=user["_id"], user_email=user["email"])

@proposals.route("/addEpic", methods=["POST"])
@jwt_required()
@proposals.arguments(AddEpicSchema, location="json")
def add_epic(payload):
    """
    API to add a new epic under a specific stakeholder.

    Parameters:
        payload (dict): JSON containing proposal_id, stakeholder, title, and description.

    Returns:
        (dict): Response indicating the success or failure of the epic creation.
    """
    user = current_user  # Fetch current user from JWT
    return add_new_epic(payload=payload, user_id=user["_id"])

@proposals.route("/updateEpic", methods=["PUT"])
@jwt_required()
@proposals.arguments(UpdateEpicSchema, location="json")
def update_epic(payload):
    """
    API to update an existing epic under a specific stakeholder.

    Parameters:
        payload (dict): JSON containing proposal_id, stakeholder, epic_id, title, and description.

    Returns:
        (dict): Response indicating the success or failure of the epic update.
    """
    user = current_user  # Fetch current user from JWT
    return update_existing_epic(payload=payload, user_id=user["_id"])

@proposals.route("/deleteEpic", methods=["DELETE"])
@jwt_required()
@proposals.arguments(DeleteEpicSchema, location="json")
def delete_epic(payload):
    """
    API to delete an epic from a specific stakeholder's list.

    Parameters:
        payload (dict): JSON containing proposal_id, stakeholder, and epic_id.

    Returns:
        (dict): Response indicating the success or failure of the deletion operation.
    """
    user = current_user  # Fetch current user from JWT
    return delete_epic_by_id(payload=payload, user_id=user["_id"])

@proposals.post("/generate/storie/<string:proposal_id>")
@jwt_required()
def stories_generate(proposal_id):
    """
    API to generate stories for epics for a specific proposal.

    Parameters:
        proposal_id (str): The ID of the proposal whose epics' stories are being generated.

    Returns:
        (dict): Response indicating success or failure of story generation.
    """
    user = current_user
    return generate_story_basedon_epics(
        proposal_id=proposal_id, user_id=user["_id"], user_email=user["email"]
    )

@proposals.post("/generate/tasks/<string:proposal_id>")
@jwt_required()
def tasks_generate(proposal_id):
    """
    API to generate stories for epics for a specific proposal.

    Parameters:
        proposal_id (str): The ID of the proposal whose epics' stories are being generated.

    Returns:
        (dict): Response indicating success or failure of story generation.
    """
    user = current_user
    return generate_tasks_basedon_stories(
        proposal_id=proposal_id, user_id=user["_id"], user_email=user["email"]
    )

@proposals.post("/add/story")
@proposals.arguments(AddStorySchema, location="json")
@jwt_required()
def add_story(body):
    """
    API endpoint to add a new story to a specific epic for a stakeholder in a proposal.

    Parameters:
        body (dict): Contains proposal_id, stakeholder, epic_id, title, description, and acceptance_criteria.
    
    Returns:
        (dict): Response with success or error message and the new story details.
    """
    user = current_user
    return add_new_story(payload=body, user_id=user["_id"])


@proposals.post("/add/task")
@proposals.arguments(AddTaskSchema, location="json")
@jwt_required()
def add_task(body):
    """
    API endpoint to add a new task to a specific story within an epic for a stakeholder in a proposal.

    Parameters:
        body (dict): Contains proposal_id, stakeholder, epic_id, story_id, description, and complexity.

    Returns:
        (dict): Response with success or error message and the new task details.
    """
    user = current_user
    return add_new_task(payload=body, user_id=user["_id"])

@proposals.put("/update/story")
@proposals.arguments(UpdateStorySchema, location="json")
@jwt_required()
def update_story(body):
    """
    API endpoint to update an existing story in a specific epic for a stakeholder in a proposal.

    Parameters:
        body (dict): Contains proposal_id, stakeholder, epic_id, story_id, title, description, and acceptance_criteria.

    Returns:
        (dict): Response with success or error message and the updated story details.
    """
    user = current_user
    return update_existing_story(payload=body, user_id=user["_id"])

@proposals.route("/update/task", methods=["PUT"])
@proposals.arguments(UpdateTaskSchema, location="json")
@jwt_required()
def update_task(body):
    """
    API Endpoint to update an existing task for a story in an epic.

    Expected Payload:
    {
        "proposal_id": "proposal_id",
        "stakeholder": "stakeholder_name",
        "epic_id": "epic_id",
        "story_id": "story_id",
        "task_id": "task_id",
        "description": "Updated task description",
        "complexity": "Medium"
    }

    Returns:
        (dict): Success message with updated task details or error message.
    """
    user = current_user
    # Call the service to update the task
    return update_existing_task(payload=body, user_id=user["_id"])

@proposals.route("/delete/story", methods=["DELETE"])
@proposals.arguments(DeleteStorySchema, location="json")
@jwt_required()
def delete_story(body):
    """
    API Endpoint to delete an existing story from a specific epic.

    Expected Payload:
    {
        "proposal_id": "proposal_id",
        "stakeholder": "stakeholder_name",
        "epic_id": "epic_id",
        "story_id": "story_id"
    }

    Returns:
        (dict): Success message or error message if the story is not found.
    """
    user = current_user

    # Call the service to delete the story
    return delete_existing_story(payload=body, user_id=user["_id"])

@proposals.route("/delete/task", methods=["DELETE"])
@proposals.arguments(DeleteTaskSchema, location="json")
@jwt_required()
def delete_task(body):
    """
    API Endpoint to delete an existing task from a specific story.

    Expected Payload:
    {
        "proposal_id": "proposal_id",
        "stakeholder": "stakeholder_name",
        "epic_id": "epic_id",
        "story_id": "story_id",
        "task_id": "task_id"
    }

    Returns:
        (dict): Success message or error message if the task is not found.
    """
    user = current_user

    # Call the service to delete the task
    return delete_existing_task(payload=body, user_id=user["_id"])

@proposals.route("/stories/<string:proposal_id>/<string:stakeholder>/<string:epic_id>", methods=["GET"])
@jwt_required()
def fetch_stories(proposal_id, stakeholder, epic_id):
    """
    API Endpoint to fetch all stories for a specific epic and stakeholder.

    Parameters:
        proposal_id (str): The ID of the proposal.
        stakeholder (str): The name of the stakeholder.
        epic_id (str): The ID of the epic for which stories need to be fetched.

    Returns:
        (dict): A response with the list of stories or an error message.
    """
    user = current_user
    # Call the service to fetch all stories based on the epic_id and stakeholder
    return fetch_stories_by_epic_and_stakeholder(proposal_id, stakeholder, epic_id, user["_id"])

@proposals.route("/tasks/<string:proposal_id>/<string:stakeholder>/<string:epic_id>/<string:story_id>", methods=["GET"])
@jwt_required()
def fetch_tasks(proposal_id, stakeholder, epic_id, story_id):
    """
    API Endpoint to fetch tasks for a specific story based on proposal ID, stakeholder, epic ID, and story ID.

    Parameters:
        proposal_id (str): The ID of the proposal.
        stakeholder (str): The name of the stakeholder.
        epic_id (str): The ID of the epic.
        story_id (str): The ID of the story.

    Returns:
        (dict): A response with the list of tasks or an error message.
    """
    user = current_user
    return fetch_tasks_by_story(proposal_id, stakeholder, epic_id, story_id, user["_id"])

@proposals.get("/epics/<string:proposal_id>/<string:stakeholder>")
@jwt_required()
def get_epics_by_stakeholder(proposal_id, stakeholder):
    """
    GET Epics based on proposal ID and stakeholder.

    Parameters:
        proposal_id (str): The ID of the proposal.
        stakeholder (str): The name of the stakeholder.

    Returns:
        JSON: A response containing the list of epics for the given stakeholder.
    """
    user = current_user
    return fetch_epics(proposal_id, stakeholder, user["_id"])

@proposals.route("/delete/proposal/<string:proposal_id>", methods=["DELETE"])
@jwt_required()
def delete_proposal_route(proposal_id):
    """
    API endpoint to delete a proposal and its related conversation based on the proposal ID.

    Parameters:
        proposal_id (str): The ID of the proposal to be deleted.

    Returns:
        (dict): A standard response indicating success or failure.
    """
    user = current_user
    return delete_proposal(proposal_id=proposal_id, user_id=user["_id"])

@proposals.route("/generate/detail/report/<string:proposal_id>", methods=["GET"])
@jwt_required()
def generate_proposal_report(proposal_id):
    """
    API endpoint to generate detailed proposal report.

    Parameters:
        proposal_id (str): The ID of the proposal to generate the report for.

    Returns:
        (dict): A JSON response with the generated report details or an error message.
    """
    user = current_user
    # Generate detailed report for the proposal
    return generateDetailReport(proposal_id, user["_id"])
    