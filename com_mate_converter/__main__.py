import sys

from loguru import logger

from com_mate_converter.app import MainApp
from com_mate_converter.log import init_logger


def main():
    debug = False
    if sys.argv:
        for i in sys.argv[1:]:
            if i.upper() in ["-DEBUG", "--DEBUG"]:
                debug = True
                break
    logger.remove()
    app = MainApp()
    init_logger(app.send_log_message, debug)
    app.run()


if __name__ == "__main__":
    main()
