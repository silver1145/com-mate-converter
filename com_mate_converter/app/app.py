import time
from typing import List, Union

import pyperclip
from loguru import logger
from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.events import Paste
from textual.message import Message
from textual.widgets import (
    Footer,
    Input,
    Label,
    ListItem,
    ListView,
    RichLog,
)
from textual.worker import get_current_worker

from com_mate_converter import CMC_Config, _
from com_mate_converter.work import WorkCommand, WorkManager, WorkProgress, WorkType

from .dialog import QuitScreen, WorkConfirmScreen
from .file_drop import getpaths
from .logo import logo_str
from .progress import CustomTimeProgress
from .suggestor import FormatSuggester


class MainApp(App):
    work_manager: WorkManager
    config: CMC_Config = CMC_Config()
    CSS_PATH = "../css/cmc.css"
    BINDINGS = [
        Binding("ctrl+c", "cancel_and_exit", _("Cancel & Exit"), show=True),
        Binding("ctrl+p", "process_clipboard", _("Process Clipboard"), show=True),
    ]
    # Widget
    text_log: RichLog
    process_percent: CustomTimeProgress
    mate_format_input: Input
    new_mate_name_label: Label
    menu_process_mode_choice: ListView
    pmat_check_mode_choice: ListView
    # Work
    is_working: bool = False
    input_paths: List
    last_time: float

    class LogMessage(Message):
        def __init__(self, text: Union[str, Text]) -> None:
            super().__init__()
            self.text = text

    def compose(self) -> ComposeResult:
        yield Label(_("[b] COM Mate Converter"), id="title")
        yield Container(
            Container(
                RichLog(markup=True, max_lines=1000, id="text-log"),
                CustomTimeProgress("Processing...", id="process-percent"),
                id="left-pane",
            ),
            Vertical(
                Container(
                    Label(_("Mate Name Format"), classes="text-label"),
                    Input(
                        suggester=FormatSuggester(
                            CMC_Config.get_format_variables(),
                            case_sensitive=True,
                        ),
                        id="mate-format-input",
                    ),
                    Label(
                        _("   Example Mate") + ": [blue]example_NPRMAT_NPRToonV2_.mate",
                    ),
                    Label(
                        _("   New MateName") + ": [blue]example_NPRMAT_NPRToonV2_.mate",
                        id="new-mate-name-label",
                    ),
                    id="right-top-pane",
                ),
                Container(
                    Label(_("Menu Process Mode"), classes="text-label"),
                    ListView(
                        ListItem(Label(_("Parse & Replace"))),
                        ListItem(Label(_("Binary Replace"))),
                        id="menu-process-mode-choice",
                    ),
                    Label(_("Pmat Check Mode"), classes="text-label"),
                    ListView(
                        ListItem(Label(_("Check & Fix"))),
                        ListItem(Label(_("Check Only"))),
                        ListItem(Label(_("Ignore"))),
                        id="pmat-check-mode-choice",
                    ),
                    id="right-buttom-pane",
                ),
                id="right-pane",
            ),
            id="app-grid",
        )
        yield Footer()

    def on_ready(self) -> None:
        CMC_Config.read_config()
        self.work_manager = WorkManager(self.post_message)
        self.text_log = self.query_one("#text-log")  # type: ignore
        self.process_percent = self.query_one("#process-percent")  # type: ignore
        self.process_percent.visible = False
        self.mate_format_input = self.query_one("#mate-format-input")  # type: ignore
        self.mate_format_input.insert_text_at_cursor(CMC_Config.config.mate_format)  # type: ignore
        self.new_mate_name_label = self.query_one("#new-mate-name-label")  # type: ignore
        self.new_mate_name_label.update(_("   New MateName") + f": [blue]{CMC_Config.get_new_example_mate_name()}")  # type: ignore
        self.menu_process_mode_choice = self.query_one("#menu-process-mode-choice")  # type: ignore
        self.menu_process_mode_choice.index = CMC_Config.config.menu_process_mode  # type: ignore
        self.pmat_check_mode_choice = self.query_one("#pmat-check-mode-choice")  # type: ignore
        self.pmat_check_mode_choice.index = CMC_Config.config.pmat_check_mode  # type: ignore
        self.print_logo()
        self.print_help()

    def action_cancel_and_exit(self) -> None:
        if self.is_working:
            self.push_screen(QuitScreen(), lambda x: (not x) or self.cancel_and_exit())  # type: ignore
        else:
            self.cancel_and_exit()

    def action_process_clipboard(self) -> None:
        text = pyperclip.paste()
        if text:
            self.post_message(Paste(text))

    def on_paste(self, message: Paste):
        if len(self.screen_stack) > 1 or self.is_working:
            return
        if CMC_Config.is_shader_info_valid():
            self.input_paths = getpaths(message.text)
            if self.input_paths:
                self.push_screen(
                    WorkConfirmScreen(self.input_paths),
                    lambda x: (not x) or self.post_message(WorkCommand(WorkType.Mate)),  # type: ignore
                )
        else:
            logger.error(_("Shader Info is None."))

    async def on_work_command(self, message: WorkCommand) -> None:
        self.process_percent.update_progress_bar(0)
        if message.work_type == WorkType.Mate:
            self.last_time = time.time()
            self.is_working = True
            self.process_percent.visible = True
            self.process_mate_files(self.input_paths)
        elif message.work_type == WorkType.Menu:
            self.process_percent.visible = True
            self.process_menu_files()
        elif message.work_type == WorkType.Pmat:
            self.process_percent.visible = True
            self.process_pmat_files()
        elif message.work_type == WorkType.Finished:
            self.process_percent.visible = False
            self.is_working = False
            self.work_manager.report_failed()
            self.work_manager.clear()
            logger.info(_("[#0087ff]Convert Finished"))
            logger.info(_("[#0087ff]Used: {seconds:.2f} s").format(seconds=time.time() - self.last_time))
            logger.info("----------")

    def on_work_progress(self, message: WorkProgress) -> None:
        self.process_percent.update_progress_bar(message.percentage)

    def on_main_app_log_message(self, message: "MainApp.LogMessage") -> None:
        self.text_log.write(message.text)

    def on_input_changed(self, message: Input.Changed) -> None:
        value = message.value.strip()
        if len(value) > 0 and value != CMC_Config.config.mate_format:
            CMC_Config.config.mate_format = value
            self.new_mate_name_label.update(_("   New MateName") + f": [blue]{self.config.get_new_example_mate_name()}")

    def on_list_view_highlighted(self, message: ListView.Highlighted) -> None:
        list_view = message.list_view
        if list_view.index is None:
            return
        if list_view == self.menu_process_mode_choice and list_view.index != CMC_Config.config.menu_process_mode:
            CMC_Config.config.menu_process_mode = list_view.index
        elif message.list_view == self.pmat_check_mode_choice and list_view.index != CMC_Config.config.pmat_check_mode:
            CMC_Config.config.pmat_check_mode = list_view.index

    @work(exclusive=True, thread=True)
    def process_mate_files(self, paths: List[str]) -> None:
        worker = get_current_worker()
        self.work_manager.start_process_mate(paths, lambda: worker.is_cancelled)

    @work(exclusive=True, thread=True)
    def process_menu_files(self) -> None:
        self.work_manager.start_process_menu()

    @work(exclusive=True, thread=True)
    def process_pmat_files(self) -> None:
        self.work_manager.start_process_pmat()

    def send_log_message(self, text: str) -> None:
        if text.startswith("\x1b"):
            text_t = Text.from_ansi(text=text)
            self.post_message(self.LogMessage(text_t))
        else:
            self.post_message(self.LogMessage(text))

    def cancel_and_exit(self) -> None:
        self.work_manager.stop_work_thread()
        self.work_manager.kill_work_thread()
        self.app.exit()
        CMC_Config.write_config()

    def print_logo(self) -> None:
        self.text_log.write(Text.from_ansi(text=logo_str))

    def print_help(self) -> None:
        self.text_log.write(_("Drag into the mods folder.\nOr copy the path and press Ctrl+P to process it.\n\n"))
