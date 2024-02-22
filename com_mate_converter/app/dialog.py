from typing import List

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label

from com_mate_converter import CMC_Config, _


class QuitScreen(ModalScreen):
    def compose(self) -> ComposeResult:
        yield Container(
            Label(_("[b]Are you sure you want to quit?"), id="question"),
            Label(
                _(
                    "[bright_red]Task is still running.\nExiting can result in corrupted mod files,\nespecially when processing Menu/Pmat."
                )
            ),
            Label(),
            Horizontal(
                Button(_("Quit"), variant="error", id="confirm", classes="dialog-button"),
                Button(_("Cancel"), variant="primary", id="cancel", classes="dialog-button"),
            ),
            id="quit-dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)


class WorkConfirmScreen(ModalScreen):
    def __init__(self, input_paths: List, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.input_paths = input_paths

    def compose(self) -> ComposeResult:
        yield Container(
            Label(_("Start to process?"), id="question"),
            Label(
                _("[grey100]Work Dirs:\n  [green3]")
                + "\n  ".join(self.input_paths[:3] + (["..."] if len(self.input_paths[:4]) == 4 else []))
                + "\n\n"
                + _(
                    "[grey100]Option:\n  [dodger_blue1]mate_format = '{mate_format}'\n  menu_process_mode = {menu_process_mode}\n  pmat_check_mode = {pmat_check_mode}\n  cpu_percent = {cpu_percent:.0%}\n  backup = {backup}"
                ).format(
                    mate_format=CMC_Config.config.mate_format,
                    menu_process_mode=CMC_Config.config.menu_process_mode,
                    pmat_check_mode=CMC_Config.config.pmat_check_mode,
                    cpu_percent=CMC_Config.config.cpu_percent,
                    backup=CMC_Config.config.backup,
                )
                + "\n"
            ),
            Horizontal(
                Button(_("Confirm"), variant="primary", id="confirm", classes="dialog-button"),
                Button(_("Cancel"), variant="default", id="cancel", classes="dialog-button"),
            ),
            id="work-dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)
