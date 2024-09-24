#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Level editor for game.py

[x] Open a window
[x] Create class CpuRenderer to use pygame draw calls
[x] Create a debug HUD
[x] Add mouse interactions
[x] Add TileMap
[ ] Use mouse to draw TileMap
    * Placeholder: I draw a tile in TileMap().__init__()
[ ] Save to file
[ ] Load from file
"""

import atexit
import sys
import pygame
from pathlib import Path
from libs.utils import setup_logging
from libs.utils import OsWindow, Color, Text, Xfm
from libs.tile import Tile


def shutdown(filename:str) -> None:
    logger.info(f"Shutdown {filename}")
    pygame.font.quit()
    pygame.quit()

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

class UI:
    def __init__(self, game) -> None:
        self.game = game
    def handle_events(self) -> None:
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT: sys.exit()
                case pygame.KEYDOWN: self.KEYDOWN(event)
                case pygame.MOUSEBUTTONDOWN: self.MOUSEBUTTONDOWN(event)
                case _: logger.debug(event)
    def KEYDOWN(self, event) -> None:
        match event.key:
            case pygame.K_q: sys.exit()
            case pygame.K_F2: self.game.debug = not self.game.debug
    def MOUSEBUTTONDOWN(self, event) -> None:
        match event.button:
            case 1: # left click (one finger)
                logger.info(f"Left-click: {event.pos}")
            case 2: # right click (three fingers)
                logger.info(f"Right-click: {event.pos}")
            case 3: # middle click (two fingers)
                logger.info(f"Middle-click: {event.pos}")
            case _:
                logger.info(event)

class CpuRenderer:
    def __init__(self, game) -> None:
        self.game = game
    def render(self) -> None:
        surf = self.game.osWindow.surf
        def render_tileMap() -> None:
            for tile in drawing['tiles_list']:
                render_vertices = [self.game.xfm.world_to_render(p) for p in tile.art]
                # Draw fill
                pygame.draw.polygon(surf, tile.color, render_vertices)
                # Draw border
                pygame.draw.polygon(surf, Color.white, render_vertices,
                                    width=2 if self.game.debug else 1)
        surf.fill(Color.grey)
        # Catch programmer error
        todo_drawings = []                              # DEBUG
        for name in self.game.drawings:
            drawing = self.game.drawings[name]
            match name:
                case "tileMap":
                    render_tileMap()
                case _:
                    todo_drawings.append(name)
        if self.game.textHud:
            self.game.textHud.msg += f"\n{'-'*50}"
            if todo_drawings == []:
                self.game.textHud.msg += "\nDrew all drawings."
            else:
                self.game.textHud.msg += f"\nForgot to draw: {','.join(todo_drawings)}"
            self.game.textHud.render(surf)
        pygame.display.update()

class TileMap:
    def __init__(self, game) -> None:
        self.game = game
        self.tile_dict = {}
        self.tile_dict['(1, -1)'] = {'pos': (1,-1), 'color': (80, 80, 80, 255)}

    @property
    def tiles_list(self) -> list:
        """Return list of tiles. Each tile is an instance of Tile.

        For each tile:
            tile.pos is the tile center.
            tile.color is the tile color.
            tile.art is the four vertices of the tile.
        """
        _tiles_list = []
        for k in self.tile_dict:
            v = self.tile_dict[k]
            tile = Tile(v['pos'], v['color'])
            _tiles_list.append(tile)
        return _tiles_list

    def draw(self) -> None:
        self.game.drawings['tileMap'] = {}
        self.game.drawings['tileMap']['tiles_list'] = self.tiles_list

class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.font.init()
        self.debug = True
        # Game engine
        self.osWindow = OsWindow(window_size=(500,180))
        self.uI = UI(self)
        self.cpuRenderer = CpuRenderer(self)
        self.scale = 30 # Num pixels equal to 1 unit of world space
        self.clock = pygame.time.Clock()
        self.xfm = Xfm(self)
        self.drawings = {}
        # Drawable game objects
        self.tileMap = TileMap(self)

    def run(self) -> None:
        while True: self.game_loop()

    def game_loop(self) -> None:
        self.textHud = TextHud(self) if self.debug else None
        self.uI.handle_events()
        self.update_drawings()
        self.cpuRenderer.render()
        ### tick(framerate=0) -> milliseconds
        self.clock.tick(60)

    def update_drawings(self) -> None:
        self.tileMap.draw()

if __name__ == '__main__':
    logger = setup_logging("INFO")
    logger.info(f"Run {Path(__file__).name}")
    atexit.register(shutdown, f"{Path(__file__).name}")
    Game().run()
