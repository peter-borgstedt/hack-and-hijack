# -*- coding: iso-8859-1 -*

import pygame
import os
import re

from ast import literal_eval
from pygame.locals import SRCALPHA
from utilities import TimeCount, get_grid_data
# PEP-0328: http://legacy.python.org/dev/peps/pep-0328/
from sprites import (SingleEntity, DynamicEntity, InteractionEntity,
                     HideOnCollideEntity, RandomHideOnCollideEntity,
                     SquareEntity, PlayerEntity)

__all__ = ['TileManager, SpriteManager, AudioManager', 'BlockManager', 'Block']

"""
A module containing management classes.

Practices:
+ Comply to PEP 0008 for programming with modules, classes, methods and
  functions (Style Guide for Python Codestyle), see:
  https://www.python.org/dev/peps/pep-0008
+ Comply to PEP 0257 (Docstring convention), see:
  https://www.python.org/dev/peps/pep-0257

@author: Peter Borgstedt (peter.borgstedt@gmail.com)
"""


class TileManager():
  """Manage all reading of tile images. Images are read then segments are
  split and cached."""

  def __init__(self, config):
    self.tile_size = config.get_eval_property('', 'image.tile.size')
    self.tile_config = config.get_prefixed_properties('tile')
    self.tiles = self._read_image_files()

  def get_tiles(self, key):
    """Get tiles from key, all segments are returned for this."""
    return self.tiles.get(key, None)

  def get_tile(self, key, position):
    """Get tile from key and position, one segments is returned."""
    tiles = self.get_tiles(key)
    if tiles:
      tile_row = tiles.get(position[0], None)
      if tile_row:
        return tile_row.get(position[1], None)
    return None

  def _read_image_files(self):
    """Get tiles sections from configuration and read _image and split
    _image into tiles. The tiles are mapped with following data types and
    structure: dict(tile_section) -> dict(Y) -> dict(X) -> Surface"""
    tiles = {}
    for key in self.tile_config.get_keys():
      properties = self.tile_config.get(key)
      image_file = properties.get('image')
      path = os.path.dirname(os.path.realpath(__file__))
      image_file = path + '/' + re.sub('/', r'/', image_file)
      image = pygame.image.load(image_file)
      tiles[key] = self._read_image(image, self.tile_size, properties)
    return tiles

  def _read_image(self, image, size, properties):
    """Read one _image and split portions of it to segments.
    The tiles are stored and returned as following data types and
    structure: dict(Y) -> dict(X) -> Surface."""
    tiles = {}
    py = px = 0
    alpha = properties.get_eval('alpha', default=False)
    for y in range(0, image.get_height(), size[1]):
      py += 1
      tiles_row = {}
      for x in range(0, image.get_width(), size[0]):
        px += 1
        flag = SRCALPHA if alpha else 0
        surface = pygame.Surface((size[0], size[1]), flag)
        surface.blit(image, (0, 0), (x, y, size[0], size[1]))
        if alpha:
          surface = surface.convert_alpha()
        else:
          surface = surface.convert()
        tiles_row[len(tiles_row)] = surface
      tiles[len(tiles)] = tiles_row
    return tiles


