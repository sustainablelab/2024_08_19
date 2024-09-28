#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Start from scratch, again.

* [x] Set up a resizable window with CPU rendering, HUD.
* [x] Set up logging:
  * DEBUG: log unused events and keystrokes
  * INFO: Use this for inspecting code
* The way I do drawing now, each object uses Xfm to do coordinate transforms
  that convert vertices from world space to screen space. I am going to try
  something different inspired by talking to Brian.
* [x] Objects "draw" by writing draw data to self.game.drawings
* [x] CpuRenderer uses Xfm to convert vertices from world space to screen space
* [ ] Xfm knows how to convert drawn objects to renderable objects
* [ ] GpuRenderer uses Xfm to convert the large global of drawings into renderable objects and then renders them.
* The new flow for drawing:
    * game_loop() calls update_drawings()
        * this calls the draw() method on every game world object (player, tiles, etc.)
        * the draw() method writes to dict Game.drawings()
    * renderer iterates over Game.drawings():
        * dict keys are the drawing 'name'; use 'name' to look up how to render
        * if 'name' matches, append 'name' to list 'done_drawings', else 'todo_drawings'
* [x] wasd moves the player in World space coordinates
    * This required changing 'hitbox' from attribute Player.hitbox to
    '@property' Player.hitbox so that an access of 'hitbox' forces a
    recalculation of hitbox from Player.pos.
* [x] DO NOT USE pygame.Rect for world space tiles!
    * Rect(left, top, width, height) only allows integer values
    * Say a Rect has x,y = 0,0 and w,h = 1,1
    * Then the topleft is 0,0 AND the center is 0,0 because the Rect does not
    use floats.
    * pygame.Rect is only meant for use in pixel space.
* [x] Create libs/frect.py FRect for making rects in world space
* [x] Move player in 0.5 increments
    * Player size variability forces player on/off the (1,1) grid because I
      want player position to remain centered
    * So I decided to allow movement in 0.5 increments to get player back on
      grid. I think the half-tile movements feel better too.
* [x] Up/Down to change player size
    * This is temporary to test the size change math.
    * Size change will be a game mechanic.
* [x] Create a level editor.
* [ ] Add interaction with tiles:
    * Right now the only interaction is that tiles act as immovable walls.
    * Add a "behavior" property to Tiles
    * [ ] Create "behavior" "win":
          When the player reaches the "win" tile, they advance to the next level.
    * [ ] Create "behavior" "push":
          When the player pushes a pushable tile, it moves if the player is
          big enough to move it.
* [ ] Create levels.
    * Introduce basic size change puzzles.
    * Then come up with levels that act as tiles so that the size change
      mechanic has a meta form at the level of moving from one level to
      another. I don't know exactly what this means yet. I just have a sense
      that I want an entire level to act as a tile in some sense so that a
      combination of levels acts as a meta tile map puzzle.
* [x] Save TileMap to file
    * [ ] Get tuple values on a single line using the regex encoder trick here:
    https://stackoverflow.com/questions/42710879/write-two-dimensional-list-to-json-file
* [x] Load TileMap from file
* [x] Collision detection
    * Detect if player hitbox overlaps tile hitbox
    * Works for any size player
