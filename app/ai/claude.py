import anthropic
from app.config import Settings


class ClaudeClient:
    def __init__(self, settings: Settings):
        self._api_key = settings.anthropic_api_key
        self._model = settings.claude_model
        self._client = None

    def _get_client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def complete(self, system: str, user: str, max_tokens: int = 2048) -> str:
        client = self._get_client()
        response = client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text

    def complete_with_tools(
        self,
        system: str,
        messages: list,
        tools: list,
        max_tokens: int = 2048,
    ) -> anthropic.types.Message:
        client = self._get_client()
        return client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            tools=tools,
        )
