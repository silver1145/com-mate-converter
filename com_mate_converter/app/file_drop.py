import os
import shlex
from pathlib import Path
from typing import List

import regex

winpath_pattern = regex.compile(r'(?:[^\s"]|"(?:\\"|[^"])*")+')
winpath_split_pattern = regex.compile(r" +(?=[A-Za-z]:)")


def getpaths(text: str) -> List[str]:
    split_filepaths = []
    if os.name == "nt":
        if " " in text and not text.startswith('"'):
            split_filepaths = winpath_split_pattern.split(text)
        else:
            split_filepaths = winpath_pattern.findall(text)
    else:
        split_filepaths = shlex.split(text)
    ret = []
    for i in split_filepaths:
        i = i.replace("\x00", "").replace('"', "")
        p = Path(i)
        if p.exists() and p.is_dir():
            ret.append(i)
    return ret
