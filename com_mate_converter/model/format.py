import dataclasses


@dataclasses.dataclass
class FormatVariable:
    mate_name: str
    shader_family: str
    shader_name: str
