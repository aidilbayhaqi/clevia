import json
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.prompts import SYSTEM_PROMPT
from app.agents.tools.registry import TOOL_SCHEMAS, execute_tool
from app.core.config import settings
from app.db.models.conversation import Conversation, Message
from app.services.safety import classify_risk, emergency_response

class CleviaAgent:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY or None)

    async def run(
        self, db: AsyncSession, *, conversation: Conversation,
        user_message: str, history: list[Message],
    ) -> dict:
        if classify_risk(user_message) == "emergency":
            conversation.risk_level = "emergency"
            return {"message": emergency_response(), "tools_used": []}

        input_items: list = []
        for msg in history[-12:]:
            input_items.append({
                "role":"assistant" if msg.role=="assistant" else "user",
                "content":msg.content,
            })
        input_items.append({"role":"user","content":user_message})
        trace: list[dict] = []

        for _ in range(settings.MAX_AGENT_STEPS):
            response = await self.client.responses.create(
                model=settings.OPENAI_MODEL,
                reasoning={"effort":settings.OPENAI_REASONING_EFFORT},
                instructions=SYSTEM_PROMPT,
                input=input_items,
                tools=TOOL_SCHEMAS,
                parallel_tool_calls=False,
            )
            input_items += response.output
            calls = [item for item in response.output if item.type=="function_call"]

            if not calls:
                return {"message":response.output_text,"tools_used":trace}

            for call in calls:
                args = json.loads(call.arguments)
                result = await execute_tool(
                    db, clinic_id=conversation.clinic_id,
                    conversation=conversation, name=call.name, arguments=args,
                )
                trace.append({"name":call.name,"arguments":args,"result":result})
                input_items.append({
                    "type":"function_call_output",
                    "call_id":call.call_id,
                    "output":json.dumps(result,ensure_ascii=False,default=str),
                })

        raise RuntimeError("Agent exceeded MAX_AGENT_STEPS")
