from typing import Optional

import construct as cs

from com_mate_converter.utils.construct_classes import Struct

from .base import COMStr


class Pmat(Struct):
    magic: bytes
    version: int
    hash: int
    material_name: str
    renderqueue: float
    shader: Optional[str]

    SUBCON = cs.Struct(
        "magic" / cs.Const(b"\x0FCM3D2_PMATERIAL"),
        "version" / cs.Int32sl,
        "hash" / cs.Int32sl,
        "material_name" / COMStr,
        "renderqueue" / cs.Float32l,
        "shader" / cs.Optional(COMStr),
    )

    def build(self) -> bytes:
        self.hash = Pmat.str_hash(self.material_name)
        return super().build()

    @staticmethod
    def str_hash(s: str) -> int:
        h = 0
        for c in s:
            h = (31 * h + ord(c)) & 0xFFFFFFFF
        return ((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000