"""

import atexit
import sys
import json
import pygame
from pathlib import Path
from pygame import Rect, Surface
from libs.frect import FRect
from libs.utils import setup_logging
from libs.utils import OsWindow, Color, Text, Xfm
from libs.tile import Tile, TileMap, TileMapEncoder, decode_tile_map_json

def shutdown(filename:str) -> None:
    logger.info(f"Shutdown {filename}")
    pygame.font.quit()
    pygame.quit()


class UI:
    def __init__(self, game) -> None:
        self.game = game
    def handle_events(self) -> None:
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT: sys.exit()
                case pygame.KEYDOWN: self.KEYDOWN(event)
                case _: logger.debug(event)
    def KEYDOWN(self, event) -> None:
        kmod = pygame.key.get_mods()
        match event.key:
            case pygame.K_q: sys.exit()
            case pygame.K_F2: self.game.debug = not self.game.debug
            # W,A,S,D and Ctrl+S save
            case pygame.K_w: self.game.player.move("up")
            case pygame.K_s:
                if (kmod & pygame.KMOD_CTRL):
                    self.game.tileMap.save() # TEMPORARY: save TileMap
                else:
                    self.game.player.move("down")
            case pygame.K_a: self.game.player.move("left")
            case pygame.K_d: self.game.player.move("right")
            # Up, Down
            case pygame.K_UP: self.game.player.scale("grow")
            case pygame.K_DOWN: self.game.player.scale("shrink")
            # Ctrl+L load
            case pygame.K_l:
                if (kmod & pygame.KMOD_CTRL):
                    self.game.tileMap.load() # TEMPORARY: load TileMap
                else:
                    pass
            case _: logger.debug(event)

class CpuRenderer:
    def __init__(self, game) -> None:
        self.game = game
    def render(self) -> None:
        surf = self.game.osWindow.surf
        def render_player() -> None:
            """Draw player as a polygon. If debug, draw player's debug tiles as polygons."""
            assert drawing['vertices']                  # game.drawings['player']['vertices']
            assert drawing['color']                     # game.drawings['player']['color']
            ### blit(source, dest, area=None, special_flags=0) -> Rect
            render_vertices = [self.game.xfm.world_to_render(p) for p in drawing['vertices']]
            pygame.draw.polygon(surf, drawing['color'], render_vertices)
            if drawing['debug']:
                assert drawing['debug']['tiles_overlay']        # game.drawings['player']['debug']['tiles_overlay']
                assert drawing['debug']['color']        # game.drawings['player']['debug']['color']
                for tile in drawing['debug']['tiles_overlay']:
                    render_vertices = [self.game.xfm.world_to_render(p) for p in tile]
                    pygame.draw.polygon(surf, drawing['debug']['color'],
                                        render_vertices, width=2)
        def render_tileMap() -> None:
            """Draw tiles as polygons."""
            for tile in drawing['tile_list']:
                render_vertices = [self.game.xfm.world_to_render(p) for p in tile.art]
                # Draw fill
                pygame.draw.polygon(surf, tile.color, render_vertices)
                # Draw border
                border_color = Color.light_grey if tile.color==Color.white else Color.white
                pygame.draw.polygon(surf, border_color, render_vertices, width=2 if self.game.debug else 1)
        self.game.osWindow.surf.fill(Color.grey)
        # Catch programmer error
        done_drawings = []                              # DEBUG
        todo_drawings = []                              # DEBUG
        # Look up how to render each drawing
        for name in self.game.drawings:
            drawing = self.game.drawings[name]
            match name:
                case "player":
                    render_player()
                    done_drawings.append(name)   # DEBUG
                case "tileMap":
                    render_tileMap()
                    done_drawings.append(name)   # DEBUG
                case _:
                    todo_drawings.append(name)   # DEBUG
        # DEBUG
        # List drawings I haven't drawn in the HUD
        if self.game.textHud:
            self.game.textHud.msg += f"\n{'-'*50}"
            self.game.textHud.msg += f"\nDrew: {','.join(done_drawings)}"
            if todo_drawings == []:
                self.game.textHud.msg += "\nDrew all drawings."
            else:
                self.game.textHud.msg += f"\nForgot to draw: {','.join(todo_drawings)}"
            self.game.textHud.render(self.game.osWindow.surf)
        pygame.display.update()

class TextHud(Text):
    def __init__(self, game) -> None:
        self.game = game
        super().__init__()
        ### pygame.time.Clock.get_fps() -> float
        self.msg += f"FPS: {self.game.clock.get_fps():0.1f}"
        ### get_pos() -> (x, y)
        mpos = pygame.mouse.get_pos()
        self.msg += f"\nMouse: Render=({mpos[0]:4d},{mpos[1]:4d})"
        mpos_w = self.game.xfm.render_to_world(mpos)
        self.msg += f", World=({mpos_w[0]:+0.2f}, {mpos_w[1]:+0.2f})({mpos_w[0]:+0.0f},{mpos_w[1]:+0.0f})"

