#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
"""Floating point rectangles for world space tiles.
"""

from dataclasses import dataclass

@dataclass
class FRect:
    """Rect with floating point values.

    center -- (x,y)
    size -- (w,h)

    Attributes
    ----------

        topleft
        topright
        bottomright
        bottomleft

    Like the pygame.Rect, FRect implements assignment to attributes.

    >>> rect = FRect((10.0,10.0), (1.0,1.0)) # Create an FRect centered at 10,10 with size (1,1)
    >>> rect.center
    (10.0, 10.0)
    >>> rect.center = rect.topleft # Move by assignment
    >>> rect.center
    (9.5, 10.5)
    >>> rect.topleft = rect.center # Move back by assignment the other way
    >>> rect.center
    (10.0, 10.0)
    """
    center:tuple
    size:tuple

    @property
    def left(self) -> float:
        x,y = self.center; w,h = self.size
        return x-(w/2)
    @property
    def right(self) -> float:
        x,y = self.center; w,h = self.size
        return x+(w/2)
    @property
    def top(self) -> float:
        x,y = self.center; w,h = self.size
        return y+(h/2)
    @property
    def bottom(self) -> float:
        x,y = self.center; w,h = self.size
        return y-(h/2)

    @property
    def topleft(self) -> tuple:
        """Return topleft of FRect."""
        x,y = self.center; w,h = self.size
        return (x - (w/2), y + (h/2))

    @property
    def topright(self) -> tuple:
        """Return topright of FRect."""
        x,y = self.center; w,h = self.size
        return (x + (w/2), y + (h/2))

    @property
    def bottomright(self) -> tuple:
        """Return bottomright of FRect."""
        x,y = self.center; w,h = self.size
        return (x + (w/2), y - (h/2))

    @property
    def bottomleft(self) -> tuple:
        """Return bottomleft of FRect."""
        x,y = self.center; w,h = self.size
        return (x - (w/2), y - (h/2))

    @topleft.setter
    def topleft(self, p:tuple) -> None:
        """Set FRect.center so that topleft == p."""
        x,y = p; w,h = self.size
        self.center = (x + (w/2), y - (h/2))

    @topright.setter
    def topright(self, p:tuple) -> None:
        """Set FRect.center so that topright == p."""
        x,y = p; w,h = self.size
        self.center = (x - (w/2), y - (h/2))

    @bottomright.setter
    def bottomright(self, p:tuple) -> None:
        """Set FRect.center so that bottomright == p."""
        x,y = p; w,h = self.size
        self.center = (x - (w/2), y + (h/2))

    @bottomleft.setter
    def bottomleft(self, p:tuple) -> None:
        """Set FRect.center so that bottomleft == p."""
        x,y = p; w,h = self.size
        self.center = (x + (w/2), y + (h/2))

if __name__ == '__main__':
    import doctest
    from pathlib import Path
    doctest.testmod()
    print(f"Run doctests in {Path(__file__).name}")
