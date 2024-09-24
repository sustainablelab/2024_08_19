#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Test how pygame.Rect works

pygame.Rect is not the Rect you want for world space rectangles. It is meant
specifically for pixel space:

- All values are 'int' (e.g., 1//2 = 0)
- +y is down (top < bottom)

To work with world space rects, make your own FRect class.
"""
import pygame
from pygame import Rect
import logging

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

def log_rect_attrs(rect:Rect) -> None:
    logger.info(rect)
    logger.info(f"rect.bottom: {rect.bottom}")
    logger.info(f"rect.bottomleft: {rect.bottomleft}")
    logger.info(f"rect.bottomright: {rect.bottomright}")
    logger.info(f"rect.center: {rect.center}")
    logger.info(f"rect.centerx: {rect.centerx}")
    logger.info(f"rect.centery: {rect.centery}")
    logger.info(f"rect.h: {rect.h}")
    logger.info(f"rect.height: {rect.height}")
    logger.info(f"rect.left: {rect.left}")
    logger.info(f"rect.topleft: {rect.topleft}")



def main() -> None:
    # Make a Rect to test ways I can move it around.

    # This example does not work because Rect.size is (1,1).
    # <rect(0, 0, 1, 1)> # left, top, width, height
    print()
    rect = Rect((0,0), (1,1))
    log_rect_attrs(rect)

    # Expect:
    #   <rect(-0.5, -0.5, 1, 1)> # left, top, width, height
    #   (Because 1/2 is 0.5)
    # Actual:
    #   <rect(0, 0, 1, 1)> # left, top, width, height
    #   (Because 1//2 is 0)
    print()
    rect.center = rect.topleft
    log_rect_attrs(rect)

    # These examples all work as expected because Rect.size is compatible with
    # 'int' division.
    if 0:
        # Make a Rect to test ways I can move it around.
        # <rect(0, 0, 2, 4)> # left, top, width, height
        print()
        rect = Rect((0,0), (2,4))
        log_rect_attrs(rect)

        # <rect(-1, -2, 2, 4)> # left, top, width, height
        print()
        rect = Rect((0,0), (2,4))
        rect.center = (0,0)
        log_rect_attrs(rect)

        # <rect(-1, -2, 2, 4)> # left, top, width, height
        print()
        rect = Rect((0,0), (2,4))
        log_rect_attrs(rect.move(
            rect.left-rect.centerx,
            rect.top-rect.centery))

        # <rect(-1, -2, 2, 4)> # left, top, width, height
        print()
        rect = Rect((0,0), (2,4))
        rect.center = rect.topleft
        log_rect_attrs(rect)

if __name__ == '__main__':
    logger = setup_logging("INFO")
    main()
