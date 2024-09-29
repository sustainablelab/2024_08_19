#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Tile class and TileMap serdes.

Tiles define their position, color, hitbox, vertices, and artwork. All Tiles
are squares with side length 'Tile().TILE_WIDTH'. 

* [ ] Add a Tile() property to define how Tile().art should manipulate the
      Tile vertices. Then do a look-up in Tile().art to create the artwork
      vertices.
"""

import sys
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
    """Define a tile in the TileMap. See also TileMap."""
    def __init__(self, pos=(0,0), color=Color.light_grey, behavior='stop') -> None:
        self.pos = pos
        self.color = color
        self.behavior = behavior
        # stop, pass, push

    def __repr__(self) -> str:
        hitbox = self.hitbox
        return (f"Tile(pos={self.pos}, color=Color.{self.color_name}, behavior=\"{self.behavior}\")")

    @property
    def TILE_WIDTH(self) -> int: return 1 # KEEP THIS AT 1 (@property excludes this from JSON).

    @property
    def name(self) -> str:
        return str(tuple(self.pos))

    @property
    def color_name(self) -> str:
        return Color().name(self.color)

    @property
    def size(self) -> tuple:
        return (self.TILE_WIDTH, self.TILE_WIDTH)

    # def move(self, direction:str) -> None:
    #     self.game.

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
    """Store Tiles in a dict: {"(x, y)": Tile(), }. See also Tile."""
    def __init__(self, game) -> None:
        self.game = game
        self.tile_dict = {}

    def save(self, file:str) -> None:
        """Save current TileMap to file."""
        with open(file, "w") as f:
            json.dump(self.tile_dict, f, cls=TileMapEncoder, indent=4)
        logger.info(f"Saved TileMap to \"{file}\"")

    def load(self, file:str) -> None:
        """Load TileMap (dict of tiles) from file.

        Example JSON TileMap with four tiles
        ------------------------------------
        {
            "(1, -1)": {
                "pos": [ 1, -1 ],
                "color": [ 80, 80, 80, 255 ]
            },
            "(2, -1)": {
                "pos": [ 2, -1 ],
                "color": [ 80, 80, 80, 255 ]
            },
            "(3, -1)": {
                "pos": [ 3, -1 ],
                "color": [ 80, 80, 80, 255 ]
            },
            "(5, -1)": {
                "pos": [ 5, -1 ],
                "color": [ 80, 80, 80, 255 ]
            }
        }
        """
        with open(file) as f:
            # Use custom deserializer to turn Tile.__dict__ vars back into Tile objects.
            self.tile_dict = decode_tile_map_json(json.load(f))
        logger.info(f"Loaded TileMap from \"{file}\"")

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
        if 0:
            _tile_list = []
            for k in self.tile_dict:
                v = self.tile_dict[k]
                tile = Tile(v['pos'], v['color'])
                _tile_list.append(tile)
            return _tile_list
        else:
            return list(self.tile_dict.values())

    def draw(self) -> None:
        """Update Game.drawings['tileMap']."""
        self.game.drawings['tileMap'] = {}              # Create drawing "tileMap"
        self.game.drawings['tileMap']['tile_list'] = self.tile_list

    def push_tile(self, old_tile_name:str, direction:str) -> bool:
        """Update tile map when a tile is pushed. Return True if the tile moves."""
        tile = self.tile_dict[old_tile_name] # Reference to tile in dict (changing tile also changes the tile_dict)
        old_pos = tile.pos
        del self.tile_dict[old_tile_name] # Remove tile from dict to avoid colliding with its old position
        # tile.move(direction, self.game.movement_amount) # Move the tile
        self.game.physics.move(tile, direction) # Move the tile
        self.tile_dict[tile.name] = tile # Use new position as new dict key
        return old_pos != tile.pos # Return True if position changed.

class TileMapEncoder(json.JSONEncoder):
    """Tell json.dump() how to encode tiles.

    pygame.Color is not JSON serializable.

    Dataclass 'Color' is a collection of named pygame.Color constants. A tile
    has a "color"; the type() of this color is 'pygame.Color'.
    """
    def default(self, obj):
        if isinstance(obj, Tile):
            return vars(obj)
        elif isinstance(obj, pygame.Color):
            return tuple(obj)
        else:
            logger.error(f"Add 'elif' statement to serialize \"{type(obj)}\": {obj}")
            sys.exit()

def decode_tile_map_json(tile_map_json:dict) -> dict:
    tile_dict = {} # Return this
    for name in tile_map_json:
        # Get pos, color, and behavior from JSON
        pos = tile_map_json[name]['pos']
        # Replace every 'color' tuple with type pygame.Color
        color = pygame.Color(tile_map_json[name]['color'])
        behavior = tile_map_json[name]['behavior']
        tile_dict[name] = Tile(pos, color, behavior)
    return tile_dict

# def decode_tile_map_json(tile_dict:dict) -> dict:
def old_decode_tile_map_json(tile_dict:dict) -> dict:
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

class Physics:
    """Physics for tile interactions: player-tile and tile-tile."""
    def __init__(self, game) -> None:
        self.game = game

    def _is_colliding(self, entity, tile:Tile) -> bool:
        """Return True if entity is colliding with tile."""
        return ((entity.hitbox.right > tile.hitbox.left) and
                (entity.hitbox.left < tile.hitbox.right) and
                (entity.hitbox.top > tile.hitbox.bottom) and
                (entity.hitbox.bottom < tile.hitbox.top))

    def list_colliding_tiles(self, entity) -> list:
        """Return list of tiles colliding with entity."""
        return [tile for tile in self.game.tileMap.tile_list if self._is_colliding(entity, tile)]

    def move(self, entity, direction:str) -> None:
        m = self.game.movement_amount # Move by half-tiles
        old_pos = entity.pos          # Restore old position if there is a collision
        match direction:
            case "up":
                entity.pos = (entity.pos[0], entity.pos[1]+m)
            case "down":
                entity.pos = (entity.pos[0], entity.pos[1]-m)
            case "left":
                entity.pos = (entity.pos[0]-m, entity.pos[1])
            case "right":
                entity.pos = (entity.pos[0]+m, entity.pos[1])

        for tile in self.list_colliding_tiles(entity):
            logger.debug(tile)
            match tile.behavior:
                case 'stop': entity.pos = old_pos
                case 'pass': pass
                case 'push': 
                    if self.game.tileMap.push_tile(tile.name, direction): pass
                    else: entity.pos = old_pos
                case _:
                    pass

if __name__ == '__main__':
    from pathlib import Path
    print(f"Run {Path(__file__).name} doctests")
    import doctest
    doctest.testmod()
