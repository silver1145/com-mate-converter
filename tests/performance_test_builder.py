from pathlib import Path
from copy import deepcopy
import random
from com_mate_converter.model import Menu, Mate
from tests import resouce_path


with open(resouce_path / "template_NPRMAT_NPRToonV2_Emissiv_Trans_.mate", "rb") as f:
    template_mate_data = f.read()
    template_mate = Mate.parse(template_mate_data)

with open(resouce_path / "template.menu", "rb") as f:
    template_menu = Menu.parse(f.read())


def build_performance_test_file(path: Path, num: int, group: int = 10, mate_per_menu: int = 4) -> None:
    path.mkdir(parents=True, exist_ok=True)
    group_size = num // group + 1
    cur_group_index = 1
    mate_group_path = path / f"mate_{cur_group_index}"
    menu_group_path = path / f"menu_{cur_group_index}"
    mate_group_path.mkdir(exist_ok=True)
    menu_group_path.mkdir(exist_ok=True)
    for i in range(1, num + 1):
        print(f"{i / num * 100:.2f}%", end="\r")
        group_index = i // group_size + 1
        if cur_group_index != group_index:
            cur_group_index = group_index
            mate_group_path = path / f"mate_{cur_group_index}"
            menu_group_path = path / f"menu_{cur_group_index}"
            mate_group_path.mkdir(exist_ok=True)
            menu_group_path.mkdir(exist_ok=True)
        mate_path = mate_group_path / f"Test_{i}_NPRMAT_NPRToonV2_Emissiv_Trans_.mate"
        with mate_path.open("wb") as f:
            f.write(template_mate_data)
        menu = deepcopy(template_menu)
        for j in range(mate_per_menu):
            menu.add_command(
                ["マテリアル変更", "wear", "0", f"Test_{random.randint(1, num)}_NPRMAT_NPRToonV2_Emissiv_Trans_.mate"]
            )
        menu_path = menu_group_path / f"Test_{i}.menu"
        with menu_path.open("wb") as f:
            f.write(menu.build())


if __name__ == "__main__":
    build_performance_test_file(path=Path(__file__).parent / "performance/", num=200000, group=100)
