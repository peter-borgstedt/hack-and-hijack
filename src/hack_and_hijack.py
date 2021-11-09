#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*
from __future__ import print_function
import pygame

from pygame.locals import KEYDOWN, QUIT, K_ESCAPE, K_F1
from view import *
from pygame.constants import K_SPACE, SRCALPHA
from context import Context
from utilities import OptionDialog
import utilities
from transitions import BitBlipper

"""
Interactive game with the concept of learning IT-security.

Practices:
+ Comply to PEP 0008 for programming with modules, classes, methods and
  functions (Style Guide for Python Codestyle), see:
  https://www.python.org/dev/peps/pep-0008
+ Comply to PEP 0257 (Docstring convention), see:
  https://www.python.org/dev/peps/pep-0257

@author: Peter Borgstedt (peter.borgstedt@gmail.com)
"""


class HackAndHijack():

  def _build_view(self, screen, room):
    """Build view, used in when rendering the room surface. Will create
    rectangles based on _player position and several other factors like
    _player position, window size, view_size and offset."""
    window_size = screen.get_size()
    view_size = room.get_size()
    # Indent surface 32px on right, left, top and 64px on the bottom.
    window_offset = (32, 32, -64, -128)
    return View(window_size, view_size, offset=window_offset)

  def __init__(self):
    """Initialize all variables that is needed to conduct all necessary
    functionality to run the game properly."""

    self._context = Context()  # Will initiate pygame.
    self._debug = self._context.get_debug()
    self._screen = self._context.get_screen()
    self._room = self._context.create_room("main_room")
    self._room_surface = self._room.get_rendered_surface()
    self._view = self._build_view(self._screen, self._room)
    self._player = self._room.renderer._player
    self._bar = self._context.get_bar()
    self._context.get_audio_manager().load_music('title')
    # grid = d.draw_grid(room.get_size())

  def run(self):
    """This will start the game. Screen will display graphics and
    interaction will be responsive."""
    init_surface = self._init_render()  # Render screen.
    print('hej')

    # TODO: load image from configuration instead.
    self._show_splash('tiles/help.png', init_surface)

    # If user Quit in splash screen, otherwise the music start breifly
    # then the program quit.
    self._inquire_events()

    # Play background music.
    self._context.get_audio_manager().play_music()

    clock = self._context.get_clock()
    while self._inquire_events():
      # Render remaining time on screen.
      self._context.tick_and_draw()

      # Check and perform move on _player character.
      self._player.inquire_move(self._room.block_manager)

      # Update view with _player sprite position.
      self._view.update(self._player)

      if self._room.renderer.draw(self._room_surface):
        # Drawing to screen directly to increases performance.
        self._screen.blit(self._room_surface, *self._view.get_rect())

        # We do not not use hardware acceleration, so flip is not of
        # any use. Change this if hardware acceleration should be
        # activated.
        pygame.display.update(self._view.get_clip())

      clock.tick(60)

  def _show_game_state(self, header, dialog_text):
    """Show game over splash. Show options to quit or play the game
    again (Yes or No), the mouse is used to click on buttons or use keys
    (J/j, N/n)."""
    font = self._context.get_font('clacon', 100)
    g_over = font.render(header, 0, (255, 255, 255))
    sw, sh = self._screen.get_size()
    w, h = g_over.get_size()
    gp_x, gp_y = ((sw - w) / 2, (sh - h) / 2)
    self._screen.blit(g_over, (gp_x, gp_y))
    p_y = gp_y + h + 8  # Y alignment with 8 pixel indentation.
    return self._show_replay_dialog(dialog_text, y=p_y)

  def _show_replay_dialog(self, dialog_text, **kwargs):
    dialog_size = (9 * 32, 4 * 32)
    option_dialog = OptionDialog(self._context, dialog_size, dialog_text,
                                 lambda: True,
                                 lambda: utilities._quit(self._context,
                                                         False), **kwargs)
    return option_dialog.show()

  def _show_help(self):
    # TODO: load image from configuration instead.
    image = pygame.image.load('tiles/help.png').convert_alpha()
    out_position = utilities.get_center_of(self._screen, image)

    screen_backup = utilities.get_screen_backup(self._screen)
    black_alpha = pygame.Surface(self._screen.get_size(), SRCALPHA)
    black_alpha.fill((0, 0, 0, 128))
    self._screen.blit(black_alpha, (0, 0))
    self._screen.blit(image, out_position)
    pygame.display.update()

    while True:
      for e in pygame.event.get():
        if e.type == QUIT:
          # -1 will run quit dialog.
          self._context.get_model()._active = -1
          return
        if e.type == KEYDOWN and e.key in (K_ESCAPE, K_F1):
          self._screen.blit(screen_backup, (0, 0))
          pygame.display.update()
          return

  def _show_splash(self, image_file, init_surface):
    """Show _image on screen with option (ESC) to return."""
    image = pygame.image.load(image_file).convert_alpha()
    out_position = utilities.get_center_of(self._screen, image)

    self._screen.fill((0, 0, 0))
    pygame.display.update()

    bit_blipper = BitBlipper(self._context, self._screen.get_rect())
    bit_blipper.fade_in(self._screen, image, out_position)
    while True:
      for e in pygame.event.get():
        if e.type == QUIT:
          if self._show_quit_dialog():
            return  # Quit
        if e.type == KEYDOWN and e.key in (K_ESCAPE, K_F1):
          bit_blipper.fade_out(self._screen, image, init_surface,
                               out_position)
          return
      bit_blipper.draw(self._screen)
      pygame.display.update()

  def _inquire_events(self):
    """The main events handling."""
    if self._context.get_model()._active == -1:
      # -1 means that the quit dialog should be displayed.
      self._show_quit_dialog()
    if self._context.get_model()._active == 0:
      # Note that _active can be set from other places than here.
      return False

    if self._context.get_time_left() < 1:
      if not self._time_is_up():  # Time is up, show quizz dialog.
        return  # Quit

    for e in pygame.event.get():
      if e.type == QUIT or e.type == KEYDOWN and e.key == K_ESCAPE:
        self._show_quit_dialog()

      if e.type == KEYDOWN:
        if e.key == pygame.K_F1:
          self._show_help()
        if e.key == K_SPACE:
          self._interact()  # Interact with sprite

    # Check whether volume is being changed.
    self._context.inquire_audio_volume_change()
    return True

  def _show_quit_dialog(self):
    # NOTE: pygame.quit() is not really necessary, pygame will
    # destroy itself upon exit -- if flow is probably structured.
    screen_backup = utilities.get_screen_backup(self._screen)
    if utilities.show_quit_dialog(self._context):
      self._context.get_model()._active = 0
      return True
    else:
      self._screen.blit(screen_backup, (0, 0))
      pygame.display.update()
      return False

  def _time_is_up(self):
    """Run when time is up. A quizz will be displayed, if it is succeded
    the level is finished. If _player fail 'GAME OVER' will be displayed
    with the option to quit the game or restart."""
    if not self._context.get_quizz().run():
      if self._context.get_model()._active == 0:
        return False  # Quit

      # Paint red alpha on screen, visualizing alarm, in other words
      # 'GAME OVER'.
      red_alpha = pygame.Surface(self._screen.get_size(), SRCALPHA)
      red_alpha.fill((255, 0, 0, 75))
      self._screen.blit(red_alpha, (0, 0))
      if self._show_game_state('GAME OVER!', 'Vill du spela igen?'):
        # Restart if _player has chosen to play again.
        self._restart()