class Player:
    def __init__(self, game) -> None:
        self.game = game
        self.pos = (-1,0) # Player starts in center of screen

    @property
    def size(self) -> tuple:
        w = self.game.player_width
        return (w,w)

    @property
    def hitbox(self) -> FRect:
        _hitbox = FRect(center=self.pos, size=self.size)
        return _hitbox

    @property
    def debug_tiles(self) -> list:
        """Return list of tiles. Each tile is the four vertices of the debug tile.

        Overlay the player with debug tiles.

        Return list of tiles, each tile is a list of four vertices.

        Explanation
        -----------
        For self.size=(2,2), there are four tiles:

        tiles = [
                FRect((x+0-0.5,y+0-0.5), (1,1)), # bottomleft
                FRect((x+1-0.5,y+0-0.5), (1,1)), # bottomright
                FRect((x+0-0.5,y+1-0.5), (1,1)), # topleft
                FRect((x+1-0.5,y+1-0.5), (1,1)), # topright
                ]

        Each tile FRect is converted to a list of four vertices.

        Position the tiles based on player size (w,h):

        w or h | sx or sy
        ------ | --------
          1    |   0.0
          2    |   0.5
          3    |   1.0
          4    |   1.5

        sx = s*(w-1)
        sy = s*(h-1)
        """
        # NOTE: Tile size is not hardcoded.
        # NOTE: This debug-tile generation works for any player size.
        # TODO: Make this work with tile sizes other than (1,1)
        # Overlay a grid of debug tiles, centered on the player.
        x,y = self.hitbox.center
        t = self.game.tile_width; # width of one tile
        s = t/2; # half-width of one tile
        w,h = self.size # Width and height of player
        tiles = [] # List of debug tiles
        for j in range(h):
            for i in range(w):
                sx = s*(w-1); sy = s*(h-1)
                tiles.append(FRect((x+i-sx,y+j-sy), (t,t)))
        # Convert each tile FRect to a list of vertices
        tile_art = []
        for tile in tiles:
            tile_art.append([
                tile.topleft,
                tile.topright,
                tile.bottomright,
                tile.bottomleft,
                ])
        return tile_art

    @property
    def vertices(self) -> list:
        """Return the four vertices of the hitbox"""
        return [list(self.hitbox.topleft),
                list(self.hitbox.topright),
                list(self.hitbox.bottomright),
                list(self.hitbox.bottomleft)]

    def draw(self) -> None:
        """Draw by declaring what is in the drawing. Update Game.drawings['player']."""
        # Draw player artwork (vertices that define a filled polygon)
        self.game.drawings['player'] = {}               # Create drawing "player"
        self.game.drawings['player']['vertices'] = self.vertices
        self.game.drawings['player']['color'] = Color.red
        # Draw debug artwork (tiles) for player
        self.game.drawings['player']['debug'] = None    # Render "if drawing['debug']"
        if self.game.debug:
            self.game.drawings['player']['debug'] = {}  # Create drawing "player.debug"
            self.game.drawings['player']['debug']['color'] = Color.white
            self.game.drawings['player']['debug']['tiles_overlay'] = self.debug_tiles

    def _is_collision(self, tile:Tile) -> bool:
        return ((self.hitbox.right > tile.hitbox.left) and
                (self.hitbox.left < tile.hitbox.right) and
                (self.hitbox.top > tile.hitbox.bottom) and
                (self.hitbox.bottom < tile.hitbox.top))

    def list_colliding_tiles(self) -> list:
        """Return list of colliding tiles."""
        return [tile for tile in self.game.tileMap.tile_list if self._is_collision(tile)]

    def is_colliding(self) -> bool:
        logger.info(str(self.pos))
        collision = False
        # Get Tile List
        tiles = self.game.tileMap.tile_list
        for tile in tiles:
            if self._is_collision(tile):
                collision = True; break
        return collision

    def move(self, direction:str) -> None:
        m = self.game.movement_amount                   # Move by half-tiles
        old_pos = self.pos # Restore old position if there is a collision
        match direction:
            case "up":
                self.pos = (self.pos[0], self.pos[1]+m)
            case "down":
                self.pos = (self.pos[0], self.pos[1]-m)
            case "left":
                self.pos = (self.pos[0]-m, self.pos[1])
            case "right":
                self.pos = (self.pos[0]+m, self.pos[1])

        # TODO: match player response to tile behavior
        for tile in self.list_colliding_tiles():
            logger.info(tile)
            match tile.behavior:
                case 'stop': self.pos = old_pos
                case 'pass': pass
                case 'push':
                    old_name = tile.name # Use name to update the 'TileMap().tile_dict'
                    tile.move(direction, m) # Move this tile (doesn't update dict yet)
                    self.game.tileMap.update_tile(old_name, tile) # Update 'TileMap().tile_dict'
                case _:
                    pass




    def scale(self, direction:str) -> None:
        match direction:
            case "grow":
                logger.debug("grow")
                # Player can get arbitrarily large
                self.game.player_width = self.game.player_width + 1
            case "shrink":
                logger.debug("shrink")
                # Player cannot be smaller than (1,1) in World space
                self.game.player_width = max(self.game.player_width - 1, 1)

