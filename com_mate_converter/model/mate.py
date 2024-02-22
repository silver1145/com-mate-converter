import dataclasses
from typing import Any, Dict, List, Tuple, Type

import construct as cs

from com_mate_converter.utils.construct_classes import Struct, subcon, subcon_switch

from .base import COMStr, FloatVector2, FloatVector4


class BaseProperty(Struct):
    prop_type: str

    @classmethod
    def from_parsed(cls: Type["BaseProperty"], data: cs.Container) -> "BaseProperty":
        if cls is BaseProperty:
            prop_type = data.get("prop_type")
            if prop_type == "tex":
                return TexProperty.from_parsed(data)
            elif prop_type == "col":
                return ColorProperty.from_parsed(data)
            elif prop_type == "vec":
                return VectorProperty.from_parsed(data)
            elif prop_type == "f":
                return FloatProperty.from_parsed(data)
            elif prop_type == "end":
                return EndProperty.from_parsed(data)
            else:
                raise ValueError(f"Unknown prop type: {prop_type}")
        else:
            return super(BaseProperty, cls).from_parsed(data)


class TexProperty(BaseProperty):
    class Tex(Struct):
        class BaseTexData(Struct):
            pass

        class Tex2dData(BaseTexData):
            name: str
            path: str
            offset: FloatVector2 = subcon(FloatVector2)
            scale: FloatVector2 = subcon(FloatVector2)

        class CubeData(BaseTexData):
            name: str
            path: str
            offset: FloatVector2 = subcon(FloatVector2)
            scale: FloatVector2 = subcon(FloatVector2)

        class TexRTData(BaseTexData):
            name: str
            path: str

        class NullTexData(BaseTexData):
            pass

        tex_name: str
        tex_type: str
        data: BaseTexData = subcon_switch(
            "tex_type", {"tex2d": Tex2dData, "cube": CubeData, "texRT": TexRTData, "null": NullTexData}
        )

        SUBCON = cs.Struct(
            "tex_name" / COMStr,
            "tex_type" / COMStr,
            "data"
            / cs.Switch(
                cs.this.tex_type,
                {
                    "tex2d": cs.Struct(
                        "name" / COMStr,
                        "path" / COMStr,
                        "offset" / FloatVector2.SUBCON,
                        "scale" / FloatVector2.SUBCON,
                    ),
                    "cube": cs.Struct(
                        "name" / COMStr,
                        "path" / COMStr,
                        "offset" / FloatVector2.SUBCON,
                        "scale" / FloatVector2.SUBCON,
                    ),
                    "texRT": cs.Struct("name" / COMStr, "path" / COMStr),
                    "null": cs.Struct(cs.Pass),
                },
            ),
        )

    prop: Tex = subcon(Tex)

    SUBCON = Tex.SUBCON


class ColorProperty(BaseProperty):
    class Color(Struct):
        name: str
        value: FloatVector4 = subcon(FloatVector4)

        SUBCON = cs.Struct("name" / COMStr, "value" / FloatVector4.SUBCON)

    prop: Color = subcon(Color)

    SUBCON = Color.SUBCON


class VectorProperty(BaseProperty):
    class Vector(Struct):
        name: str
        value: FloatVector4 = subcon(FloatVector4)

        SUBCON = cs.Struct("name" / COMStr, "value" / FloatVector4.SUBCON)

    prop: Vector = subcon(Vector)

    SUBCON = Vector.SUBCON


class FloatProperty(BaseProperty):
    class Float(Struct):
        name: str
        value: float

        SUBCON = cs.Struct("name" / COMStr, "value" / cs.Float32l)

    prop: Float = subcon(Float)

    SUBCON = Float.SUBCON


class EndProperty(BaseProperty):
    prop: Dict = dataclasses.field(default_factory=dict)

    SUBCON = cs.Struct(cs.Pass)

    def __init__(
        self,
        prop_type="end",
        prop: Any = None,
    ) -> None:
        super().__init__(prop_type=prop_type)
        self.prop = dict()


class Material(Struct):
    name: str
    shader: str
    shader_filename: str
    properties: List[BaseProperty] = subcon(BaseProperty, default_factory=list)

    SUBCON = cs.Struct(
        "name" / COMStr,
        "shader" / COMStr,
        "shader_filename" / COMStr,
        "properties"
        / cs.RepeatUntil(
            cs.obj_.prop_type == "end",
            cs.Struct(
                "prop_type" / COMStr,
                "prop"
                / cs.Switch(
                    cs.this.prop_type,
                    {
                        "tex": TexProperty.SUBCON,
                        "col": ColorProperty.SUBCON,
                        "vec": VectorProperty.SUBCON,
                        "f": FloatProperty.SUBCON,
                        "end": EndProperty.SUBCON,
                    },
                ),
            ),
        ),
    )