class SpriteManager():
  """Creates sprites from configuration."""

  def __init__(self, config, tile_manager, audio_manager):
    self._sprite_config = config.get_prefixed_properties('sprite')
    self._tile_manager = tile_manager
    self._audio_manager = audio_manager

  def get_tile(self, key_and_position, x, y):
    """Get Tile sprite, a basic sprite that contains one image."""
    tiles = [self._tile_manager.get_tile(*key_and_position)]
    return SingleEntity(tiles, x, y)

  def get_sprite(self, mapping_key, x, y):
    """Get sprite from mapping key. The key represent a prefixed section,
    i.e. sprite*mapping_key."""
    properties = self._sprite_config.get(mapping_key)
    sprite_type = properties.get('type').lower()

    if sprite_type == 'square':
      return SquareEntity(properties.get_eval('color'), x, y)
    elif sprite_type == 'player':
      return PlayerEntity(self._get_keyed_tiles('player'), x, y)
    elif sprite_type == 'dynamic':
      return DynamicEntity(self._get_tiles(properties), x, y)
    elif sprite_type == 'hide_on_collide':
      return HideOnCollideEntity(self._get_tiles(properties), x, y)
    elif sprite_type == 'random_hide_on_collide':
      return RandomHideOnCollideEntity(self._get_tiles(properties), x, y)
    elif sprite_type == 'interactive':
      return InteractionEntity(self._get_tiles(properties), x, y)
    else:  # Default to Tile sprite.
      return SingleEntity(self._get_tiles(properties), x, y)

  def _get_tiles(self, sprite_properties):
    """Get tiles from the tile property in the current sprite
    configuration."""
    tile_property = sprite_properties.get_eval('tile')
    key = tile_property[0]
    values = tile_property[1]
    tiles = []
    for tile in values:
      tiles.append(self._tile_manager.get_tile(key, tile))
    return tiles

  def _get_keyed_tiles(self, key):
    """Get keyed tiles from property in the sprite configuration.
    Each tile is binded to a key, for example:
    'up': ((0,0), (0,1), ..), down: ((1,0), (1,1), ...), ..."""
    sprite_properties = self._sprite_config.get(key)
    tile = sprite_properties.get('tile')
    tile_map_str = sprite_properties.get('tile.map')
    tile_map = literal_eval(tile_map_str)

    tiles = self._tile_manager.get_tiles(tile)
    player_mapped_tiles = {}
    for key in tile_map.keys():
      player_mapped_tiles[key] = [tiles[y][x] for y, x in tile_map[key]]
    return player_mapped_tiles


class AudioManager():
  """Audio manager, contain functionality for loading and playing sounds
  and music.
  TODO: read caption from configuration?
  """
  _SOUND_VOL_CAPTION = 'Ljud: {:.2%}'
  _MUSIC_VOL_CAPTION = 'Musik: {:.2%}'
  _VOLUME_ADJUSTMENT = 0.025

  def __init__(self, config):
    # Check whether the mixer is initiated.
    self._is_inited = pygame.mixer.get_init() is not None
    # Retrieve audio configuration.
    self._audio_config = config.get_properties('audio')
    self._volume_delay = TimeCount(1000/10, True)  # 5fps
    # Set default values.
    sound_volume = self._audio_config.get('sound_volume', default=0.5)
    self._sound_volume = float(sound_volume)
    music_volume = self._audio_config.get('music_volume', default=0.25)
    self._music_volume = float(music_volume)
    # Load sounds.
    self._sound = self._load_sound()
    # Structure available music files.
    self._music = self._audio_config.get_eval('music')
    self._channels = {}

  def load_music(self, music_id):
    if self._is_inited:
      """Load music file and set current music volume."""
      pygame.mixer.music.load(self._music[music_id])
      pygame.mixer.music.set_volume(self._music_volume)

  def play_music(self):
    """Play loaded music."""
    if self._is_inited:
      pygame.mixer.music.play(-1)

  def play_sound(self, sound_id):
    """Play loaded and cached sound."""
    if self._is_inited:
      self.get_sound(sound_id).play()

  def play_sound_in_channel(self, sound_id, ch_id):
    """Play loaded and cached sound in channel."""
    if self._is_inited:
      channel = self._channels.get(ch_id, None)
      if channel is None:
        self._channels[ch_id] = channel = pygame.mixer.Channel(ch_id)
      channel.play(self.get_sound(sound_id))

  def get_sound(self, sound_id):
    """Get loaded and cached sound."""
    return self._sound.get(sound_id, None)

  def _load_sound(self):
    if not self._is_inited:
      return  # Do not load if there is no audio interface.

    """Load and cache sounds."""
    sounds = {}
    # Need to skip load if no audio, it will crash the program on runtime
    # if we try to load audio when the mixer is not initiated.
    if pygame.mixer.get_init() is None:
      return sounds  # No sound card active.

    sound_property = self._audio_config.get_eval('sound')
    for key in sound_property:
      sound = pygame.mixer.Sound(sound_property[key])
      if sound is not None:
        sound.set_volume(self._sound_volume)
        sounds[key] = sound
    return sounds

  def increase_music_volume(self):
    if not self._is_inited:
      return  # Do set volume if there is no audio interface.

    if not self._volume_delay.is_obsolete():
      return
    """Increase music volume."""
    adjustment = self._VOLUME_ADJUSTMENT
    self._music_volume = self._get_volume(self._music_volume, adjustment)
    self._adjust_audio_volume([pygame.mixer.music], self._music_volume)

  def decrease_music_volume(self):
    if not self._is_inited:
      return  # Do set volume if there is no audio interface.

    if not self._volume_delay.is_obsolete():
      return
    """Decrease music volume."""
    adjustment = -self._VOLUME_ADJUSTMENT
    self._music_volume = self._get_volume(self._music_volume, adjustment)
    self._adjust_audio_volume([pygame.mixer.music], self._music_volume)

  def increase_sound_volume(self):
    if not self._is_inited:
      return  # Do set volume if there is no audio interface.

    if not self._volume_delay.is_obsolete():
      return
    """Increase sound volume."""
    adjustment = self._VOLUME_ADJUSTMENT
    self._sound_volume = self._get_volume(self._sound_volume, adjustment)
    self._adjust_audio_volume(self._sound.values(), self._sound_volume)

  def decrease_sound_volume(self):
    if not self._is_inited:
      return  # Do set volume if there is no audio interface.

    if not self._volume_delay.is_obsolete():
      return
    """Decrease sound volume."""
    adjustment = -self._VOLUME_ADJUSTMENT
    self._sound_volume = self._get_volume(self._sound_volume, adjustment)
    self._adjust_audio_volume(self._sound.values(), self._sound_volume)

  def _adjust_audio_volume(self, audio, adjustment):
    """Adjust volume for audio with given adjustment."""
    for au in audio:
      au.set_volume(adjustment)

  def _get_volume(self, current_volume, volume_amount):
    """Calculate new volume amount."""
    return max(min(current_volume + volume_amount, 1), 0)


