# About

Setting up graphics using approach inspired by conversation with Brian.

# Vim Omnicomplete

I am baffled by Python omincomplete. Last night I could not get it to
omnicomplete on locally defined classes at all. Then this morning, it just
works:

In `game.py` I have this `import` statement:

```
from libs.frect import FRect
```

Then I type `FRe` and hit `Ctrl-x Ctrl-o`. The text completes to `FRect`
and I get this in the Preview window:

```
Rect with floating point values.

    center -- (x,y)
    size -- (w,h)
```

Not only is the omnicomplete working all of a sudden, but even the Preview
window is formatting my docstring nicely!
