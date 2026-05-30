"""Anthropic-backed structured-output prompt caller.

This is the Fair Witness analogue of TableThat's ``BasePromptCaller`` (which
targets OpenAI). It gives every orchestration stage the same contract:

    caller = SomePromptCaller()
    result: SomePydanticModel = await caller.invoke(user_content="...")

Structured output is obtained by handing the model a single tool whose
``input_schema`` is the Pydantic model's JSON schema and forcing
``tool_choice`` to that tool. Claude must then "call" the tool with arguments
that match the schema, which we validate back into the Pydantic model.

A single shared ``AsyncAnthropic`` client is reused across all callers so the
fan-out stage can issue many concurrent requests cheaply.
"""

import logging
from typing import Optional, Type

import anthropic
from pydantic import BaseModel

from config.settings import settings

logger = logging.getLogger(__name__)

_shared_client: Optional[anthropic.AsyncAnthropic] = None


def get_shared_client() -> anthropic.AsyncAnthropic:
    global _shared_client
    if _shared_client is None:
        _shared_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _shared_client


_TOOL_NAME = "emit_result"


def _inline_refs(schema: dict) -> dict:
    """Resolve a Pydantic JSON schema's ``$defs``/``$ref`` into an inlined schema.

    Anthropic accepts ``$ref`` in tool input schemas, but a fully self-contained
    schema is more reliably honored — in particular it reduces Claude's tendency
    to emit nested arrays as JSON strings under forced ``tool_choice``.
    """
    defs = schema.get("$defs", {})

    def resolve(node):
        if isinstance(node, dict):
            if "$ref" in node:
                ref = node["$ref"].split("/")[-1]
                target = defs.get(ref, {})
                merged = {k: v for k, v in node.items() if k != "$ref"}
                return resolve({**target, **merged})
            return {k: resolve(v) for k, v in node.items() if k != "$defs"}
        if isinstance(node, list):
            return [resolve(item) for item in node]
        return node

    return resolve({k: v for k, v in schema.items() if k != "$defs"})


class BasePromptCaller:
    """Base class for structured, single-shot Claude calls."""

    def __init__(
        self,
        response_model: Type[BaseModel],
        system_message: str,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ):
        self.response_model = response_model
        self.system_message = system_message
        self.model = model or settings.CLAUDE_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = get_shared_client()

    def _tool_definition(self) -> dict:
        return {
            "name": _TOOL_NAME,
            "description": (
                f"Return the {self.response_model.__name__} result. "
                "You MUST call this tool exactly once with fully-populated arguments. "
                "Provide array fields as native JSON arrays of objects — never as a "
                "string containing JSON."
            ),
            # Inline $defs so Claude sees a self-contained schema; this markedly
            # reduces the array-as-string serialization quirk under forced tools.
            "input_schema": _inline_refs(self.response_model.model_json_schema()),
        }

    async def invoke(self, user_content: str, max_attempts: int = 2) -> BaseModel:
        """Run the prompt and return a validated instance of ``response_model``.

        On a validation failure we retry once with the validation error fed back
        to the model, which reliably fixes occasional structured-output drift.
        """
        messages = [{"role": "user", "content": user_content}]

        last_error: Optional[Exception] = None
        for attempt in range(1, max_attempts + 1):
            response = await self._create(messages)
            tool_block = next(
                (b for b in response.content if getattr(b, "type", None) == "tool_use"),
                None,
            )
            if tool_block is None:
                last_error = RuntimeError("Model did not return a structured result.")
                logger.warning(f"{self.response_model.__name__}: no tool_use block (attempt {attempt})")
                continue

            try:
                return self.response_model.model_validate(tool_block.input)
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Validation failed for {self.response_model.__name__} "
                    f"(attempt {attempt}/{max_attempts}): {e}"
                )
                if attempt < max_attempts:
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": tool_block.id,
                            "is_error": True,
                            "content": (
                                f"Your result failed schema validation:\n{e}\n\n"
                                "Call the tool again with corrected arguments. Ensure "
                                "all required fields are present and every array is a "
                                "native JSON array (not a string)."
                            ),
                        }],
                    })

        logger.error(f"Failed to get valid {self.response_model.__name__}: {last_error}")
        raise last_error if last_error else RuntimeError("Structured output failed.")

    async def _create(self, messages: list):
        try:
            return await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_message,
                tools=[self._tool_definition()],
                tool_choice={"type": "tool", "name": _TOOL_NAME},
                messages=messages,
            )
        except anthropic.APIStatusError as e:
            logger.error(f"Anthropic API error ({e.status_code}): {e.message}")
            raise RuntimeError(f"Anthropic API error: {e.message}") from e
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise RuntimeError(f"Anthropic API error: {e}") from e
