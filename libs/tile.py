#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Tile class and TileMap serdes.

Tiles define their position, color, hitbox, vertices, and artwork. All Tiles
are squares with side length 'Tile().TILE_WIDTH'. 

* [ ] Add a Tile() property to define how Tile().art should manipulate the
      Tile vertices. Then do a look-up in Tile().art to create the artwork
      vertices.
"""

import json
import pygame
if __name__ == '__main__':
    from frect import FRect
    from utils import Color
else:
    from libs.frect import FRect
    from libs.utils import Color
import logging
logger = logging.getLogger(__name__)

class Tile:
    def __init__(self, pos=(0,0), color=Color.light_grey) -> None:
        self.pos = pos
        self.color = color
        self.TILE_WIDTH = 1                             # KEEP THIS AT 1
        # stop, pass, push
        self.behavior = 'push'

    def __repr__(self) -> str:
        hitbox = self.hitbox
        return (f"Tile(pos={self.pos}, color=Color.{self.color_name}): "
               f"behavior=\"{self.behavior}\", name=\"{self.name}\"")

    @property
    def name(self) -> str:
        return str(tuple(self.pos))

    @property
    def color_name(self) -> str:
        return Color().name(self.color)

    @property
    def size(self) -> tuple:
        return (self.TILE_WIDTH, self.TILE_WIDTH)

    def move(self, direction:str, movement_amount:float) -> None:
        m = movement_amount
        old_pos = self.pos
        match direction:
            case "up":
                self.pos = (self.pos[0], self.pos[1]+m)
            case "down":
                self.pos = (self.pos[0], self.pos[1]-m)
            case "left":
                self.pos = (self.pos[0]-m, self.pos[1])
            case "right":
                self.pos = (self.pos[0]+m, self.pos[1])

    @property
    def hitbox(self) -> FRect:
        _hitbox = FRect(self.pos, self.size)
        return _hitbox

    @property
    def art(self) -> list:
        """Access tile vertices."""
        return self.vertices() # TODO: create tile art based on the vertices

    # Private
    def vertices(self) -> list:
        """Return the four vertices of the hitbox. See Tile().art"""
        rect = self.hitbox
        return [
                rect.topleft,
                rect.topright,
                rect.bottomright,
                rect.bottomleft,
                ]

class TileMap:
    def __init__(self, game) -> None:
        self.game = game
        self.tile_dict = {}

    @property
    def tile_list(self) -> list:
        """Return list of tiles from 'TileMap().tile_dict'. Each tile is an instance of Tile.

        It is often useful to have a list of Tiles to iterate over: rendering,
        testing for collisions, etc. This is why I made the
        'TileMap().tile_list' property.

        For each tile:
            tile.pos is the tile center.
            tile.color is the tile color.
            tile.behavior is the tile behavior.
            tile.art is the four vertices of the tile.

        Why not just use the dict directly? TileMap().tile_dict is NOT a
        dictionary of Tiles. It is a dictionary of tile values ('(x, y)':
        {'pos': (x, y), 'color': (r, g, b, a)}.

        I was avoiding putting Tiles directly in the 'TileMap().tile_dict' to
        avoid writing custom serialization when saving levels to file. This
        was a bad decision.

        TODO: store Tiles as Tiles in the TileMap().tile_dict. Get rid of the
        conversion that happens in this function.

        Example
        -------
        for k in self.tile_dict:
            logger.info(f"{k}: {self.tile_dict[k]}")
        (1, 5): {'pos': (1, 5), 'color': (40, 40, 40, 255)}
        (2, 5): {'pos': (2, 5), 'color': (40, 40, 40, 255)}
        (3, 5): {'pos': (3, 5), 'color': (40, 40, 40, 255)}
        (5, 5): {'pos': (5, 5), 'color': (40, 40, 40, 255)}
        for t in _tile_list:
            logger.info(f"{t}")
        Tile(pos=(1, -1), center=(1, -1))
        Tile(pos=(2, -1), center=(2, -1))
        Tile(pos=(3, -1), center=(3, -1))
        Tile(pos=(5, -1), center=(5, -1))
        """
        _tile_list = []
        for k in self.tile_dict:
            v = self.tile_dict[k]
            tile = Tile(v['pos'], v['color'])
            _tile_list.append(tile)
        return _tile_list

    def draw(self) -> None:
        """Update Game.drawings['tileMap']."""
        self.game.drawings['tileMap'] = {}              # Create drawing "tileMap"
        self.game.drawings['tileMap']['tile_list'] = self.tile_list

    def update_tile(self, old_tile_name:str, new_tile:tuple) -> None:
        """Update old tile in TileMap with new tile."""
        # First: remove old tile from TileMap dict. Keep its values in 'tile_values' for re-inserting.
        tile_values = self.tile_dict.pop(old_tile_name)

        # Update the position in 'tile_values'
        tile_values['pos'] = new_tile.pos

        ## TODO: handle the case that there is already a tile at the new position (make this an assert: it should never happen!)
        ## Until I fix this, the pushed tile overwrites (erases) any existing tiles.

        # Insert tile back into 'TileMap().tile_dict'
        self.tile_dict[new_tile.name] = tile_values

class TileMapEncoder(json.JSONEncoder):
    """Tell json.dump() how to encode tiles.

    pygame.Color is not JSON serializable.

    Dataclass 'Color' is a collection of named pygame.Color constants. A tile
    has a "color"; the type() of this color is 'pygame.Color'.
    """
    def default(self, obj):
        if isinstance(obj, pygame.Color):
            return tuple(obj)
        else:
            logger.error(f"Add 'elif' statement to serialize \"{type(obj)}\": {obj}")
            sys.exit()

def decode_tile_map_json(tile_dict:dict) -> dict:
    """Convert basic types from JSON file back into custom objects.

    Conversions
    -----------
    JSON 'color':
        'color': [255,255,255,255]
    Convert to pygame.Color:
        pygame.Color(255,255,255,255)
    """
    for name in tile_dict:
        # Replace every 'color' tuple with type pygame.Color
        color = pygame.Color(tile_dict[name]['color'])
        tile_dict[name]['color'] = color
    return tile_dict

if __name__ == '__main__':
    from pathlib import Path
    print(f"Run {Path(__file__).name} doctests")
    import doctest
    doctest.testmod()
