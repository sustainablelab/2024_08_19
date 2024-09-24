# About

Tile puzzle game. Experimenting with coding design inspired by Brian:

* decouple "game art" from renderer
* work in three coordinates systems:
  * world space
  * normalized space
  * pixel space

# Conventions

## Naming conventions

* classes and objects are camel case
  * class: first letter is capitalized
    * examples: `OsWindow()`, `UI()`
  * object: first letter is not capitalized
    * examples: `osWindow()`, `uI()`
* functions are snake case
  * capitalization has no special meaning
  * example: `game_loop()` -- typical function name
  * example: `KEYDOWN()` -- capitalized to match pygame constant `KEYDOWN`
    (searching for 'KEYDOWN' finds function 'KEYDOWN()' that handles the
    'KEYDOWN' event)

## File conventions

* applications are at the top level in `./`
* my lib code:
  * my lib code goes in `libs/`
  * my lib modules have accompanying test code in file `test_blah.py`
  * example: `libs/frect.py` has test code `libs/test_frect.py`

## Unit testing

* Use `unittest`

# Design

## Setup design

* `Game().__init__()`: create `game.osWindow`
  * `OsWindow().__init__()`: create the OS Window and sets its size.
* `Game().__init__()`: create `game.uI`
  * `UI().handle_events()`: handle `pygame` events (`QUIT`, `KEYDOWN`, etc.)
  * call `uI.handle_events()` in `game.game_loop()`
* `Game().__init__()`: create `game.cpuRenderer`
  * call `cpuRenderer.render()` in `game.game_loop()`
* `Tile().__init__()`: define the tile width (tiles are square)
* `Game().__init__()`: define `game.tile_width` to return `Tile().tile_width`
* `Game().__init__()`: define `game.player_width` as a multiple of `game.tile_width`
* `Game().__init__()`: define `game.scale` as number of pixels per unit of world space
* `Game().__init__()`: create `game.xfm` to transform between coordinate spaces
  * `CpuRenderer().render_blah`: use `game.xfm.world_to_render()` to transform world space vertices to pixel space
  * `TextHud().__init__()`: use `game.xfm.render_to_world()` to transform mouse from pixel space to world space
* `Game().__init__()`: define empty `game.drawings` dict
* `Game().__init__()`: create drawable objects: `game.player`, `game.tileMap`
  * `game.player`:
    * `Player().pos`: (x,y) center of player
    * `Player().size`: (w,h) size of player (player is always square)
    * `Player().hitbox`: FRect with (x,y) center and (w,h) size
    * `Player().debug_tiles`: list of tiles to draw as overlay on player
    * `Player().vertices`: convert `Player().hitbox` FRect to a list of vertices
    * `Player().draw()`: create entries in `game.drawings['player']`, expected by `CpuRenderer().render()`
    * `Player().move()`: define up/down/left/right movement in discrete steps of half a tile
    * `Player().scale()`: define grow/shrink scaling
  * `game.tileMap`:
    * `TileMap().__init()`: call `TileMap().load()` to load JSON file into dict `game.tileMap.tile_dict`
      * `game.tileMap.tile_dict`: `{"(x, y)": {"pos": [ x, y ], "color": [ r, g, b, a ]}`
    * `TileMap().load()`: load tile map from JSON file
    * `TileMap().save()`: save tile map to JSON file
    * `TileMap().tiles_artwork`: convert `game.tileMap.tile_dict` dict into a list of Tiles:
      

## Loop design

* `Game().game_loop()`: render using Renderer's `render()` method
  * *For now I am using a CPU renderer.*
  * `CpuRenderer().render()`:
    * Erase OS Window with background color
    * Look up how to render each "drawing" in `game.drawings`
      * Each "drawable class" (`Player()`, `TileMap()`) defines a `draw()` method
        * `Name().draw()` updates dict `game.drawings` with dict entry `drawings['name']`
          * `drawings['name']` is a dict of whatever information is needed to draw `name`
          * *all position information is in world space*
      * `CpuRenderer().render()`: defines a `render_name()` method for each "drawable class"
        * *`render_name()` expects dict `drawings['name']` to have certain entries*
          * example: `render_player()` expects `drawings['player']` has `vertices` and `color`:
            * `drawings['player']['vertices']` (in world space)
            * `drawings['player']['color']`
        * `render_name()`: use `game.xfm.world_to_render()` to transform vertices to pixel space

