#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Tile class.
"""

if __name__ == '__main__':
    from frect import FRect
    from utils import Color
else:
    from libs.frect import FRect
    from libs.utils import Color

class Tile:
    def __init__(self, pos=(0,0), color=Color.light_grey) -> None:
        self.pos = pos
        self.color = color
        self.TILE_WIDTH = 1                             # KEEP THIS AT 1

    def __repr__(self) -> str:
        hitbox = self.hitbox
        return f"Tile(pos={self.pos}, center={hitbox.center}, hitbox={hitbox}"

    @property
    def size(self) -> tuple:
        return (self.TILE_WIDTH, self.TILE_WIDTH)

    @property
    def hitbox(self) -> FRect:
        _hitbox = FRect(self.pos, self.size)
        return _hitbox

    @property
    def vertices(self) -> list:
        """Return the four vertices of the hitbox"""
        rect = self.hitbox
        return [
                rect.topleft,
                rect.topright,
                rect.bottomright,
                rect.bottomleft,
                ]

    @property
    def art(self) -> list:
        return self.vertices # TODO: create tile art based on the vertices

if __name__ == '__main__':
    from pathlib import Path
    print(f"Run {Path(__file__).name} doctests")
    import doctest
    doctest.testmod()
