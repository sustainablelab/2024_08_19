#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Level editor for game.py

Rules
-----
1. The same position cannot have more than one tile. Placing a tile over an
existing tile, therefore, replaces the existing tile with the new tile.

User Instructions
-----------------
* Number keys (1,2,3,4,...) to select the tile style
* Move tile cursor with mouse
    * left-click to place a tile
    * right-click to erase a tile
* Alternatively, move tile cursor with w,a,s,d
    * space to place a tile
    * if a tile is in the spot, space erases the tile
    * putting the above two steps together, press space twice to replace a
      tile with a new tile

Dev
---
[x] Open a window
[x] Create class CpuRenderer to use pygame draw calls
[x] Create a debug HUD
[x] Add mouse interactions
[x] Add TileMap
[x] Add alpha transparency for ghost tile cursor
    * Game().__init__(): os.environ["PYGAME_BLEND_ALPHA_SDL2"] = "1"
    * Create drawing surface for cursor:
        * Cursor().blah()
        * CpuRenderer.render() calls 
[x] Display tile styles at top of screen
[x] Display style number of tile under tiles at top of screen
[x] Use mouse to draw TileMap
    * [x] Left-click places a tile
    * [x] Right-click erases a tile
    * [x] Show ghost of selected tile type where cursor is currently located
    * [x] Number keys change tile type
[x] Use keyboard to draw TileMap
    [x] * w,a,s,d moves a tile cursor around
    [x] * <Space> toggles place/erase
        * erase tile if a tile exists
        * place tile if empty
[x] Save to file
[ ] Load from file
    * For now I am saving in Editor and loading in Game.
