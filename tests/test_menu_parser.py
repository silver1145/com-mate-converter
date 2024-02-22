from construct import ConstructError
import pytest
from tests import resouce_path
from com_mate_converter.model import Menu


@pytest.mark.finished
def test_read():
    with open(resouce_path / "menu_example.menu", "rb") as f:
        Menu.parse(f.read())


@pytest.mark.finished
def test_write():
    menu = generate_menu()
    menu.build()


@pytest.mark.finished
def test_readwrite():
    with open(resouce_path / "menu_example.menu", "rb") as f:
        data = f.read()
    menu = Menu.parse(data)
    assert menu.build() == data
    menu = generate_menu()
    data = menu.build()
    assert Menu.parse(data) == menu


@pytest.mark.finished
def test_readerror():
    with open(resouce_path / "menu_example_error.menu", "rb") as f:
        data = f.read()
    try:
        Menu.parse(data)
    except:
        pass
    else:
        raise Exception("Menu Error not Caught")


@pytest.mark.finished
def test_truncate():
    with open(resouce_path / "menu_example_untruncated.menu", "rb") as f:
        data_untruncated = f.read()
    with open(resouce_path / "menu_example.menu", "rb") as f:
        data = f.read()
    assert Menu.parse(data_untruncated).build() == data


def generate_menu() -> Menu:
    menu = Menu.create(item_name="example", category="wear", infoText="_" * 128)
    menu.add_command(["icons", "example.tex"])
    menu.add_command(["onclickmenu"])
    menu.add_command(["additem", "example.model", "wear"])
    return menu
