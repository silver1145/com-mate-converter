from typing import Dict, List, Optional

import regex

from com_mate_converter.model.base import COMStr


def encode_com_str(text: str) -> bytes:
    return COMStr.build(text)


def decode_com_str(data: bytes) -> str:
    return COMStr.parse(data)


class BinaryReplace:
    repls: Dict[str, bytes] = {}
    replace_pattern: Optional[regex.Pattern] = None

    @staticmethod
    def compile_pattern(mate_name_dict: Dict[str, str], sort_len: bool = False) -> None:
        BinaryReplace.repls.clear()
        keys: List[bytes] = []
        for k, v in mate_name_dict.items():
            BinaryReplace.repls[k] = encode_com_str(v)
            keys.append(encode_com_str(k))
        if sort_len:
            keys.sort(key=lambda s: (len(s), s), reverse=True)
        BinaryReplace.replace_pattern = regex.compile(b"|".join(map(regex.escape, keys)), regex.IGNORECASE)

    @staticmethod
    def replace(data: bytes) -> bytes:
        if BinaryReplace.replace_pattern is not None:
            return BinaryReplace.replace_pattern.sub(BinaryReplace.repl, data)
        return data

    @staticmethod
    def repl(match: regex.Match) -> bytes:
        data: bytes = match.group()
        if (text := BinaryReplace.repls.get(decode_com_str(data).lower())) is not None:
            return text
        return data
