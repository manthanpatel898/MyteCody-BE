import datetime
from wsgiref import validate
from xml.dom import ValidationErr
from marshmallow import Schema, fields

class ChatPayload(Schema):
    proposal_id = fields.String(required=False, allow_none=True)
    data = fields.String(required=True)
    created_at = fields.DateTime(default=datetime.datetime.utcnow)  # Automatically set to current time
    updated_at = fields.DateTime(default=datetime.datetime.utcnow)

class ProposalUsageSchema(Schema):
    user_id = fields.String(required=True)
    proposal_id = fields.String(required=True)
    model_calls = fields.Int(required=True)
    tokens_used = fields.Int(required=True)
    created_at = fields.DateTime(default=datetime.datetime.utcnow)  # Automatically set to current time
    updated_at = fields.DateTime(default=datetime.datetime.utcnow)


class SaveStep1Prompt(Schema):
    project_vision = fields.String(required=True)
    proposal_id = fields.String(required=True)

class UpdateBusinessVerticalSchema(Schema):
    """
    Schema for validating the request body for updating the business vertical.
    """
    proposal_id = fields.String(required=True, description="ID of the proposal to update")
    business_vertical = fields.List(
        fields.String(required=True), 
        description="A list of business verticals to update in the proposal"
    )

class UpdateStakeHoldersSchema(Schema):
    """
    Schema for validating the request body for updating stakeholders.
    """
    proposal_id = fields.String(required=True, description="ID of the proposal to update")
    stake_holders = fields.List(
        fields.String(required=True), 
        description="A list of stakeholders to update in the proposal"
    )

class AddEpicSchema(Schema):
    proposal_id = fields.String(required=True)
    stakeholder = fields.String(required=True)
    title = fields.String(required=True)
    description = fields.String(required=True)

class UpdateEpicSchema(Schema):
    proposal_id = fields.String(required=True)
    stakeholder = fields.String(required=True)
    id = fields.String(required=True)
    title = fields.String(required=True)
    description = fields.String(required=True)

class DeleteEpicSchema(Schema):
    proposal_id = fields.String(required=True)
    stakeholder = fields.String(required=True)
    id = fields.String(required=True)

class AddStorySchema(Schema):
    proposal_id = fields.String(required=True)
    stakeholder = fields.String(required=True)
    epic_id = fields.String(required=True)
    title = fields.String(required=True)
    description = fields.String(required=True)
    acceptance_criteria = fields.List(fields.String(), required=True)  # List of acceptance criteria

class AddTaskSchema(Schema):
    proposal_id = fields.String(required=True)
    stakeholder = fields.String(required=True)
    epic_id = fields.String(required=True)
    story_id = fields.String(required=True)
    description = fields.String(required=True)
    complexity = fields.String(required=True)  # Dropdown for complexity (Very_Simple, Simple, Medium, etc.)

class UpdateStorySchema(Schema):
    proposal_id = fields.String(required=True)
    stakeholder = fields.String(required=True)
    epic_id = fields.String(required=True)
    story_id = fields.String(required=True)
    title = fields.String(required=True)
    description = fields.String(required=True)
    acceptance_criteria = fields.List(fields.String(), required=True)  # List of criteria

class UpdateTaskSchema(Schema):
    proposal_id = fields.String(required=True, error_messages={"required": "Proposal ID is required."})
    stakeholder = fields.String(required=True, error_messages={"required": "Stakeholder is required."})
    epic_id = fields.String(required=True, error_messages={"required": "Epic ID is required."})
    story_id = fields.String(required=True, error_messages={"required": "Story ID is required."})
    task_id = fields.String(required=True, error_messages={"required": "Task ID is required."})
    description = fields.String(required=False)
    complexity = fields.String(required=False)

    # @validate('complexity')
    # def validate_complexity(self, value):
    #     valid_complexities = ["Very_Simple", "Simple", "Medium", "Complex", "Very_Complex"]
    #     if value not in valid_complexities:
    #         raise ValidationErr(f"Invalid complexity level: {value}. Must be one of {valid_complexities}.")

class DeleteStorySchema(Schema):
    proposal_id = fields.String(required=True, error_messages={"required": "Proposal ID is required."})
    stakeholder = fields.String(required=True, error_messages={"required": "Stakeholder is required."})
    epic_id = fields.String(required=True, error_messages={"required": "Epic ID is required."})
    story_id = fields.String(required=True, error_messages={"required": "Story ID is required."})

class DeleteTaskSchema(Schema):
    proposal_id = fields.String(required=True, error_messages={"required": "Proposal ID is required."})
    stakeholder = fields.String(required=True, error_messages={"required": "Stakeholder is required."})
    epic_id = fields.String(required=True, error_messages={"required": "Epic ID is required."})
    story_id = fields.String(required=True, error_messages={"required": "Story ID is required."})
    task_id = fields.String(required=True, error_messages={"required": "Task ID is required."})
