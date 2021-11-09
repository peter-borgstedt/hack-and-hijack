#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*

import pygame
from utilities import TimeCount, add_to_set_in_dict, get_grid_data
import debug

from random import randint

__all__ = ['DirtyLayerGrid', 'SingleEntity', 'DynamicEntity',
           'VisibilityEntity', 'HideOnCollideEntity', 'InteractionEntity',
           'SquareEntity', 'PlayerEntity']


"""
Contains sprites and sprite a optimized grid renderer.

Practices:
+ Comply to PEP 0008 for programming with modules, classes, methods and
  functions (Style Guide for Python Codestyle), see:
  https://www.python.org/dev/peps/pep-0008
+ Comply to PEP 0257 (Docstring convention), see:
  https://www.python.org/dev/peps/pep-0257

@author: Peter Borgstedt (pebo6883@it.su.se)
"""


class DirtyLayerGrid(pygame.sprite.Sprite):
  """Handles drawing of all sprites in the map. Will paint and repaint
  dirty sprites. Created with efficiency and performance in mind.

  I did not like the functionality and implementation of the LayerDirty
  group. I needed something simple and super fast. This class extends the
  Sprite with just the methods and functionality I need.

  @note: Requires all sprites to be of type pygame.sprite.DirtySprite.
  """

  def __init__(self, name):
    super(DirtyLayerGrid, self).__init__()
    self.name = name
    self._spritelist = []  # List of all sprites, for fast iteration.
    self._sprite_matrix = {}  # Y-grid -> X-grid -> Layer -> (X-) sprites.
    self._layer_to_dirty = {}  # Layer -> dirty sprites.
    self._listeners = {}
    self._collided_sprites = set()
    self._player = None

  def draw_all(self, surface, **kwargs):
    """Draw all sprites, whether they are dirty or not. Clear any
    existing dirty sprites.
    Possible to draw specific layer 'layer' as key word argument."""
    layer_to_sprites = {}
    for sprite in self._spritelist:
      add_to_set_in_dict(layer_to_sprites, sprite, sprite._layer)

    layers = None
    if 'layer' in kwargs:
      layers = [kwargs['layer']]
    else:
      layers = sorted(layer_to_sprites.keys())

    for layer in sorted(layers):
      dirty_sprites = self._layer_to_dirty.get(layer, set())
      for sprite in layer_to_sprites[layer]:
        sprite.draw(surface)
#                self._draw_sprite_grid(sprite, surface)
        sprite._dirty = 0
      dirty_sprites.clear()

  def _create_grid_sprites(self):
    """TODO: Unfinished, remove or finish. Show in debug."""
    for y in range(0, 14):
      for x in range(0, 14):
        y * 32
        x * 32

  def _draw_sprite_grid(self, sprite, surface):
    """TODO:Replace with grid layer, or remove."""
    if isinstance(sprite, PlayerEntity):
      return

    rect = sprite.get_rect()
    x_list = [(rect.x, rect.y + rect.height - 1),
              (rect.x + rect.width - 1, rect.y + rect.height - 1)]
    y_list = [(rect.x + rect.width - 1, rect.y),
              (rect.x + rect.width - 1, rect.y + rect.height - 1)]
    pygame.draw.lines(surface, (255, 0, 0), False, x_list, 1)
    pygame.draw.lines(surface, (255, 0, 0), False, y_list, 1)

  def draw(self, surface):
    """Draw dirty sprites, return True/False whether any sprites where
    drawn or not."""
    sprites_drawn = 0
    for layer in sorted(self._layer_to_dirty.keys()):
      dirty_layer = self._layer_to_dirty.get(layer)
      for dirty_sprite in set(dirty_layer):
        dirty_sprite.draw(surface)
