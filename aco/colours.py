from dataclasses import dataclass


@dataclass
class Colour:
    background_grey: tuple[int, int, int] = (18, 18, 18)  # Background Initial.
    middle_grey: tuple[int, int, int] = (28, 42, 38)
    l_grey: tuple[int, int, int] = (48, 66, 64)  # Background
    dark_grey: tuple[int, int, int] = (70, 78, 72)  # Background
    dense_canopy: tuple[int, int, int] = (50 + 2, 58, 60)  # Tree
    light_canopy: tuple[int, int, int] = (44, 38, 28)  # Tree
    tree_border: tuple[int, int, int] = (44, 38, 28)  # Tree

    """General Colours"""
    grey: tuple[int, int, int] = (46, 42, 33)
    light_grey: tuple[int, int, int] = (46 + 3, 42 + 3, 33 + 3)
    black: tuple[int, int, int] = (18, 30, 28)
    white: tuple[int, int, int] = (255, 255, 255)
    yellow: tuple[int, int, int] = (253, 218, 13)
    brown: tuple[int, int, int] = (111, 78, 55)
