# -*- coding: iso-8859-1 -*

import pygame
from manager import BlockManager, Block
from ast import literal_eval
from sprites import DirtyLayerGrid

__all__ = ['Room']

"""
A module containing context for a room/map/level.

Practices:
+ Comply to PEP 0008 for programming with modules, classes, methods and
  functions (Style Guide for Python Codestyle), see:
  https://www.python.org/dev/peps/pep-0008
+ Comply to PEP 0257 (Docstring convention), see:
  https://www.python.org/dev/peps/pep-0257

@author: Peter Borgstedt (peter.borgstedt@gmail.com)
"""


class Room():
  """Room contain the structure of map/room/level in the game. It contain
  all necessary to render and interact with it."""

  def __init__(self, prefix_section, context):
    config = context.get_config()
    self.properties = config.get_properties("room*" + prefix_section)
    self.renderer = DirtyLayerGrid(prefix_section)
    self.block_manager = BlockManager()
    self.read(context.get_sprite_manager())

  def read(self, sprite_manager):
    """Read blocks and sprites for this room. Build the data structure.
    TODO: Optimize identical sprites with different positions,
    TODO: Map sprite to positions.
    """
    self.read_blocks()
    layer_sizes = self.read_sprites(sprite_manager)
    w = h = 0
    for key in layer_sizes.keys():
      layer_size = layer_sizes[key]
      w = layer_size[0] if layer_size[0] > w else w
      h = layer_size[1] if layer_size[1] > h else h
    self.size = ((w, h))

  def read_sprites(self, sprite_manager):
    """Read and create sprites (with sprite_manager) add these to the
    renderer."""
    matrix = self.properties.get_prefixed('matrix.layer', '.')
    sprite_map = self.properties.get_eval('sprite.map', default={})
    tile_map = self.properties.get_eval('tile.map', default={})

    layer_sizes = {}
    for layer in sorted(matrix.keys()):
      layer_matrix_str = matrix[layer]
      layer_matrix = literal_eval(layer_matrix_str)
      layer_sizes[layer] = (len(layer_matrix[0]) * 32,
                            len(layer_matrix) * 32)
      x = y = 0
      for row in layer_matrix:
        for column in row:
          key = tile_map.get(column, None)
          if key:
            sprite = sprite_manager.get_tile(key, x, y)
            self.renderer.add(sprite, layer=int(layer))
          else:
            key = sprite_map.get(column, None)
            if key:
              self._set_sprite(sprite_manager, key, x, y, layer)
            elif isinstance(column, tuple):
              z, i = column
              z = tile_map.get(z, None)
              sprite = sprite_manager.get_tile((z, i), x, y)
              self.renderer.add(sprite, layer=int(layer))
          x += 32
        y += 32
        x = 0
    return layer_sizes

  def read_blocks(self):
    """Read blocks and add these to block_manager."""
    blocking_matrix = self.properties.get_eval('matrix.block', default={})
    blocking_map = self.properties.get_eval('blocking.map', default={})

    x = y = 0
    for row in blocking_matrix:
      for column in row:
        block_key = blocking_map.get(column, None)
        if block_key:
          if isinstance(block_key, tuple):
            block = Block(x, y, block_key, self.renderer)
            self.block_manager.add(block, x/32, y/32)
        x += 32
      y += 32
      x = 0

  def _set_sprite(self, sprite_manager, key, x, y, layer):
    """Create and set sprite in renderer from mapping key, location and
    layer."""
    if key is not None:
      sprite = sprite_manager.get_sprite(key, x, y)
      self.renderer.add(sprite, layer=int(layer))

  def get_size(self):
    """Get size of room surface to be rendered."""
    return self.size

  def get_rendered_surface(self):
    """Get a full rendered surface of the room."""
    surface = pygame.Surface(self.get_size())
    surface.fill((32, 32, 32))
    surface = surface.convert()
    self.renderer.draw_all(surface)
    return surface.convert()
