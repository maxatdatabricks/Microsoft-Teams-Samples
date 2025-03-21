# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from botbuilder.core import TurnContext, MessageFactory
from botbuilder.schema import HeroCard, CardAction, ActionTypes, Mention, Attachment
from botbuilder.core.teams import TeamsActivityHandler
from html import escape

from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

# Load required Databricks variables from the .env file into the environment.
load_dotenv()

# WorkspaceClient is used to interact with the Databricks workspace.
# Default authentication flow uses the DATABRICKS_HOST, DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET environment variables.
w = WorkspaceClient()

class BotActivityHandler(TeamsActivityHandler):
    def __init__(self):
        super().__init__()

        # Registers an activity event handler for the message activity event.
        # This is triggered whenever the bot receives a message.
        self.on_message_activity = self.handle_message

    async def handle_message(self, turn_context: TurnContext):
        """
        Handles incoming messages sent to the bot.

        Args:
            turn_context (TurnContext): Provides context for the current turn of conversation.
        """
        # Removes any mention of the bot in the received message text (e.g., "@BotName Hello").
        turn_context.remove_recipient_mention(turn_context.activity)

        # Extract the user's message text and strip any extra spaces.
        user_message = turn_context.activity.text.strip()

        # Extract model name from the environment and raise error if unset or blank.
        model_name = os.getenv("DATABRICKS_MODEL_NAME", "").strip()
        if not model_name:
            raise ValueError("DATABRICKS_MODEL_NAME environment variable is not set or is empty. Check your ./env/.env.local file.")
        
        # Send the user's message to the Databricks model for processing.
        raw_response = w.serving_endpoints.query(
            name=model_name,
            messages=[
                ChatMessage(
                    role=ChatMessageRole.SYSTEM, content="You are a helpful assistant." # Note: you could provide a better set of instructions.
                ),
                ChatMessage(
                    role=ChatMessageRole.USER, content=user_message
                ),
            ],
            max_tokens=128,
        )

        response = raw_response.choices[0].message.content

        # Send the response from the Databricks model to the user.
        await turn_context.send_activity(MessageFactory.text(response))

