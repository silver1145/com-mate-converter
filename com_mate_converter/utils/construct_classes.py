import dataclasses
import typing

import construct as cs
from typing_extensions import Self

# https://github.com/matejcik/construct-classes

if typing.TYPE_CHECKING:
    from typing_extensions import dataclass_transform
else:

    def dataclass_transform(**kwargs: typing.Any) -> typing.Any:
        def inner(cls: typing.Any) -> typing.Any:
            return cls

        return inner


def subcon(
    cls: typing.Type["Struct"],
    *,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = None,
    **kwargs: typing.Any,
) -> typing.Any:
    if metadata is None:
        metadata = {}
    metadata["substruct"] = cls
    return dataclasses.field(metadata=metadata, **kwargs)


def subcon_switch(
    distinct_field: str,
    classes: typing.Dict[str, typing.Type["Struct"]],
    *,
    metadata: typing.Optional[typing.Dict[str, typing.Any]] = None,
    **kwargs: typing.Any,
) -> typing.Any:
    if metadata is None:
        metadata = {}
    metadata["substruct_dist_field"] = distinct_field
    metadata["substruct"] = classes
    return dataclasses.field(metadata=metadata, **kwargs)


@dataclass_transform(
    field_specifiers=(
        subcon,
        subcon_switch,
    )
)
class _StructMeta(type):
    def __new__(cls, name: str, bases: typing.Tuple[type, ...], namespace: typing.Dict[str, typing.Any]) -> type:
        new_cls = super().__new__(cls, name, bases, namespace)
        return dataclasses.dataclass()(new_cls)


class Struct(metaclass=_StructMeta):
    SUBCON: typing.ClassVar["cs.Construct[cs.Container[typing.Any], typing.Dict[str, typing.Any]]"]
    SUBCON_COMPILED: typing.ClassVar[
        typing.Optional["cs.Construct[cs.Container[typing.Any], typing.Dict[str, typing.Any]]"]
    ] = None

    def build(self) -> bytes:
        if self.SUBCON_COMPILED is not None:
            return self.SUBCON_COMPILED.build(dataclasses.asdict(self))
        return self.SUBCON.build(dataclasses.asdict(self))

    @staticmethod
    def _decontainerize(item: typing.Any) -> typing.Any:
        if isinstance(item, cs.ListContainer):
            return [Struct._decontainerize(i) for i in item]
        return item

    @classmethod
    def from_parsed(cls: typing.Type[Self], data: cs.Container) -> Self:
        args = {}
        for field in dataclasses.fields(cls):
            field_data = data.get(field.name)
            subcls = field.metadata.get("substruct")
            if isinstance(subcls, dict):
                subcls = subcls.get(data.get(field.metadata.get("substruct_dist_field")))  # type: ignore
            if subcls is None:
                args[field.name] = field_data
                continue

            if isinstance(field_data, cs.ListContainer):
                args[field.name] = [subcls.from_parsed(d) for d in field_data]
            elif isinstance(field_data, cs.Container):
                args[field.name] = subcls.from_parsed(field_data)
            elif field_data is None:
                continue
            else:
                raise ValueError(f"Mismatched type for field {field.name}: expected a struct, found {type(field_data)}")

        for key in args:
            args[key] = cls._decontainerize(args[key])
        return cls(**args)

    @classmethod
    def parse(cls: typing.Type[Self], data: bytes) -> Self:
        if cls.SUBCON_COMPILED is not None:
            result = cls.SUBCON_COMPILED.parse(data)
        else:
            result = cls.SUBCON.parse(data)
        return cls.from_parsed(result)
