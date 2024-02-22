import dataclasses


@dataclasses.dataclass
class Config:
    mate_format: str
    menu_process_mode: int
    pmat_check_mode: int
    cpu_percent: float
    backup: bool
