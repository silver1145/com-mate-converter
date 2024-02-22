import construct as cs

from com_mate_converter.utils.construct_classes import Struct

COMStr = cs.PascalString(cs.VarInt, "utf-8")


class FloatVector2(Struct):
    x: float
    y: float

    SUBCON = cs.Struct(
        "x" / cs.Float32l,
        "y" / cs.Float32l,
    )


class FloatVector3(Struct):
    x: float
    y: float
    z: float

    SUBCON = cs.Struct(
        "x" / cs.Float32l,
        "y" / cs.Float32l,
        "z" / cs.Float32l,
    )


class FloatVector4(Struct):
    x: float
    y: float
    z: float
    w: float

    SUBCON = cs.Struct(
        "x" / cs.Float32l,
        "y" / cs.Float32l,
        "z" / cs.Float32l,
        "w" / cs.Float32l,
    )
