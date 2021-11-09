# -*- coding: iso-8859-1 -*

import os
import pygame
import manager
import config_reader
import quiz
import room
import mini_games
import random
import utilities
import debug


"""
Game context. A wrapper with resources that is used in the game.

Practices:
+ Comply to PEP 0008 for programming with modules, classes, methods and
  functions (Style Guide for Python Codestyle), see:
  https://www.python.org/dev/peps/pep-0008
+ Comply to PEP 0257 (Docstring convention), see:
  https://www.python.org/dev/peps/pep-0257

@author: Peter Borgstedt (peter.borgstedt@gmail.com)
"""


class Context():
  """Game context. A wrapper that contain contain resource and functionality
  classes that is continuously used in the game."""

  def __init__(self):
    self._init()
    self._clock = pygame.time.Clock()

    self._fonts = self._setup_fonts()
    loader = _Loader(self.get_font('clacon', 21))

    # TODO: Use same font?
    self._audio_font = self.get_font('clacon', 21)
    self._time_font = self.get_font('clacon', 21)
    self._debug = debug.DEBUG

    self._config = loader._config
    self._screen = loader.create_screen()
    loader.draw_loading(self._screen)  # Draw 'Loading..." on screen.

    self._quizz = loader.create_quizz(self)
    self._model = loader.create_model()
    self._tile_manager = loader.create_tile_manager()
    self._audio_manager = loader.create_audio_manager()
    self._sprite_manager =\
        loader.create_sprite_manager(self._tile_manager,
                                     self._audio_manager)
    self._bar = loader.create_bar(self._screen)
    self._interaction = self._build_interactions()

  def _init(self):
    """Initialize pygame."""
    # TODO: Use audio settings from configuration?
    pygame.mixer.pre_init(44100, -16, 1, 1024)
    pygame.init()  # Initiate pygame
    pygame.display.set_caption('Hack and hijack')

  def get_debug(self):
    """Get instance of debugger."""
    return self._debug

  def get_clock(self):
    """Get instance of clock."""
    return self._clock

  def _build_interactions(self):
    """Build interactions.
    TODO: move to loader?
    TODO: Read from configuration what interaction should be loaded."""
    return {'bit_coin_collector':
            mini_games.Collector(self, 'bit_coin_collector'),
            'bit_eater':
            mini_games.Collector(self, 'bit_eater')}

  def _setup_fonts(self):
    """Setup font "library", we probably want to load these from the
    configuration.
    TODO: Read and build dictionary from configuration instead.
    """
    return {'clacon': 'resources/clacon.ttf',
            'pc_keys': 'resources/pckeys.ttf',
            'digital': 'resources/digital-7.ttf'}

  def get_bar(self):
    """Get instance of bar wrapper."""
    return self._bar

  def increase_music_volume(self):
    """Increases music volume and paint the new amount on the bar."""
    self._audio_manager.increase_music_volume()
    self.draw_music_volume()

  def decrease_music_volume(self):
    """Decreases music volume and paint the new amount on the bar."""
    self._audio_manager.decrease_music_volume()
    self.draw_music_volume()

  def increase_sound_volume(self):
    """Increases sound volume and paint the new amount on the bar."""
    self._audio_manager.increase_sound_volume()
    self.draw_sound_volume()

  def decrease_sound_volume(self):
    """Decreases sound volume and paint the new amount on the bar."""
    self._audio_manager.decrease_sound_volume()
    self.draw_sound_volume()

  def get_font(self, font_id, size, **kwargs):
    """ TODO: Cache? May be some performance benefits in caching fonts that
    are being reused often.
    """
    path = self._fonts.get(font_id, None)
    if path is None:
      # If no font is found, return default (MONOSPACE).
      return pygame.font.SysFont("MONOSPACE", size, **kwargs)
    return pygame.font.Font(path, size, **kwargs)

  def get_screen_size(self):
    """Get the (main-) screen size."""
    return self._screen.get_size()

  def get_screen(self):
    """Get the (main-) screen surface."""
    return self._screen

  def get_quizz(self):
    """Return quizz, not sure this should be here, probably should exist
    in the context and not model."""
    return self._quizz

  def create_room(self, config_section):
    """Create a room with from given room-id, see configuration."""
    return room.Room(config_section, self)

  def get_tile_manager(self):
    """Get the tile manager, containing cached images/tiles."""
    return self._tile_manager

  def get_sprite_manager(self):
    """Get the sprite manager, create sprites of several types."""
    return self._sprite_manager

  def get_audio_manager(self):
    """Get the audio manager, load and play sounds and music."""
    return self._audio_manager

  def get_config(self):
    """Get full configuration."""
    return self._config

  def get_random_interaction(self):
    """Get a random interaction."""
    return self._interaction[random.choice(self._interaction.keys())]

  def get_model(self):
    """Get model containing current game state."""
    return self._model

  def blit_remaining_time(self, surface):
    """Blit remaining time on screen."""
    text = 'Kvarst�eende tid: ' + str(max(self.get_time_left(), 0))
    return self._blit_bar_text(text, surface, (32, 22, 8*32, 32*2))

  def tick_and_draw(self):
    """Tick time, if time is obsolete blit on screen and update display."""
    if not self._model.tick_time():
      return
    pygame.display.update(self.blit_remaining_time(self._screen))

  def _blit_bar_text(self, caption, surface, rect):
    """Blit text on bar."""
    font_surface = self._audio_font.render(caption, 1, (255, 255, 255))
    _, y = self._bar._position
    p_x, p_y, w, h = rect
    s_y = y + p_y
    bar_image = self._bar._image
    surface.blit(bar_image, (p_x, s_y), (p_x, p_y, w, h))
    surface.blit(font_surface, (p_x, s_y))
    return (p_x, s_y, w, h)

  def blit_music_volume(self, surface):
    """Blit current music volume on screen."""
    music_volume = self._audio_manager._music_volume
    caption = self._audio_manager._MUSIC_VOL_CAPTION.format(music_volume)
    rect = (28 * 32, 22, 4 * 32, 32*2)
    return self._blit_bar_text(caption, surface, rect)

  def blit_sound_volume(self, surface):
    """Blit current sound volume on screen."""
    sound_volume = self._audio_manager._sound_volume
    caption = self._audio_manager._SOUND_VOL_CAPTION.format(sound_volume)
    rect = (23 * 32, 22, 4 * 32, 32*2)
    return self._blit_bar_text(caption, surface, rect)

  def draw_music_volume(self):
    """Blit current music volume on screen and then update display."""
    pygame.display.update(self.blit_music_volume(self._screen))

  def draw_sound_volume(self):
    """Blit current sound volume on screen and then update display."""
    pygame.display.update(self.blit_sound_volume(self._screen))

  def get_time_left(self):
    """Retrieve the current time and calculate the remaining time."""
    return self._model._max_time - self._model._time

  def inquire_audio_volume_change(self):
    """Validate whether _player has pressed any key combination that
    should trigger change of audio volume."""
    keys = pygame.key.get_pressed()
    # Change volume or music, CTRL-UP/DOWN.
    if pygame.key.get_mods() & pygame.KMOD_CTRL:
      if keys[pygame.K_UP]:  # Increase music volume.
        self.increase_music_volume()
      if keys[pygame.K_DOWN]:  # Decrease music volume.
        self.decrease_music_volume()

    # Change volume or sound, SHIFT-UP/DOWN.
    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
      if keys[pygame.K_UP]:  # Increase sound volume.
        self.increase_sound_volume()
      if keys[pygame.K_DOWN]:  # Decrease sound volume.
        self.decrease_sound_volume()


