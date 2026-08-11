import json

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.prompts import SYSTEM_PROMPT
from app.agents.tools.registry import TOOL_SCHEMAS, execute_tool
from app.core.config import settings
from app.db.models.conversation import Conversation, Message
from app.services.safety import classify_risk, emergency_response


class CleviaAgent:
    """
    Clevia AI orchestrator.

    OpenAI client dibuat secara lazy supaya seluruh FastAPI backend tetap
    dapat boot walaupun OPENAI_API_KEY belum dikonfigurasi.
    """

    def _get_client(self) -> AsyncOpenAI:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. "
                "Set it in .env and restart the API container."
            )

        return AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY
        )

    async def run(
        self,
        db: AsyncSession,
        *,
        conversation: Conversation,
        user_message: str,
        history: list[Message],
    ) -> dict:
        # Emergency handling bersifat deterministic dan tidak bergantung
        # kepada koneksi OpenAI.
        if classify_risk(user_message) == "emergency":
            conversation.risk_level = "emergency"
            return {
                "message": emergency_response(),
                "tools_used": [],
            }

        client = self._get_client()

        input_items: list = []

        for message in history[-12:]:
            input_items.append(
                {
                    "role": (
                        "assistant"
                        if message.role == "assistant"
                        else "user"
                    ),
                    "content": message.content,
                }
            )

        input_items.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        tool_trace: list[dict] = []

        for _ in range(settings.MAX_AGENT_STEPS):
            response = await client.responses.create(
                model=settings.OPENAI_MODEL,
                reasoning={
                    "effort": settings.OPENAI_REASONING_EFFORT,
                },
                instructions=SYSTEM_PROMPT,
                input=input_items,
                tools=TOOL_SCHEMAS,
                parallel_tool_calls=False,
            )

            input_items += response.output

            function_calls = [
                item
                for item in response.output
                if item.type == "function_call"
            ]

            if not function_calls:
                return {
                    "message": response.output_text,
                    "tools_used": tool_trace,
                }

            for function_call in function_calls:
                arguments = json.loads(
                    function_call.arguments
                )

                result = await execute_tool(
                    db,
                    clinic_id=conversation.clinic_id,
                    conversation=conversation,
                    name=function_call.name,
                    arguments=arguments,
                )

                tool_trace.append(
                    {
                        "name": function_call.name,
                        "arguments": arguments,
                        "result": result,
                    }
                )

                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": function_call.call_id,
                        "output": json.dumps(
                            result,
                            ensure_ascii=False,
                            default=str,
                        ),
                    }
                )

        raise RuntimeError(
            "Agent exceeded MAX_AGENT_STEPS"
        )