class TileMapGame(TileMap):
    """Dict of tiles. Each tile is a Tile().

    The tilemap is stored as a dictionary:

        TileMap().tile_dict

    Access the tilemap as a list using the property:

        TileMap().tile_list
    """
    def __init__(self, game) -> None:
        super().__init__(game)
        if 1: # Change to 0 to debug serialization
            self.load() # Create self.tile_dict. TODO: loading happens elsewhere
        else:
            self.load_to_debug_serialization()

    # DEBUGGING
    def load_to_debug_serialization(self) -> None:
        self.tile_dict = {}
        positions = [(1,-1), (2,-1), (3,-1), (5,-1)]
        for pos in positions:
            name = str(pos)
            self.tile_dict[name] = {}
            self.tile_dict[name]['pos'] = pos
            self.tile_dict[name]['color'] = Color.light_grey

    def load(self) -> None:
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

        Example of same TileMap but generated in Python code
        ----------------------------------------------------
            positions = [(1,-1), (2,-1), (3,-1), (5,-1)]
            for pos in positions:
                name = str(pos)
                tiles[name] = {}
                tiles[name]['pos'] = pos
                tiles[name]['color'] = Color.light_grey
        """
        file = "level1.json"
        with open(file) as f:
            # Use custom deserializer to turn color tuples back into Color objects.
            self.tile_dict = decode_tile_map_json(json.load(f))
        logger.info(f"Loaded TileMap from \"{file}\"")

    def save(self) -> None:
        """Save current TileMap to file."""
        file = "level.json"
        with open(file, "w") as f:
            json.dump(self.tile_dict, f, cls=TileMapEncoder, indent=4)
        logger.info(f"Saved TileMap to \"{file}\"")

class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.font.init()
        self.debug = True
        # Game engine
        self.osWindow = OsWindow(window_size=(500,180))
        self.uI = UI(self)
        self.clock = pygame.time.Clock()
        self.cpuRenderer = CpuRenderer(self)
        self.player_width = 2*self.tile_width # Player width in World space. Pick any player_width
        self.scale = 30 # Num pixels equal to 1 unit of world space
        self.xfm = Xfm(self)
        self.drawings = {}
        # Drawable game objects
        self.player = Player(self)
        self.tileMap = TileMapGame(self)

    @property
    def tile_width(self) -> int:
        """Tile width in World space."""
        return Tile().TILE_WIDTH

    @property
    def movement_amount(self) -> float:
        """Amount that player moves on each movement."""
        return self.tile_width/2

    def run(self) -> None:
        while True: self.game_loop()

    def game_loop(self) -> None:
        self.textHud = TextHud(self) if self.debug else None
        self.uI.handle_events()
        self.update_drawings()                          # Update global drawing dict
        self.cpuRenderer.render()                       # Render drawing dict on CPU
        ### tick(framerate=0) -> milliseconds
        self.clock.tick(60)

    def update_drawings(self) -> None:
        """Update self.game.drawings: artwork for all game world objects."""
        self.player.draw()
        self.tileMap.draw()

if __name__ == '__main__':
    logger = setup_logging("INFO")
    logger.info(f"Run {Path(__file__).name}")
    atexit.register(shutdown, f"{Path(__file__).name}")
    Game().run()