class Model():
  """Model, contain game state and data."""

  def __init__(self, config):
    self._active = 1  # 1: active, 0: not active (will cause exit)
    self._time = 0  # The amount of seconds that has past.
    props = config.get_properties('')
    self._max_time = props.get_eval('max_time', default=60)  # In seconds.
    self._time_ticker = utilities.TimeCount(1000, True)

  def tick_time(self):
    """Tick time, will continously validate whether time delay (1000ms)
    is obsolete or not -- and update timer if."""
    if self._time_ticker.is_obsolete():
      self._time += 1
      return True  # Time as updated (with 1000ms)
    return False  # No update yet.


class _Loader():
  """Initiating classes, is only called upon on startup when the game
  context is created."""

  _CONF_FILE = 'hack_and_hijack.conf'

  def __init__(self, font):
    self._config = self._load_config()
    self.font = font

  def _load_config(self):
    """Load game configuration."""
    config_file = os.path.dirname(os.path.realpath(__file__))
    config_file = os.path.join(config_file, self._CONF_FILE)
    return config_reader.ConfigReader.read_config(config_file)

  def draw_loading(self, screen):
    """Draw 'Laddar...' on screen when starting up."""
    f_surface = self.font.render('Laddar...', 1, (255, 255, 255))
    screen.blit(f_surface, utilities.get_center_of(screen, f_surface))
    # Update whole screen, no need for optimization.
    pygame.display.update()

  def create_quizz(self, context):
    """Create quizz. Requires fonts and config."""
    return quiz.Quizz(context)

  def create_model(self):
    """Creates a fresh model with initialized state."""
    return Model(self._config)

  def create_screen(self):
    """Initiate pygame and center and create (main-) screen."""
    os.environ['SDL_VIDEO_CENTERED'] = '1'  # Center dialog.
    WIN_SIZE = self._config.get_eval_property('', 'window.size')
    return pygame.display.set_mode(WIN_SIZE, 0)

  def create_tile_manager(self):
    """Create tile manager, containing all images sliced into tiles."""
    return manager.TileManager(self._config)

  def create_sprite_manager(self, tile_manager, audio_manager):
    """Create sprite manager, containing functionality for creating
    different types of sprites."""
    return manager.SpriteManager(self._config, tile_manager, audio_manager)

  def create_audio_manager(self):
    """Create audio manager, containing functionality surrounding sounds
    and music."""
    return manager.AudioManager(self._config)

  def create_bar(self, screen):
    image = pygame.image.load('tiles/bar.png').convert()
    _, h = screen.get_size()
    return Bar(image.convert(), (0, h - image.get_height()))


class Bar():
  """Wrapper class with image an position for the bar displayed in the
  bottom. Used to repaint area when painting text on screen in that certain
  surface area."""

  def __init__(self, image, position):
    self._image = image
    self._position = position

  def update(self, screen):
    """Just blit image on screen."""
    screen.blit(self._image, self._position)

  def draw(self, screen):
    """Blit on screen and update on display."""
    self.update(screen)
    pygame.display.update((self._position, self._image.get_size()))