"""

import atexit
import sys
import os
import json
import pygame
from pygame import Surface
from pathlib import Path
from libs.utils import setup_logging
from libs.utils import OsWindow, Color, Text, Xfm
from libs.tile import Tile, TileMap, TileMapEncoder
from libs.frect import FRect


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
        self.msg += f", World=({mpos_w[0]:+0.2f}, {mpos_w[1]:+0.2f})"

class UI:
    def __init__(self, game) -> None:
        self.game = game
    def handle_events(self) -> None:
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT: sys.exit()
                case pygame.KEYDOWN: self.KEYDOWN(event)
                case pygame.MOUSEBUTTONDOWN: self.MOUSEBUTTONDOWN(event)
                case pygame.MOUSEMOTION: self.MOUSEMOTION(event)
                case _: logger.debug(event)
    def KEYDOWN(self, event) -> None:
        kmod = pygame.key.get_mods()
        match event.key:
            case pygame.K_q: sys.exit()
            case pygame.K_F2: self.game.debug = not self.game.debug
            case pygame.K_1: self.game.cursor.style = 1
            case pygame.K_2: self.game.cursor.style = 2
            case pygame.K_3: self.game.cursor.style = 3
            case pygame.K_4: self.game.cursor.style = 4
            # W,A,S,D to move cursor (as alternative to using mouse)
            case pygame.K_w: self.game.cursor.use_mpos = False; self.game.cursor.move('up')
            case pygame.K_s:
                if kmod & pygame.KMOD_CTRL:
                    self.game.tileMap.save()
                else:
                    self.game.cursor.use_mpos = False; self.game.cursor.move('down')
            case pygame.K_a: self.game.cursor.use_mpos = False; self.game.cursor.move('left')
            case pygame.K_d: self.game.cursor.use_mpos = False; self.game.cursor.move('right')
            # Space to place tiles (or replace tiles or erase tiles)
            case pygame.K_SPACE: self.game.cursor.space()
    def MOUSEMOTION(self, event) -> None:
        self.game.cursor.use_mpos = True
    def MOUSEBUTTONDOWN(self, event) -> None:
        xfm = self.game.xfm # Xfm mouse pixel coordinate to world space
        match event.button:
            case 1: # left click (one finger)
                logger.info(f"Left-click: {event.pos}")
                self.game.editor.place_tile(xfm.render_to_world(event.pos))
            case 2: # right click (three fingers)
                logger.info(f"Right-click: {event.pos}")
                self.game.editor.erase_tile(xfm.render_to_world(event.pos))
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
            for tile in drawing['tile_list']:
                render_vertices = [self.game.xfm.world_to_render(p) for p in tile.art]
                # Draw fill
                pygame.draw.polygon(surf, tile.color, render_vertices)
                # Draw border
                border_color = Color.light_grey if tile.color==Color.white else Color.white
                pygame.draw.polygon(surf, border_color, render_vertices,
                                    width=3 if self.game.debug else 1)
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
        self.game.cursor.render(surf)
        self.game.cursor.render_styles(surf)
        if self.game.textHud:
            self.game.textHud.msg += f"\n{'-'*50}"
            if todo_drawings == []:
                self.game.textHud.msg += "\nDrew all drawings."
            else:
                self.game.textHud.msg += f"\nForgot to draw: {','.join(todo_drawings)}"
            self.game.textHud.render(surf)
        pygame.display.update()

class Cursor:
    """Cursor.render() blits ghost of selected tile type at mouse position."""
    def __init__(self, game) -> None:
        self.game = game
        self.use_mpos = True # True if mouse moves; False if W,A,S,D pressed
        self.pos = (0,0) # Cursor position in World space
        self.style = 1
        self.style_dict = {}
        self.style_dict[1] = {'color':Color.white}
        self.style_dict[2] = {'color':Color.grey}
        self.style_dict[3] = {'color':Color.light_grey}
        self.style_dict[4] = {'color':Color.red}

    @property
    def color(self) -> Color:
        return self.style_dict[self.style]['color']

    def space(self) -> None:
        if self.game.editor.has_tile(self.pos):
            self.game.editor.erase_tile(self.pos)
        else:
            # Place a tile at self.pos
            self.game.editor.place_tile(self.pos)

    def move(self, direction:str) -> None:
        m = Tile().TILE_WIDTH # Move in increments of the tile width
        match direction:
            case "up":    self.pos = (self.pos[0],   self.pos[1]+m)
            case "down":  self.pos = (self.pos[0],   self.pos[1]-m)
            case "left":  self.pos = (self.pos[0]-m, self.pos[1])
            case "right": self.pos = (self.pos[0]+m, self.pos[1])

    def render(self, surf) -> None:
        """Blit a cursor surface onto the OS Window surface."""
        scale = self.game.scale # To convert world units to pixels
        # TODO: use selected tile type instead of hardcoded red tile
        tile = Tile((0,0), Color().transparent(self.color))
        size_pixels = (tile.size[0]*scale,
                       tile.size[1]*scale)
        xfm = self.game.xfm # To xfm mouse pixel coordinate to world space
        editor = self.game.editor # To snap to grid
        # Snap mouse to tile grid coordinates
        if self.use_mpos:
            # Use mouse position to update World space cursor position
            mpos = pygame.mouse.get_pos() # Get mouse position in pixels
            self.pos = editor.snap_pos_to_grid(xfm.render_to_world(mpos)) # Xfm and snap
        mpos = xfm.world_to_render(self.pos) # Xfm back to pixels
        # DEBUG
        if self.game.textHud: self.game.textHud.msg += f"\nCursor: {self.pos}"
        # Center tile on mouse
        tile_frect = FRect(mpos, size_pixels) # Make an FRect (+y is up) in pixel space
        tile_rect = pygame.Rect(tile_frect.bottomleft, size_pixels) # +y is down
        # Create a surface to draw the tile
        ### Surface((width, height), flags=0, depth=0, masks=None) -> Surface
        cursor_surf = pygame.Surface((size_pixels[0]+1, size_pixels[1]+1), flags=pygame.SRCALPHA)
        # Draw the tile on this surface
        render_vertices = [xfm.world_to_render(p, cursor_surf) for p in tile.art]
        # Draw fill
        pygame.draw.polygon(cursor_surf, tile.color, render_vertices)
        # Draw border
        pygame.draw.polygon(cursor_surf, Color.white, render_vertices, width=1)
        ### blit(source, dest, area=None, special_flags=0) -> Rect
        surf.blit(cursor_surf, tile_rect.topleft, special_flags=pygame.BLEND_ALPHA_SDL2)# Use alpha blending

    def render_styles(self, surf) -> None:
        """Blit tyle style surfaces onto the OS Window surface."""
        xfm = self.game.xfm
        scale = self.game.scale
        for n in self.style_dict:
            # Get color, pixel-space vertices, and pixel space Rect for surf position
            name = str(n)
            style = self.style_dict[n]
            color = style['color']
            tile = Tile((0,0), color)
            size_pixels = (tile.size[0]*scale, tile.size[1]*scale)
            pos_w = (-1+2*n,2) # World coordinates
            pos_p = xfm.world_to_render(pos_w) # Render coordinates
            tile_frect = FRect(pos_p, size_pixels)
            tile_rect = pygame.Rect(tile_frect.bottomleft, size_pixels)
            tile_surf = pygame.Surface((size_pixels[0]+1, size_pixels[1]+1))
            render_vertices = [xfm.world_to_render(p, tile_surf) for p in tile.art]
            pygame.draw.polygon(tile_surf, tile.color, render_vertices)
            border_color = Color.light_grey if tile.color==Color.white else Color.white
            pygame.draw.polygon(tile_surf, border_color, render_vertices,
                                width=5 if self.style==n else 1)
            # Draw to OS Window
            surf.blit(tile_surf, tile_rect.topleft)
            # Add Text under the style
            text = Text()
            text.msg = name
            # Find the width of the text
            _surf = text.font.render(text.msg, True, Color.white)
            w = _surf.get_width()
            # Use text width to center the position
            text.pos = (tile_rect.midbottom[0] - w/2, tile_rect.midbottom[1])
            text.render(surf)

class Editor:
    def __init__(self, game) -> None:
        self.game = game

    def snap_pos_to_grid(self, pos_world:tuple) -> tuple:
        return (round(pos_world[0]), round(pos_world[1]))

    def place_tile(self, pos_world:tuple) -> None:
        pos = self.snap_pos_to_grid(pos_world)
        self.game.tileMap.tile_dict[str(pos)] = {'pos': pos, 'color': self.game.cursor.color}

    def has_tile(self, pos_world:tuple) -> bool:
        pos = self.snap_pos_to_grid(pos_world)
        tile_name = str(pos)
        tile_dict = self.game.tileMap.tile_dict
        return tile_name in tile_dict

    def erase_tile(self, pos_world:tuple) -> None:
        pos = self.snap_pos_to_grid(pos_world)
        tile_name = str(pos)
        tile_dict = self.game.tileMap.tile_dict
        if self.has_tile(pos_world):
            del tile_dict[tile_name]

class TileMapEditor(TileMap):
    def __init__(self, game) -> None:
        super().__init__(game)

    def save(self) -> None:
        """Save current TileMap to file."""
        file = "level1.json"
        with open(file, "w") as f:
            json.dump(self.tile_dict, f, cls=TileMapEncoder, indent=4)
        logger.info(f"Saved TileMap to \"{file}\"")

class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.font.init()
        os.environ["PYGAME_BLEND_ALPHA_SDL2"] = "1"     # Use SDL2 alpha blending
        self.debug = True
        # Game engine
        self.osWindow = OsWindow(window_size=(500,180))
        self.uI = UI(self)
        self.cpuRenderer = CpuRenderer(self)
        self.editor = Editor(self)
        self.scale = 30 # Num pixels equal to 1 unit of world space
        self.clock = pygame.time.Clock()
        self.xfm = Xfm(self)
        self.cursor = Cursor(self)
        self.drawings = {}
        # Drawable game objects
        self.tileMap = TileMapEditor(self)

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