#                self.draw_sprite_grid(dirty_sprite, surface)
        sprites_drawn += 1
        # If _dirty is 2, then it should always be rendered.
        if dirty_sprite._dirty == 1:
          dirty_sprite._dirty = 0
        self.modify_dirty(dirty_sprite)

    if debug.DEBUG is True and sprites_drawn > 0:
      print('[DEBUG - sprites.DirtyLayerGrid.draw - %s] %s sprites drawn' \
          % (self.name, sprites_drawn))
    return sprites_drawn > 0

  def add_event_listeners(self, listener, event_type):
    """Add event listener, current possible events:
        'collide_in': run when a PlayerEntity is entering the sprite.
        'collide_in': run when a PlayerEntity is exited the sprite.
    """
    listeners = self._listeners.get(event_type, None)
    if listeners is None:
      self._listeners[event_type] = listeners = []
    listeners.append(listener)

  def set_colliding_dirt(self, player):
    """Set the given sprite and any colliding neighbours to _dirty."""
    player._dirty = 1
    self.modify_dirty(player)
    surrounding_sprites = self.get_flat_sprites_at(player.get_rect())
    previous, current = self._get_current_and_previous(surrounding_sprites)
    if len(surrounding_sprites) > 0:
      for sprite in surrounding_sprites:
        if sprite._dirty == 0:
          sprite._dirty = 1
          self.modify_dirty(sprite)

    for s in current:
      # If _Entity.collide_in return True it indicated that
      # any existing listeners should be run.
      if s.collide_in(player):
        self._run_listeners('collide_in', s)
        if debug.DEBUG:
          print('[DEBUG - Entity.collide] Collide out in %s'\
              % type(s))

    for s in previous:
      # If _Entity.collide_out return True it indicated that
      # any existing listeners should be run.
      if s.collide_out(player):
        self._run_listeners('collide_out', s)
        if debug.DEBUG:
          print('[DEBUG - Entity.collide] Collide out in %s'\
              % type(s))

  def _get_current_and_previous(self, surrounding_sprites):
    """Retrieve current and previous collided sprites.
    TODO: use method intersect and diff with a Set instead, may be
    give some performance boost, and less code."""
    previous = []
    current = []
    for sprite in self._collided_sprites:  # Previous collided sprites.
      if sprite in surrounding_sprites:
        current.append(sprite)
      else:
        previous.append(sprite)
    self._collided_sprites = surrounding_sprites
    return previous, current

  def _run_listeners(self, event_type, sprite):
    """Run listeners that inquire following event_type."""
    listeners = self._listeners.get(event_type, None)
    if listeners is not None:
      for listener in listeners:
        listener(sprite)

  def get_dirty_size(self):
    """Get current amount of _dirty sprites."""
    size = 0
    for value in list(self._layers_to_dirty.values()):
      size += len(value)
    return size

  def _add_player(self, player, layer):
    """Add specifically the _player sprite to renderer."""
    if self._player is None:
      player._layer = layer
      player.add_internal(self)
      self._spritelist.append(player)
      self._add_dirty(player)
      self._player = player

  def add(self, *sprites, **kwargs):
    """Add sprite to renderer."""
    layer = kwargs.get('layer', 0)
    for sprite in sprites:
      if isinstance(sprite, PlayerEntity):
        self._add_player(sprite, layer)
      else:
        sprite._layer = layer
        sprite.add_internal(self)
        self._spritelist.append(sprite)
        self._add_sprite_to_grid(sprite)
        self._add_dirty(sprite)

  def add_dirt(self, grid_positions):
    """Add dirt on all sprites in grid positions. Matrix uses following
    structure: {y1:(x1, ...), ...}"""
    for y in list(grid_positions.keys()):
      y_sprites = self._sprite_matrix[y]  # Should not be None.
      for x in grid_positions[y]:
        for layer in list(y_sprites.get(x, None).values()):
          for sprite in layer:
            sprite._dirty = 1
            self._add_dirty(sprite)

  def _add_dirty(self, sprite):
    """Will add sprite to queue of _dirty sprites to be repainted. Will
    then modify the _dirty flag to not _dirty."""
    if sprite._dirty == 1:
      self.modify_dirty(sprite)
    elif sprite._dirty == 2:
      self._append_dirty_if_absence(sprite, sprite._layer)

  def get_sprites_at(self, target_rect):
    """Get sprite from target rectangle (currently only support 32x32)."""
    return get_grid_data(target_rect, self._sprite_matrix)

  def get_flat_sprites_at(self, target_rect):
    """Get sprite all layers of given target rectangle (currently only
    support 32x32). Do a flattening and return all sprites in alist.
    TODO: Use set instead for hash operations?
    """
    sprites = set()
    target_sprites = self.get_sprites_at(target_rect)
    if target_sprites is not None:
      for layers in target_sprites:
        sprites.update([i for sl in list(layers.values()) for i in sl])
    return sprites

  def _add_sprite_to_grid(self, sprite):
    """Add sprite to grid matrix mapping x, y, layer to sprites.
    Following data types and structure is used:
    dict(y-grid) -> dict(x-grid) -> dict(layer) -> Set(sprites).
    TODO: Read tile resolution from config.
    """
    x = sprite.get_rect().x / 32
    y = sprite.get_rect().y / 32
    columns = self._sprite_matrix.get(y, None)
    if columns is None:
      self._sprite_matrix[y] = {x: {sprite._layer: [sprite]}}
    else:
      layers = columns.get(x, None)
      if layers is None:
        columns[x] = layers = {}
      layer = layers.get(sprite._layer, None)
      if layer is None:
        layers[sprite._layer] = layer = set()
      layer.add(sprite)

  def modify_dirty(self, sprite):
    """Modify sprite that are dirty. Append them to the queue.

    """
    layer = sprite._layer
    if sprite._dirty == 1:
      add_to_set_in_dict(self._layer_to_dirty, sprite, layer)
    elif sprite._dirty == 0:
      try:
        self._layer_to_dirty.get(layer).remove(sprite)
      except:
        pass  # Intentionally ignore exception


