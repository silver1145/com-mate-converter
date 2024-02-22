from typing import Callable, Optional

import loguru

logger_init = False
logger_levels = {
    "CRITICAL": "[#d70000]CRIT [/#d70000]",
    "ERROR": "[#870000]ERROR[/#870000]",
    "WARNING": "[#ffd700]WARN [/#ffd700]",
    "INFO": "[#0087ff]INFO [/#0087ff]",
    "DEBUG": "[#00d700]DEBUG[/#00d700]",
}


class LogFilter:
    def __init__(self, level: str):
        self.level = level

    def __call__(self, record: "loguru.Record"):
        levelno = loguru.logger.level(self.level).no
        return record["level"].no >= levelno


def format_record(record: "loguru.Record") -> str:
    levename = logger_levels[record.get("level").name]
    if record.get("exception") is not None:
        return f"[#808080]{'{:%H:%M:%S}'.format(record.get('time'))}[/#808080] {levename} | {{message}}\n{{exception}}"
    return f"[#808080]{'{:%H:%M:%S}'.format(record.get('time'))}[/#808080] {levename} | {{message}}"


def init_logger(log_callback: Callable[[str], None], debug=False, filter_str: Optional[str] = None) -> None:
    log_filter = LogFilter(filter_str or "INFO" if not debug else "DEBUG")
    loguru.logger.add(
        log_callback,
        format=format_record,
        filter=log_filter,
        backtrace=True,
        diagnose=debug,
    )
