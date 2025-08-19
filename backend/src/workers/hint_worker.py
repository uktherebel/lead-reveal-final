from typing import Dict, Any 
from src.workers.base_worker import BaseWorker
from src.prompts.hint_prompt import _HINT_PROMPT

class HintWorker(BaseWorker):
    def _setup(self):
        self.chain = _HINT_PROMPT | self.llm

    async def process(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        try:
            msg = await self.execute_with_retry(lambda: self.chain.ainvoke(ctx))
            hint = msg.content if hasattr(msg, "content") else str(msg)
            return {"success": True, "hint": hint.strip()}
        except Exception as e:
            return await self.handle_error(e, {"stage": "hint"})