class Mate(Struct):
    magic: bytes
    version: int
    mate_name: str
    material: Material = subcon(Material)

    SUBCON = cs.Struct(
        "magic" / cs.Const(b"\x0eCM3D2_MATERIAL"),
        "version" / cs.Int32sl,
        "mate_name" / COMStr,
        "material" / Material.SUBCON,
    )
    SUBCON_COMPILED = cs.Struct(
        "magic" / cs.Const(b"\x0eCM3D2_MATERIAL"),
        "version" / cs.Int32sl,
        "mate_name" / COMStr,
        "material"
        / cs.Struct(
            "name" / COMStr,
            "shader" / COMStr,
            "shader_filename" / COMStr,
            "properties"
            / cs.RepeatUntil(
                cs.obj_.prop_type == '"end"',
                cs.Struct(
                    "prop_type" / COMStr,
                    "prop"
                    / cs.Switch(
                        cs.this.prop_type,
                        {
                            "tex": TexProperty.SUBCON,
                            "col": ColorProperty.SUBCON,
                            "vec": VectorProperty.SUBCON,
                            "f": FloatProperty.SUBCON,
                            "end": EndProperty.SUBCON,
                        },
                    ),
                ),
            ),
        ),
    ).compile()

    @staticmethod
    def create(mate_name: str, shader: str, shader_filename: str, material_name: str) -> "Mate":
        material = Material(
            name=material_name,
            shader=shader,
            shader_filename=shader_filename,
            properties=[EndProperty()],
        )
        return Mate(
            magic=b"\x0eCM3D2_MATERIAL",
            version=1000,
            mate_name=mate_name,
            material=material,
        )

    def check_end(self) -> int:
        length = index = len(self.material.properties)
        for p in reversed(self.material.properties):
            index -= 1
            if type(p) is EndProperty:
                return index
        else:
            self.material.properties.append(EndProperty())
            return length

    def add_property(self, property: BaseProperty) -> None:
        self.material.properties.insert(self.check_end(), property)

    def add_tex2d(
        self,
        name: str,
        file: str,
        filepath: str,
        offset: Tuple[float, float] = (0, 0),
        scale: Tuple[float, float] = (1, 1),
    ) -> None:
        self.add_property(
            TexProperty(
                prop_type="tex",
                prop=TexProperty.Tex(
                    tex_name=name,
                    tex_type="tex2d",
                    data=TexProperty.Tex.Tex2dData(
                        name=file,
                        path=filepath,
                        offset=FloatVector2(*offset),
                        scale=FloatVector2(*scale),
                    ),
                ),
            )
        )

    def add_cube(
        self,
        name: str,
        file: str,
        filepath: str,
        offset: Tuple[float, float] = (0, 0),
        scale: Tuple[float, float] = (1, 1),
    ) -> None:
        self.add_property(
            TexProperty(
                prop_type="tex",
                prop=TexProperty.Tex(
                    tex_name=name,
                    tex_type="cube",
                    data=TexProperty.Tex.CubeData(
                        name=file,
                        path=filepath,
                        offset=FloatVector2(*offset),
                        scale=FloatVector2(*scale),
                    ),
                ),
            )
        )

    def add_texrt(
        self,
        name: str,
        value_1: str,
        value_2: str,
    ) -> None:
        self.add_property(
            TexProperty(
                prop_type="tex",
                prop=TexProperty.Tex(
                    tex_name=name,
                    tex_type="texRT",
                    data=TexProperty.Tex.TexRTData(
                        name=value_1,
                        path=value_2,
                    ),
                ),
            )
        )

    def add_texnull(self, name: str) -> None:
        self.add_property(
            TexProperty(
                prop_type="tex",
                prop=TexProperty.Tex(
                    tex_name=name,
                    tex_type="null",
                    data=TexProperty.Tex.NullTexData(),
                ),
            )
        )

    def add_color(self, name: str, color: Tuple[float, float, float, float]) -> None:
        self.add_property(
            ColorProperty(
                prop_type="col",
                prop=ColorProperty.Color(
                    name=name,
                    value=FloatVector4(*color),
                ),
            )
        )

    def add_vector(self, name: str, vector: Tuple[float, float, float, float]) -> None:
        self.add_property(
            VectorProperty(
                prop_type="vec",
                prop=VectorProperty.Vector(
                    name=name,
                    value=FloatVector4(*vector),
                ),
            )
        )

    def add_float(self, name: str, value: float) -> None:
        self.add_property(
            FloatProperty(
                prop_type="f",
                prop=FloatProperty.Float(
                    name=name,
                    value=value,
                ),
            )
        )