class _Entity(pygame.sprite.DirtySprite):
  """Abstract sprite, contain some standard methods and functionality.
  This class is used only by extending it in other classes.
  _dirty attribute flag: 0: clean, 1: dirty, 2: always dirty"""

  def __init__(self, rect):
    super(_Entity, self).__init__()
    self._rect = rect
    self._dirty = 1  # Initial value.
    self._visible = 1  # Initial value.

  def get_rect(self):
    """Get rectangle."""
    return self._rect

  def draw(self, surface):
    pass  # Overridden in extension classes.

  def collide_out(self, _self):
    # Overridden in extension classes.
    return False  # Do not run listeners if any are present.

  def collide_in(self, _self):
    # Overridden in extension classes.
    return False  # Do not run listeners if any are present.

  def interaction(self, _context, _player):
    # Overridden in extension classes.
    return False  # Indicated an interaction has not been run.

  def reset(self):
    pass  # Overridden in extension classes.

  # Overridden, see: pygame.sprite.DirtySprite.update(self, *args)
  def update(self, *args):
    pass  # Intentionally bypassing method.


class SingleEntity(_Entity):
  """Sprite entity that can display a tile image."""

  def __init__(self, images, x, y):
    super(SingleEntity, self).__init__(pygame.Rect(x, y, 32, 32))
    self._image = images[0]

  def draw(self, surface):
    """Draw tile."""
    surface.blit(self._image, self._rect)


class DynamicEntity(_Entity):
  """Sprite entity that can display a range of tile images depending
  on the image index set."""

  def __init__(self, images, x, y):
    super(DynamicEntity, self).__init__(pygame.Rect(x, y, 32, 32))
    self._images = images
    self._index = 0

  def draw(self, surface):
    """Draw tile from current index."""
    surface.blit(self._images[self._index], self._rect)

  def reset(self):
    """Set sprite to initialized state."""
    self._index = 0