#                self._screen.blit(screen_backup, (0, 0))
        return True  # Restart game.
      else:
        return False  # Quit
    else:
      # TODO: refactor this, its almost identical to the GAME OVER
      # code segment.
      black_alpha = pygame.Surface(self._screen.get_size(), SRCALPHA)
      black_alpha.fill((0, 0, 0, 128))
      self._screen.blit(black_alpha, (0, 0))
      if self._show_game_state('DU VANN!', 'Vill du spela igen?'):
        # Restart if _player has chosen to play again.
        self._restart()
#                self._screen.blit(screen_backup, (0, 0))
        return True  # Restart game.
      else:
        return False  # Quit

  def _init_render(self):
    """Render screen with a initialized game state. Used in the beginning
    and when game is restarted. This will draw the whole screen, else the
    screen will be black until the _player move the character. The renderer
    will only render when it has to, and only redraw those sprites that
    has been flagged _dirty."""
    init_surface = pygame.Surface(self._screen.get_size())
    # TODO: load image from configuration instead.
    image = pygame.image.load('tiles/screen.png').convert()
    init_surface.blit(image, (0, 0))
    self._bar.update(init_surface)
    self._view.update(self._player)
    init_surface.blit(self._room_surface, *self._view.get_rect())
    self._context.blit_remaining_time(init_surface)
    self._context.blit_music_volume(init_surface)
    self._context.blit_sound_volume(init_surface)
    return init_surface

  def _restart(self):
    """Restart game, resetting model and sprite states."""
    self._context.get_model()._time = 0
    for sprite in self._room.renderer._spritelist:
      sprite.reset()
      sprite._dirty = 1
      self._room.renderer.modify_dirty(sprite)
    self._screen.blit(self._init_render(), (0, 0))
    pygame.display.update()

  def _interact(self):
    """Initialize interaction with colliding sprites."""
    rect = self._player.get_rect()
    sprites = self._room.renderer.get_flat_sprites_at(rect)
    for sprite in sprites:
      if sprite.interaction(self._context, self._player):
        break


if __name__ == '__main__':
  HackAndHijack().run()
