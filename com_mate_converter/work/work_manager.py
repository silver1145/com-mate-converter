import os
import threading
import time
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

import py7zr
from loguru import logger
from textual.message import Message

from com_mate_converter import _
from com_mate_converter.config import CMC_Config
from com_mate_converter.model import FormatVariable, Mate, Menu, Pmat
from com_mate_converter.model.mate import FloatProperty

from .binary_replace import BinaryReplace
from .work_thread import BackupThread, WorkPoolThread


class WorkType(IntEnum):
    Mate = 0
    Menu = 1
    Pmat = 2
    Finished = 3


class WorkCommand(Message):
    def __init__(self, work_type: WorkType) -> None:
        super().__init__()
        self.work_type = work_type


class WorkProgress(Message):
    def __init__(self, percentage: float) -> None:
        super().__init__()
        self.percentage = percentage


class WorkManager:
    send_message_callback: Callable[[Message], bool]
    work_pool_thread: Optional[WorkPoolThread] = None
    backup_thread: Optional[BackupThread] = None
    # Files
    work_dirs: List[Path]
    mate_list: List[Path]
    menu_list: List[Tuple[Path, Path]]
    pmat_list: List[Tuple[Path, Path]]
    # Work
    finish_counter: int = 0
    finish_counter_lock: threading.Lock
    backup_dict: Dict[Path, Path]
    mate_pmat_set: Set[str]
    mate_proc_list: List[Path]
    mate_pass_list: List[Path]
    mate_name_dict: Dict[str, str]
    menu_pass_list: List[Path]
    pmat_change_list: List[Path]
    pmat_pass_list: List[Path]
    pmat_fname_change_list: List[Path]

    def __init__(self, send_message_callback: Callable[[Message], bool]) -> None:
        self.send_message_callback = send_message_callback
        self.work_dirs = []
        self.mate_list = []
        self.menu_list = []
        self.pmat_list = []
        self.backup_dict = dict()
        self.finish_counter_lock = threading.Lock()
        self.mate_pmat_set = set()
        self.mate_proc_list = []
        self.mate_pass_list = []
        self.mate_name_dict = dict()
        self.menu_pass_list = []
        self.pmat_change_list = []
        self.pmat_pass_list = []
        self.pmat_fname_change_list = []

    def kill_work_thread(self) -> None:
        if self.backup_thread is not None:
            self.backup_thread.kill()
        if self.work_pool_thread is not None:
            self.work_pool_thread.kill()

    def stop_work_thread(self) -> None:
        if self.backup_thread is not None:
            self.backup_thread.stop()
        if self.work_pool_thread is not None:
            self.work_pool_thread.stop()

    def clear(self) -> None:
        self.work_dirs.clear()
        self.mate_list.clear()
        self.menu_list.clear()
        self.pmat_list.clear()
        self.backup_dict.clear()
        self.mate_pmat_set.clear()
        self.mate_proc_list.clear()
        self.mate_pass_list.clear()
        self.mate_name_dict.clear()
        self.menu_pass_list.clear()
        self.pmat_change_list.clear()
        self.pmat_pass_list.clear()
        self.pmat_fname_change_list.clear()
        self.finish_counter = 0

    def counter_add(self) -> None:
        with self.finish_counter_lock:
            self.finish_counter += 1

    def report_failed(self) -> None:
        report_path = Path.cwd() / "failed_or_pass_list.txt"
        if len(self.mate_pass_list) + len(self.menu_pass_list) + len(self.pmat_pass_list) == 0:
            if report_path.exists():
                os.remove(report_path)
            return
        with report_path.open("w", encoding="utf-8") as f:
            for p in self.mate_pass_list:
                f.write(f"{p.as_posix()}\n")
            for p in self.menu_pass_list:
                f.write(f"{p.as_posix()}\n")
            for p in self.pmat_pass_list:
                f.write(f"{p.as_posix()}\n")

    def start_process_mate(self, paths: List[str], is_cancelled: Callable[[], bool]) -> None:
        if self.work_pool_thread is not None and not self.work_pool_thread.is_stopped():
            logger.error(_("A Work Thread Pool is still running"))
            self.send_message_callback(WorkCommand(WorkType.Finished))
            return
        self.clear()
        logger.info(_("Searching..."))
        logger.debug(_("Search for Mate..."))
        self._glob_mates(paths, is_cancelled)
        logger.info(_("[royal_blue1]Found {num} NPR Mate").format(num=len(self.mate_list)))
        if len(self.mate_list) == 0:
            self.send_message_callback(WorkCommand(WorkType.Finished))
            return
        self.work_pool_thread = WorkPoolThread(self.process_mate, self.mate_list, self.process_mate_finish)
        self.work_pool_thread.start()
        logger.info(_("Processing Mate..."))

    @logger.catch
    def process_mate(self, mate_path: Path) -> None:
        if "_NPRMAT" not in mate_path.stem:
            self.mate_pass_list.append(mate_path)
            logger.warning(_("Ignore Mate (no NPRMAT): {filename}").format(filename=mate_path.name))
            return
        mate_name, shader_filename = mate_path.stem.split("_NPRMAT")
        try:
            with mate_path.open("rb") as f:
                mate = Mate.parse(f.read())
        except:
            self.mate_pass_list.append(mate_path)
            logger.warning(_("Failed to Read Mate: {filename}").format(filename=mate_path.name))
            return
        shader_name = CMC_Config.shader_names.get(shader_filename.lower())
        if shader_name is None:
            self.mate_pass_list.append(mate_path)
            logger.warning(_("Ignore Mate (Unknown Shader): {filename}").format(filename=mate_path.name))
            return
        self.mate_pmat_set.add(mate.material.name)
        mate.material.shader = shader_name
        mate.material.shader_filename = f"com3d2mod{shader_filename}"
        new_mate_name = CMC_Config.get_new_mate_name(
            FormatVariable(
                mate_name=mate_name,
                shader_family=CMC_Config.shader_families.get(shader_filename) or "npr",
                shader_name=shader_filename,
            )
        )
        new_mate_path = mate_path.parent / new_mate_name
        index = 1
        while new_mate_path.exists():
            new_mate_name = CMC_Config.get_new_mate_name(
                FormatVariable(
                    mate_name=f"{mate_name}_{index}",
                    shader_family=CMC_Config.shader_families.get(shader_filename) or "npr",
                    shader_name=shader_filename,
                )
            )
            new_mate_path = mate_path.parent / new_mate_name
        mate_path.rename(new_mate_path)
        mate.mate_name = new_mate_name[:-5]
        if shader_filename.startswith("_NPRToon"):
            for p in mate.material.properties:
                if type(p) is FloatProperty:
                    if "Toggle" in p.prop.name:
                        p.prop.name += "_ON_SSKEYWORD"
        try:
            data = mate.build()
        except:
            self.mate_pass_list.append(mate_path)
            logger.warning(_("Failed to Process Mate: {filename}").format(filename=mate_path.name))
            return
        self.mate_name_dict[mate_path.name.lower()] = new_mate_name
        with new_mate_path.open("wb") as f:
            f.write(data)
        self.mate_proc_list.append(new_mate_path)
        self.counter_add()
        self.send_message_callback(
            WorkProgress((self.finish_counter + len(self.mate_pass_list)) / len(self.mate_list) * 100)
        )

    def process_mate_finish(self) -> None:
        if CMC_Config.config.backup and self.mate_proc_list:
            if lst := list(self.backup_dict.values()):
                backup_folder = lst[0].parent
            else:
                backup_folder = Path.cwd() / "backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_folder.mkdir(parents=True, exist_ok=True)
            backup_path = backup_folder / "new_file_list.txt"
            if backup_path.exists():
                with backup_path.open("a", encoding="utf-8") as f:
                    for p in self.mate_proc_list:
                        f.write(f"{p.as_posix()}\n")
            else:
                with backup_path.open("w", encoding="utf-8") as f:
                    for p in self.mate_proc_list:
                        f.write(f"{p.as_posix()}\n")
        self.send_message_callback(WorkCommand(WorkType.Menu))

    @logger.catch
    def _glob_mates(self, paths: List[str], is_cancelled: Callable[[], bool]) -> None:
        self.mate_list.clear()
        mate_list: List[Path] = []
        backup_path: Optional[Path] = None
        backup_filenames: Set[str] = set()
        curr_datetime: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        for p in paths:
            p = Path(p)
            if p.exists():
                if p.is_dir():
                    self.work_dirs.append(p)
                    cur_list = list(p.glob("**/*_NPRMAT_*.mate"))
                    if CMC_Config.config.backup:
                        if backup_path is None:
                            backup_path = Path.cwd() / "backup" / curr_datetime
                            backup_path.mkdir(parents=True, exist_ok=True)
                        backup_filename = p.name
                        backup_filepath = backup_path / f"{backup_filename}.7z"
                        index = 1
                        while backup_filename in backup_filenames or backup_filepath.exists():
                            backup_filename = f"{p.name}_{index}"
                            backup_filepath = backup_path / f"{backup_filename}.7z"
                        backup_filenames.add(backup_filename)
                        self.backup_dict[p] = backup_filepath
                        if cur_list:
                            logger.info(
                                _('Backuping to "{b_name}"').format(
                                    b_name=backup_filepath.relative_to(Path.cwd() / "backup")
                                )
                            )
                            with py7zr.SevenZipFile(backup_filepath, "w") as archive:
                                for mate_p in cur_list:
                                    if is_cancelled():
                                        return
                                    archive.write(mate_p, str(mate_p.relative_to(p.parent)))
                    mate_list += cur_list
        self.mate_list = mate_list

    def start_process_menu(self) -> None:
        if self.work_pool_thread is not None and not self.work_pool_thread.is_stopped():
            logger.error(_("A Work Thread Pool is still running"))
            self.send_message_callback(WorkCommand(WorkType.Finished))
            return
        if self.backup_thread is not None and not self.backup_thread.is_stopped():
            logger.error(_("A Backup Thread is still running"))
            self.backup_thread.stop()
            self.send_message_callback(WorkCommand(WorkType.Finished))
            return
        self.finish_counter = 0
        logger.debug(_("Search for Menu..."))
        self._glob_menus()
        logger.info(_("[royal_blue1]Found {num} Menu").format(num=len(self.menu_list)))
        if len(self.menu_list) == 0:
            self.send_message_callback(WorkCommand(WorkType.Pmat))
            return
        if CMC_Config.config.menu_process_mode == 1:
            BinaryReplace.compile_pattern(self.mate_name_dict)
        if CMC_Config.config.backup:
            self.backup_thread = BackupThread(self.backup_dict)
            self.backup_thread.start()
        self.work_pool_thread = WorkPoolThread(self.process_menu, self.menu_list, self.process_menu_finish)
        self.work_pool_thread.start()
        logger.info(_("Processing Menu..."))

    @logger.catch
    def process_menu(self, menu_p: Tuple[Path, Path]) -> None:
        work_path, menu_path = menu_p
        with menu_path.open("rb") as f:
            data = f.read()
        changed = False
        if CMC_Config.config.menu_process_mode == 0:
            try:
                menu = Menu.parse(data)
            except:
                self.counter_add()
                self.menu_pass_list.append(menu_path)
                logger.warning(_("Failed to Read Menu: {filename}").format(filename=menu_path.name))
                return
            for c in menu.commands:
                if (args_len := len(c.args)) > 1 and c.args[0] == "マテリアル変更":
                    for i in range(1, args_len):
                        arg_lower = c.args[i].lower()
                        if "_nprmat_" in arg_lower and arg_lower.endswith(".mate"):
                            if (new_mate_name := self.mate_name_dict.get(arg_lower)) is not None:
                                c.args[i] = new_mate_name
                                changed = True
            if changed:
                try:
                    new_data = menu.build()
                except:
                    self.counter_add()
                    self.menu_pass_list.append(menu_path)
                    logger.warning(_("Failed to Process Menu: {filename}").format(filename=menu_path.name))
                    return
        elif CMC_Config.config.menu_process_mode == 1:
            new_data = BinaryReplace.replace(data)
            if new_data != data:
                changed = True
        if changed:
            with menu_path.open("wb") as f:
                f.write(new_data)
            if CMC_Config.config.backup and self.backup_thread is not None:
                self.backup_thread.add_backup(work_path, menu_path, data)
        self.counter_add()
        self.send_message_callback(WorkProgress((self.finish_counter) / len(self.menu_list) * 100))

    @logger.catch
    def process_menu_finish(self) -> None:
        if self.backup_thread is not None:
            self.backup_thread.stop()
            while self.backup_thread.is_alive():
                time.sleep(0.1)
            logger.debug(_("Backup Mate Finished"))
        self.send_message_callback(WorkCommand(WorkType.Pmat))

    @logger.catch
    def _glob_menus(self) -> None:
        self.menu_list.clear()
        menu_list: List[Tuple[Path, Path]] = []
        for p in self.work_dirs:
            for m in p.glob("**/*.menu"):
                menu_list.append((p, m))
        self.menu_list = menu_list

    def start_process_pmat(self) -> None:
        if self.work_pool_thread is not None and not self.work_pool_thread.is_stopped():
            logger.error(_("A Work Thread Pool is still running"))
            self.send_message_callback(WorkCommand(WorkType.Finished))
            return
        if self.backup_thread is not None and not self.backup_thread.is_stopped():
            logger.error(_("A Backup Thread is still running"))
            self.backup_thread.stop()
            self.send_message_callback(WorkCommand(WorkType.Finished))
            return
        if CMC_Config.config.pmat_check_mode == 2:
            self.send_message_callback(WorkCommand(WorkType.Finished))
            return
        self.finish_counter = 0
        logger.debug(_("Search for Pmat..."))
        self._glob_pmats()
        logger.info(_("[royal_blue1]Found {num} Pmat").format(num=len(self.pmat_list)))
        if len(self.pmat_list) == 0:
            self.send_message_callback(WorkCommand(WorkType.Finished))
            return
        if CMC_Config.config.backup:
            self.backup_thread = BackupThread(self.backup_dict)
            self.backup_thread.start()
        self.work_pool_thread = WorkPoolThread(self.process_pmat, self.pmat_list, self.process_pmat_finish)
        self.work_pool_thread.start()
        logger.info(_("Processing Pmat..."))

    @logger.catch
    def process_pmat(self, pmat_p: Tuple[Path, Path]) -> None:
        work_path, pmat_path = pmat_p
        with pmat_path.open("rb") as f:
            data = f.read()
        try:
            pmat = Pmat.parse(data)
        except:
            self.counter_add()
            self.pmat_pass_list.append(pmat_path)
            logger.warning(_("Failed to Read Pmat: {filename}").format(filename=pmat_path.name))
            return
        changed = False
        pmat_new_filepath: Optional[Path] = None
        pmat_filename = pmat_path.stem
        pmat_mat_name = pmat.material_name
        if pmat_filename != pmat_mat_name:
            if pmat_filename in self.mate_pmat_set and pmat_mat_name not in self.mate_pmat_set:
                logger.info(_("[white]Detect Wrong [MatName] Pmat: {filename}").format(filename=pmat_path.name))
                if CMC_Config.config.pmat_check_mode == 0:
                    changed = True
                    pmat.material_name = pmat_filename
            elif pmat_filename not in self.mate_pmat_set and pmat_mat_name in self.mate_pmat_set:
                logger.info(_("[white]Detect Wrong [FileName] Pmat: {filename}").format(filename=pmat_path.name))
                if CMC_Config.config.pmat_check_mode == 0:
                    changed = True
                    pmat_new_filepath = pmat_path.parent / f"{pmat_mat_name}.pmat"
            else:
                logger.info(_("[white]Detect Pmat with Potential Error: {filename}").format(filename=pmat_path.name))
        if changed:
            if CMC_Config.config.backup and self.backup_thread is not None:
                self.backup_thread.add_backup(work_path, pmat_path, data)
            try:
                new_data = pmat.build()
                with pmat_path.open("wb") as f:
                    f.write(new_data)
                if pmat_new_filepath is not None:
                    self.pmat_fname_change_list.append(pmat_path)
                    pmat_path.rename(pmat_new_filepath)
            except:
                self.pmat_pass_list.append(pmat_path)
                logger.warning(_("Failed to Process Pmat: {filename}").format(filename=pmat_path.name))
        self.counter_add()
        self.send_message_callback(WorkProgress((self.finish_counter) / len(self.pmat_list) * 100))

    @logger.catch
    def process_pmat_finish(self) -> None:
        if self.backup_thread is not None:
            self.backup_thread.stop()
            while self.backup_thread.is_alive():
                time.sleep(0.1)
            logger.debug(_("Backup Pmat Finished"))
        if CMC_Config.config.backup and self.pmat_fname_change_list:
            if lst := list(self.backup_dict.values()):
                backup_folder = lst[0].parent
            else:
                backup_folder = Path.cwd() / "backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_folder.mkdir(parents=True, exist_ok=True)
            backup_path = backup_folder / "new_file_list.txt"
            if backup_path.exists():
                with backup_path.open("a", encoding="utf-8") as f:
                    for p in self.pmat_fname_change_list:
                        f.write(f"{p.as_posix()}\n")
            else:
                with backup_path.open("w", encoding="utf-8") as f:
                    for p in self.pmat_fname_change_list:
                        f.write(f"{p.as_posix()}\n")
        self.send_message_callback(WorkCommand(WorkType.Finished))

    @logger.catch
    def _glob_pmats(self) -> None:
        self.pmat_list.clear()
        pmat_list: List[Tuple[Path, Path]] = []
        for p in self.work_dirs:
            for m in p.glob("**/*.pmat"):
                pmat_list.append((p, m))
        self.pmat_list = pmat_list
