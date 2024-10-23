import dataclasses
import json
from pathlib import Path
from typing import Dict, List

import regex
from loguru import logger

from com_mate_converter.i18n import _
from com_mate_converter.model import Config, FormatVariable


class CMC_Config:
    config: Config = Config(
        mate_format="{mate_name}_{shader_family}",
        menu_process_mode=0,
        pmat_check_mode=0,
        cpu_percent=0.6,
        backup=True,
    )

    shader_names: Dict[str, str] = {}
    shader_families: Dict[str, str] = {}
    # config path
    config_file: Path = Path.cwd() / "config" / "config.json"
    shader_names_file: Path = Path.cwd() / "config" / "ShaderNames.json"
    shader_families_file: Path = Path.cwd() / "config" / "ShaderFamilies.json"
    # ui
    example_mate_format_variable: FormatVariable = FormatVariable(
        mate_name="example",
        shader_family="npr",
        shader_name="_NPRToonV2_",
    )
    variable_pattern: regex.Pattern = regex.compile(r"\{([^}]+)\}")

    class SafeDict(dict):
        def __missing__(self, key):
            if key.lower() in self:
                return self[key.lower()].upper()
            return f"{{{key}}}"

    @staticmethod
    def get_format_variables() -> List[str]:
        return [
            "{mate_name}",
            "{shader_family}",
            "{shader_name}",
            "{MATE_NAME}",
            "{SHADER_FAMILY}",
            "{SHADER_NAME}",
        ]

    @staticmethod
    def read_config():
        if CMC_Config.config_file.exists():
            try:
                with CMC_Config.config_file.open("r", encoding="utf-8") as f:
                    config_dict = json.load(f)
                    if (mate_format := config_dict.get("mate_format")) is not None:
                        CMC_Config.config.mate_format = mate_format
                    if (menu_process_mode := config_dict.get("menu_process_mode")) is not None:
                        CMC_Config.config.menu_process_mode = menu_process_mode
                    if (pmat_check_mode := config_dict.get("pmat_check_mode")) is not None:
                        CMC_Config.config.pmat_check_mode = pmat_check_mode
                    if (cpu_percent := config_dict.get("cpu_percent")) is not None:
                        CMC_Config.config.cpu_percent = cpu_percent
                    if (backup := config_dict.get("backup")) is not None:
                        CMC_Config.config.backup = backup
            except Exception:
                logger.warning(_("Failed to load ui config."))
        if CMC_Config.shader_names_file.exists():
            try:
                shader_names = {}
                with CMC_Config.shader_names_file.open("r", encoding="utf-8") as f:
                    ori_shader_names = json.load(f)
                    for k, v in ori_shader_names.items():
                        shader_names[k.lower()] = v
                CMC_Config.shader_names = shader_names
            except Exception:
                logger.warning(_("Failed to load shader names."))
        if CMC_Config.shader_families_file.exists():
            try:
                with CMC_Config.shader_families_file.open("r", encoding="utf-8") as f:
                    families = json.load(f)
                    shader_families = {}
                    for k, v in families.items():
                        for shader_name in v:
                            shader_families[shader_name.lower()] = k
                    CMC_Config.shader_families = shader_families
            except Exception:
                logger.warning(_("Failed to load shader families."))

    @logger.catch
    @staticmethod
    def write_config():
        if not CMC_Config.config_file.parent.exists():
            CMC_Config.config_file.parent.mkdir(parents=True, exist_ok=True)
        with CMC_Config.config_file.open("w", encoding="utf-8") as f:
            json.dump(dataclasses.asdict(CMC_Config.config), f, indent=4)

    @staticmethod
    def get_new_mate_name(format_variable: FormatVariable) -> str:
        variable_dict = dataclasses.asdict(format_variable)
        variable_dict = CMC_Config.SafeDict(variable_dict)
        return (
            CMC_Config.variable_pattern.sub(lambda match: variable_dict[match.group(1)], CMC_Config.config.mate_format)
            + ".mate"
        )

    @staticmethod
    def get_new_example_mate_name() -> str:
        variable_dict = CMC_Config.SafeDict(dataclasses.asdict(CMC_Config.example_mate_format_variable))
        return (
            CMC_Config.variable_pattern.sub(lambda match: variable_dict[match.group(1)], CMC_Config.config.mate_format)
            + ".mate"
        )

    @staticmethod
    def is_shader_info_valid():
        return len(CMC_Config.shader_names) > 0
