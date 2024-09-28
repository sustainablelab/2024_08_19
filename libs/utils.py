#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Utilities
"""

import pygame
from pygame import Rect, Surface
from dataclasses import dataclass
import logging
# logger = logging.getLogger(__name__) # Uncomment this if I use the logger

def setup_logging(loglevel:str="DEBUG") -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
            "%(levelname)s in '%(funcName)s()' (%(filename)s:%(lineno)d) -- %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setLevel(loglevel)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger

class OsWindow:
    def __init__(self, window_size:tuple) -> None:
        flags = pygame.RESIZABLE
        self.surf = pygame.display.set_mode(window_size, flags=flags)

# TODO: find a way to make color names and values defined in one place
@dataclass
class Color:
    white      = pygame.Color((255,)*3)
    grey       = pygame.Color((40,)*3)
    med_grey   = pygame.Color((80,)*3)
    light_grey = pygame.Color((120,)*3)
    red        = pygame.Color(255,0,0)

    def transparent(self, color:pygame.Color, a:int=100) -> pygame.Color:
        return pygame.Color(color.r, color.g, color.b, a)

    def name(self, color:pygame.Color) -> str:
        color_tuple = (color.r, color.g, color.b)
        match color_tuple:
            case (255,255,255): color_name = 'white'
            case (40,40,40): color_name = 'grey'
            case (80,80,80): color_name = 'med_grey'
            case (120,120,120): color_name = 'light_grey'
            case (255,0,0): color_name = 'red'
            case _: color_name = 'unknown'
        return color_name

class Text:
    def __init__(self) -> None:
        self.msg = ""
        self.pos = (0, 0)
        self.font = pygame.font.SysFont("RobotoMono", 15)

    def render(self, surf:Surface) -> Rect:
        w=0
        lines = self.msg.split("\n")
        for i,line in enumerate(lines):
            ### render(text, antialias, color, background=None) -> Surface
            text_surf = self.font.render(line, True, Color.white)
            w = max(w, text_surf.get_width())
            ### blit(source, dest, area=None, special_flags=0) -> Rect
            surf.blit(text_surf, (self.pos[0], self.pos[1] + i*self.line_height))
        h = self.line_height*len(lines)
        return Rect(self.pos, (w,h))

    @property
    def line_height(self) -> int:
        return self.font.get_linesize()

class Xfm:
    """Transform points between coordinate spaces.

    Rendering: world_to_render() transforms world (x,y) to game art surface (x,y)

    There are two coordinate systems:
    1. World: 0,0 is center; scale is game units
    2. Render: 0,0 is topleft of game art surface; scale is pixels

    Math without homogeneous coordinates (2x2 xfm matrix)
    ------------------------------------
    w = vector in world space -- world units, origin: center
    r = vector in render space -- pixels, origin: topleft surf
    t = translation vector from origin of world space to origin of render space
    k = scale (pixels per world unit)
    C = Matrix to scale coordinates from World to Render
    Cinv = Inverse of C (scale coordinates from Render to World)

    Convert from world space to render space: scale, then add pixel offset

      C       w       t                             r
    | k  0 || x | + | e | = x|k| + y| 0| + |e| = | kx + e|
    | 0 -k || y |   | f |    |0|    |-k|   |f|   |-ky + f|

    To convert from render space to world space:

    Cw + t = r      # Start with above expression
    Cw = r - t      # Take steps to isolate w
    w = Cinv(r - t) # Final step to isolate w: multiply both sides by Cinv

    Inverting a 2x2 diagonal matrix is easy. Just replace each diagonal
    element with its multiplicative inverse (replace k with 1/k).
    Notate "1/k" as "k_".

    First express the vector difference "r - t" as a single vector
      r   -   t   = ( r-t )
    | x | - | e | = | x-e |
    | y |   | f |   | y-f |

    Convert from render space to world space: subtract pixel offset, then scale

      Cinv  (  r-t  ) =                               w
    | k_ 0 |(| x-e |) = (x-e)|k_| + (y-f)| 0 | = | k_(x-e) |
    | 0 -k_|(| y-f |)        |0 |        |-k_|   |-k_(y-f) |

    Math with homogeneous coordinates (3x3 xfm matrix)
    ---------------------------------
    v_w = vector in world space -- world units, origin: center
    v_r = vector in render space -- pixels, origin: topleft surf
    k = scale (pixels per world unit)
    e,f = x,y offset vector t_r -- pixels, origin: topleft surf
    C_wr = Matrix to xfm coordinates from World to Render

      C_wr      v_w                            v_r
    | k  0  e || x | = x|k| + y| 0| + 1|e| = | kx + e|
    | 0 -k  f || y |    |0|    |-k|    |f|   |-ky + f|
    | 0  0  1 || 1 |    |0|    | 0|    |1|   |    1  |

    TODO: using homogeneous coordinates, I can just do this:

    (C_wr)(v_w) = v_r
    v_w = inv(C_wr)(v_r)

    TODO: Write a matrix arithmetic library and switch to homogeneous coordinates.
    """
    def __init__(self, game) -> None:
        self.game = game
    def world_to_render(self, p:tuple, surf:Surface=None) -> tuple:
        x,y = p # Point in World coordinates
        k = self.game.scale # Scale from world coords to pixel coords
        if surf:
            w,h = surf.get_size()
        else:
            w,h = self.game.osWindow.surf.get_size()
        e,f = (w/2, h/2) # Translation vector t_r in pixel coords
        return (int(k*x + e), int(-k*y + f))
    def render_to_world(self, p:tuple, surf:Surface=None) -> tuple:
        x,y = p # Point in Render coordinates
        k_ = 1/self.game.scale
        if surf:
            w,h = surf.get_size()
        else:
            w,h = self.game.osWindow.surf.get_size()
        w,h = self.game.osWindow.surf.get_size()
        e,f = (w/2, h/2) # Translation vector t_r in pixel coords
        return (k_*(x-e), -k_*(y-f))



if __name__ == '__main__':
    import doctest
    from pathlib import Path
    doctest.testmod()
    print(f"Run doctests in {Path(__file__).name}")
