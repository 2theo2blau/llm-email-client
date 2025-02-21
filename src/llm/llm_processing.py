import requests
import json
import os
from src.models.email_models import UnprocessedEmail

class LLMProcessor:
    def __init__(self,
                 db_connection,
                 api_base_url: str,
                 api_key: str,
                 model: str,
                 agent_id: str):
        self.db = db_connection
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.model = model
        self.agent_id = agent_id

    def create_prompt(self, email: UnprocessedEmail) -> str:
        """Expand stored email elements into a prompt for the LLM"""
        return f"""
        Email:
        From: {email.sender}
        Subject: {email.subject}
        Timestamp: {email.timestamp}

        Message Body:
        {email.body}

        Please write a thorough and articulate response to the email above.
        """
    
    def query_llm(self, prompt: str) -> str:
        """Send request to the LLM API and return the response"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            # "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            # "temperature": 1.0,
            "agent_id": self.agent_id,
        }

        response = requests.post(
            f"{self.api_base_url}/v1/agents/completions",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            raise Exception(f"API Request Failed: {response.text}")

        return response.json()["choices"][0]["message"]["content"]