class BlockManager():
  """Block manager. Contain a matrix of blocks contained in the map. Each
  block contain the amount of blockage. For example, a block may only block
  50% of it's total area.

  Instead of using a list of blocks that we iterate through EACH time the
  player move the character (which is a frequent action) -- retrieve blocks
  from the character grid position.
  The implementation use a matrix and calculate the position grid and
  retrieve these a dictionary. This is ALOT faster than iterating through
  a list of sprites performing a collide_rect on each these.

  It is a fast collusion detection. It is a performance issue when
  performing collusion detection on alot of sprites."""

  def __init__(self):
    self.blocks = {}
    self.currently_blocked = []

  def add(self, block, x, y):
    """Add a blocks."""
    columns = self.blocks.get(y, None)
    if columns is None:
      self.blocks[y] = {x: block}
    else:
      columns[x] = block

  def get_blocks(self):
    """Get all blocks."""
    return self.blocks

  def collide(self, target_rect):
    """See if target_rect is colliding with any blocks, return True
    if that is the case.
    TODO: print debug message?"""

    target_blocks = get_grid_data(target_rect, self.blocks)
    if target_blocks is not None:
      for block in target_blocks:
        if block.collide(target_rect):
          return True


class Block():
  """A block consist of an area that completely or partially blocks the
  character from moving."""

  def __init__(self, x, y, modifier, renderer):
    self.renderer = renderer
    self.position_x = x / 32
    self.position_y = y / 32
    self._rect = pygame.Rect(x, y, 32, 32)
    bx, by, bw, bh = modifier
    self.block_rect = pygame.Rect(x + bx, y + by, 32 + bw, 32 + bh)

  def collide(self, target_rect):
    """Will retrieve blocks from a block matrix, which will be ALOT faster
    than iterating through a list of blocks."""
    if self.block_rect.colliderect(target_rect):
      return True
    return False