class VisibilityEntity(SingleEntity):
  """Sprite entity same as the SingleEntity but contain also the attribute
  _visible which can be set either 0 (not visible) or 1 (visible).
  @note: only visible entities is drawn."""

  def __init__(self, images, x, y):
    super(VisibilityEntity, self).__init__(images, x, y)

  def draw(self, surface):
    """Draw only if sprite entity is visible."""
    if self._visible == 1:
      SingleEntity.draw(self, surface)

  def reset(self):
    self._visible = 1


class InteractionEntity(SingleEntity):
  """Complex sprite entity that is used to run interactions.
  When collided in or out the north sprite of this entity will change state
  (image index) if it is of a DynamicEntity type. Will only paint north
  neigbhour sprite if the interaction has not been performed and the
  PlayerEntity is faced upwards."""

  def __init__(self, images, x, y):
    super(InteractionEntity, self).__init__(images, x, y)
    self._interacted = 0

  def interaction(self, context, player):
    """Retrieve random interaction from context and run it."""
    if player._tile_key != 'up' or self._interacted == 1:
      return  # only interact if _player is positioned upward
    self._interacted = 1
    self.collide_out(player)
    context.get_random_interaction().run()
    return True  # Indicated an interaction been run.

  def _get_north_sprite(self):
    """Get sprite north of this sprite."""
    # Kind of ugly, seems like a hack. We probably should do something
    # nicer here. Also if a sprite is in several groups (which will not
    # happen in current implementation) we only act on the first.
    g = self.groups()[0]
    x = self._rect.x / 32
    y = (self._rect.y / 32) - 1  # Get grid y one above current one.
    spr = []  # Sprites
    spr.extend([i for sl in list(g._sprite_matrix[y][x].values()) for i in sl])
    for sprite in spr:
      if isinstance(sprite, DynamicEntity):
        # Only get first occurring, should not occur more than one.
        return sprite

  def _set_state_north_sprite(self, sprite, index):
    """Change image index on north sprite and send to the rendering
    queue for repaint."""
    sprite._index = index
    sprite._dirty = 1
    self.groups()[0]._add_dirty(sprite)

  def collide_out(self, _player):
    """Set image index to 0 on north sprite."""
    self._set_state_north_sprite(self._get_north_sprite(), 0)
    return False  # Do not run listeners if any are present.

  def collide_in(self, player):
    """Set image index to 1 on north sprite if charactered is faced
    upward and this entity sprite has not been interacted."""
    sprite = self._get_north_sprite()
    if player._tile_key == 'up' and self._interacted == 0:
      self._set_state_north_sprite(sprite, 1)
    elif sprite._index == 1:
      self._set_state_north_sprite(sprite, 0)
    return False  # Do not run listeners if any are present.

  def reset(self):
    """Set sprite to initialized state."""
    self._interacted = 0


class HideOnCollideEntity(VisibilityEntity):
  """Sprite entity that is being hidden when collided."""

  def __init__(self, images, x, y):
    super(HideOnCollideEntity, self).__init__(images, x, y)

  def collide_in(self, _self):
    if self._visible == 1:
      self._visible = 0
      return True  # Run listeners.
    return False  # Do not run listeners.


class RandomHideOnCollideEntity(DynamicEntity):
  """Sprite entity that display random tile and is hidden when collided."""

  def __init__(self, images, x, y):
    super(RandomHideOnCollideEntity, self).__init__(images, x, y)
    self.reset()

  def draw(self, surface):
    """Draw tile from current index."""
    if self._visible:
      DynamicEntity.draw(self, surface)

  def collide_in(self, _self):
    if self._visible == 1:
      self._visible = 0
      return True  # Run listeners.
    return False  # Do not run listeners.

  def reset(self):
    """Set sprite to initialized state."""
    self._visible = 1
    self._index = randint(0, len(self._images) - 1)


class SquareEntity(SingleEntity):
  """Sprite entity that will draw a rectangle filled with a given color."""

  def __init__(self, color, x, y):
    super(SquareEntity, self).__init__([pygame.Surface((32, 32))], x, y)
    self._image.fill(color)
    self._image = self._image.convert()


