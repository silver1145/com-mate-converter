from typing import Optional

from textual.suggester import SuggestFromList


class FormatSuggester(SuggestFromList):
    async def get_suggestion(self, value: str) -> Optional[str]:
        index = value.rfind("{")
        if index >= 0:
            sugg = await super().get_suggestion(value[index:])
            if sugg is not None:
                return value[:index] + sugg
        return None
