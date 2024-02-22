import dataclasses
from typing import List

import construct as cs

from com_mate_converter.utils.construct_classes import Struct, subcon

from .base import COMStr


class Command(Struct):
    arg_num: int
    args: List[str] = dataclasses.field(default_factory=list)

    SUBCON = cs.Struct("arg_num" / cs.Int8ul, "args" / cs.Array(cs.this.arg_num, COMStr))

    @staticmethod
    def create(args: List[str]):
        return Command(
            arg_num=len(args),
            args=args,
        )


class Menu(Struct):
    magic: bytes
    version: int
    src_name: str
    item_name: str
    category: str
    info_text: str
    body_size: int
    commands: List[Command] = subcon(Command, default_factory=list)

    SUBCON = cs.Struct(
        "magic" / cs.Const(b"\x0ACM3D2_MENU"),
        "version" / cs.Int32sl,
        "src_name" / COMStr,
        "item_name" / COMStr,
        "category" / COMStr,
        "info_text" / COMStr,
        "body_size" / cs.Int32sl,
        "commands"
        / cs.RepeatUntil(
            cs.obj_.arg_num == 0,
            Command.SUBCON,
        ),
    )
    SUBCON_COMPILED = cs.Struct(
        "magic" / cs.Const(b"\x0ACM3D2_MENU"),
        "version" / cs.Int32sl,
        "src_name" / COMStr,
        "item_name" / COMStr,
        "category" / COMStr,
        "info_text" / COMStr,
        "body_size" / cs.Int32sl,
        "commands"
        / cs.RepeatUntil(
            cs.obj_.arg_num == 0,
            Command.SUBCON,
        ),
    ).compile()
    SUBCON_HEADER_COMPILED = cs.Struct(
        "magic" / cs.Const(b"\x0ACM3D2_MENU"),
        "version" / cs.Int32sl,
        "src_name" / COMStr,
        "item_name" / COMStr,
        "category" / COMStr,
        "info_text" / COMStr,
        "body_size" / cs.Int32sl,
    ).compile()
    SUBCON_COMMANDS_COMPILED = cs.Struct(
        "commands"
        / cs.RepeatUntil(
            cs.obj_.arg_num == 0,
            Command.SUBCON,
        )
    ).compile()

    def build(self) -> bytes:
        data_dict = dataclasses.asdict(self)
        body_data = self.SUBCON_COMMANDS_COMPILED.build(data_dict)  # type: ignore
        data_dict["body_size"] = self.body_size = len(body_data)
        return self.SUBCON_HEADER_COMPILED.build(data_dict) + body_data

    @staticmethod
    def create(item_name: str, category: str, infoText: str, src_name: str = "") -> "Menu":
        return Menu(
            magic=b"\x0ACM3D2_MENU",
            version=2001,
            src_name=src_name,
            item_name=item_name,
            category=category,
            info_text=infoText,
            body_size=0,
            commands=[Command(arg_num=0, args=[])],
        )

    def check_end(self) -> int:
        length = index = len(self.commands)
        for c in reversed(self.commands):
            index -= 1
            if c.arg_num == 0:
                return index
        else:
            self.commands.append(Command(arg_num=0, args=[]))
            return length

    def add_command(self, command_args: List[str]):
        if len(command_args) > 0:
            self.commands.insert(self.check_end(), Command.create(command_args))