class PlayerEntity(_Entity):
  """Player entity sprite, can only contain one in each DirtyLayer.
  Moves and interacts with other sprites. Contains several tiles that is
  animated with a set delay. PlayerEntity can be positioned up, down, right
  and left. PlayerEntity will trigger the DirtyLayer when collisions is
  done over sprites."""
  _MOVE_AMOUNT = 3  # Pixels

  def __init__(self, tiles, x, y):
    super(PlayerEntity, self).__init__(None)  # Set rectangle below.
    self._image = pygame.Surface((32, 32))
    _, _, w, h = self._image.get_rect()
    self._start_position = (x, y)
    self._start_direction = 'down'  # Start by pointing character down.
    self._rect = pygame.Rect(x, y, w, h)
    self._tiles = tiles
    self._tile_key = self._start_direction
    self._tile_index = 0
    self._dirty = 1
    self._delay = TimeCount(100, True)  # Milliseconds.

  def draw(self, surface):
    """Overridden method in _Entity."""
    surface.blit(self._tiles[self._tile_key][self._tile_index],
                 self._rect)

  def inquire_move(self, block_manager):
    """Validate if any responsive keys have been pressed and act upon
    them."""
    keys = pygame.key.get_pressed()
    if pygame.key.get_mods() & (pygame.KMOD_CTRL | pygame.KMOD_SHIFT):
      return

    if keys[pygame.K_UP]:
      self._move_up(block_manager)
    elif keys[pygame.K_DOWN]:
      self._move_down(block_manager)
    elif keys[pygame.K_LEFT]:
      self._move_left(block_manager)
    elif keys[pygame.K_RIGHT]:
      self._move_right(block_manager)

  def _move_up(self, block_manager):
    """Move the character upward."""
    tmp = pygame.Rect(self._rect)
    tmp.top -= self._MOVE_AMOUNT
    self._move_direction(block_manager, tmp, 'up')

  def _move_down(self, block_manager):
    """Move the character downward."""
    tmp = pygame.Rect(self._rect)
    tmp.top += self._MOVE_AMOUNT
    self._move_direction(block_manager, tmp, 'down')

  def _move_left(self, block_manager):
    """Move the character leftward."""
    tmp = pygame.Rect(self._rect)
    tmp.left -= self._MOVE_AMOUNT
    self._move_direction(block_manager, tmp, 'left')

  def _move_right(self, block_manager):
    """Move the character rightward."""
    tmp = pygame.Rect(self._rect)
    tmp.left += self._MOVE_AMOUNT
    self._move_direction(block_manager, tmp, 'right')

  def _move_direction(self, block_manager, tmp, direction):
    """Move character if no collision exist. Set tile index and
    position on character."""
    print('hej')
    if not self._check_collision(block_manager, tmp):
      # Must repaint previous location before the new rectangle is set.
      self._tile_key = direction
      self._set_dirty()
      self._rect = tmp
      if self._delay.is_obsolete():
        self._tile_index = ((self._tile_index + 1) % 4)
    elif self._tile_key != direction:
      self._tile_key = direction
      self._set_dirty()
      # We want to repaint character when changing direction state,
      # even though its blocked.
      return

  def _set_dirty(self):
    """Set self and colliding sprites as _dirty."""
    for group in self.groups():
      if isinstance(group, DirtyLayerGrid):
        group.set_colliding_dirt(self)

  def _check_collision(self, block_manager, tmp):
    """Validate if there are any collusion on the new position."""
    if debug.DEBUG:
      print('[DEBUG - sprites.Player] Grid position [x: %s, y: %s]'\
          % (int(float(tmp.x) % 32), int(float(tmp.y) % 32)))
    return block_manager.collide(tmp)

  def reset(self):
    """Reset to initialized state."""
    self._rect.x = self._start_position[0]
    self._rect.y = self._start_position[1]
    self._tile_index
    self._tile_key = self._start_direction
