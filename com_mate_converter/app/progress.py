from typing import Optional

from rich.console import RenderableType
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from textual.widgets import Static


class CustomProgress(Static):
    def __init__(
        self,
        description: str = "",
        total: int = 100,
        renderable: RenderableType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__(
            renderable=renderable, expand=expand, shrink=shrink, markup=markup, name=name, id=id, classes=classes
        )
        self._bar = Progress("{task.description}", BarColumn(), TaskProgressColumn())
        self._task_id = self._bar.add_task(description, total=total)

    def on_mount(self) -> None:
        self._bar.update(self._task_id, completed=0)
        self.update(self._bar)

    def update_progress_bar(self, percent) -> None:
        self._bar.update(self._task_id, completed=percent)
        self.update(self._bar)


class CustomTimeProgress(Static):
    def __init__(
        self,
        description: str = "",
        total: int = 100,
        renderable: RenderableType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__(
            renderable=renderable, expand=expand, shrink=shrink, markup=markup, name=name, id=id, classes=classes
        )
        self._bar = Progress(
            "{task.description}",
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        )
        self._task_id = self._bar.add_task(description, total=total)

    def on_mount(self) -> None:
        self._bar.update(self._task_id, completed=0)
        self.update(self._bar)

    def update_progress_bar(self, percent) -> None:
        if percent == 0:
            self._bar.reset(self._task_id)
        self._bar.update(self._task_id, completed=percent)
        self.update(self._bar)
