from construct import ConstructError
import pytest
from tests import resouce_path
from com_mate_converter.model import Mate


@pytest.mark.finished()
def test_read():
    with open(resouce_path / "example_1.mate", "rb") as f:
        Mate.parse(f.read())
    with open(resouce_path / "example_2.mate", "rb") as f:
        Mate.parse(f.read())
    with open(resouce_path / "example_3.mate", "rb") as f:
        Mate.parse(f.read())


@pytest.mark.finished()
def test_write():
    mate = generate_mate()
    mate.build()


@pytest.mark.finished()
def test_readwrite():
    with open(resouce_path / "example_1.mate", "rb") as f:
        data = f.read()
    mate = Mate.parse(data)
    assert mate.build() == data
    mate = generate_mate()
    data = mate.build()
    assert Mate.parse(data) == mate


@pytest.mark.finished()
def test_readerror():
    with open(resouce_path / "example_1_corrupted.mate", "rb") as f:
        data = f.read()
    try:
        Mate.parse(data)
    except (ConstructError, ValueError):
        pass
    else:
        raise Exception("Mate Corrupt Error not Caught")
    with open(resouce_path / "example_1_error_prop.mate", "rb") as f:
        data = f.read()
    try:
        Mate.parse(data)
    except (ConstructError, ValueError):
        pass
    else:
        raise Exception("Mate Property Error not Caught")


@pytest.mark.finished()
def test_truncate():
    with open(resouce_path / "example_1_untruncated.mate", "rb") as f:
        data_untruncated = f.read()
    with open(resouce_path / "example_1.mate", "rb") as f:
        data = f.read()
    assert Mate.parse(data_untruncated).build() == data


def generate_mate() -> Mate:
    mate = Mate.create(
        mate_name="test",
        shader="test/Test",
        shader_filename="test_Test",
        material_name="test",
    )
    mate.add_tex2d(name="_MainTex", file="test_1", filepath="test_1.png")
    mate.add_cube(name="_CubeTex", file="test_2", filepath="test_2.png")
    mate.add_texrt(name="_RTTex", value_1="discard", value_2="discard")
    mate.add_texnull("_MatCapTex")
    mate.add_color(name="_Color", color=(0.5, 0.5, 0.5, 1))
    mate.add_vector(name="_Vector", vector=(0, 0, 0, 0))
    mate.add_float(name="_MatCap", value=0)
    return mate
