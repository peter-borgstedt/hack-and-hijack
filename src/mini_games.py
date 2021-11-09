# -*- coding: iso-8859-1 -*

import pygame
import utilities

from pygame.locals import KEYDOWN, QUIT, K_ESCAPE, K_UP, K_DOWN

from room import Room
from view import View
from transitions import BitBlipper
from sprites import HideOnCollideEntity, RandomHideOnCollideEntity

"""
Mini game that the player collect items. Highly dynamic and configurable.

Practices:
+ Comply to PEP 0008 for programming with modules, classes, methods and
  functions (Style Guide for Python Codestyle), see:
  https://www.python.org/dev/peps/pep-0008
+ Comply to PEP 0257 (Docstring convention), see:
  https://www.python.org/dev/peps/pep-0257

@author: Peter Borgstedt (peter.borgstedt@gmail.com)
"""


class Collector():
    def __init__(self, context, game_key):
        self._context = context
        self._audio_manager = self._context.get_audio_manager()
        self._collected = 0
        config = self._context.get_config()
        self._game_config = config.get_properties('game*' + game_key)
        self._collect_sound = self._game_config.get('collect_sound')
        room_key = self._game_config.get('room')

        self._room = self._build_room(context, room_key)
        self._item_amount = self._count_collectable_items(self._room)
        self._player = self._room.renderer._player
        self._block_manager = self._room.block_manager
        self._monitor = self._build_monitor(context)

        w, h = context.get_screen().get_size()
        h -= self._context.get_bar()._image.get_height()
        self._window_clip = (0, 0, w, h)
        self._bit_blipper = BitBlipper(self._context, (0, 0, w, h))

        self._monitor_surface = self._monitor.get_rendered_surface()
        sw, sh = self._monitor_surface.get_size()
        self._monitor_position = ((w - sw)/2, (h - sh)/2)

        self._win_surface = self._room.get_rendered_surface().convert()
        self._win_size = (16*32, 11*32)

        p_x, p_y = self._monitor_position = ((w - sw)/2, (h - sh)/2)
        self._win_position = p_x + 2*32, p_y + 2*32, 0, 0

        self._view = View(self._win_size, self._room.get_size(),
                          offset=self._win_position)

        self._collect_font = self._context.get_font('digital', 30)
        self._collect_color = (25, 220, 55)

        self._dialog = self.ScreenDialog(self._context, self._win_size,
                                         self._win_position)

    def _count_collectable_items(self, room):
        """Count amount of collectable sprite entities."""
        amount = 0
        for s in room.renderer._spritelist:
            if isinstance(s, (HideOnCollideEntity, RandomHideOnCollideEntity)):
                amount += 1
        return amount

    def _build_room(self, context, game_key):
        """Build from config and initialize game."""
        room = context.create_room(game_key)
        renderer = room.renderer
        renderer.active = 0
        renderer.add_event_listeners(lambda _s: self._collect(), 'collide_in')
        return room

    def _collect(self):
        """Will be run each timer the event listener is triggered, which is
        listening on 'collide' events."""
        self._audio_manager.play_sound_in_channel(self._collect_sound, 0)
        self._collected += 1
        # Clear the surface as the collected will be rendered.
        # Send event to renderer queue that following grid positions are
        # dirty. The renderer will then take care of business.
        cols = (1, 2, 3, 4, 5)
        self._monitor.renderer.add_dirt({14: cols, 15: cols})

    def _build_monitor(self, context):
        return Room('monitor', context)

    def _init(self):
        self._collected = 0
        self._view.update(self._player)
        self._draw_collected(self._monitor_surface)

    def _reset(self):
        for sprite in self._room.renderer._spritelist:
            sprite.reset()

    def run(self):
        screen = self._context.get_screen()
        self._init()

        out_surface = pygame.Surface(screen.get_size())
        out_surface.blit(screen, (0, 0))

        in_surface = pygame.Surface(self._monitor_surface.get_size())
        in_surface.blit(self._monitor_surface, (0, 0))
        in_surface.blit(self._win_surface, (64, 64), self._view.get_rect()[1])

        self._fade_in(in_surface)
        clock = self._context.get_clock()
        while not self._stop(self._context):
            self._context.tick_and_draw()

            if self._collected < self._item_amount:
                # Check and perform move on _player character.
                self._player.inquire_move(self._room.block_manager)

                # Update view to _player sprite position.
                self._view.update(self._player)

                if self._monitor.renderer.draw(self._monitor_surface):
                    # Render collected amount.
                    self._draw_collected(self._monitor_surface)
                    screen.blit(self._monitor_surface, self._monitor_position)

                # Render dirty sprites.
                if self._room.renderer.draw(self._win_surface):
                    screen.blit(self._win_surface, *self._view.get_rect())
            else:
                self._dialog.show()

            # Draw background animation.
            self._bit_blipper.draw(screen)
            clock.tick(60)

            # Update screen
            pygame.display.update(self._window_clip)

        if self._context.get_model()._active == 1:
            self._reset()  # Reset, as this class instance is reused.
            self._fade_out(in_surface, out_surface)
            self._bit_blipper.reset()
            self._room.renderer.draw_all(self._win_surface)
            self._monitor.renderer.draw_all(self._monitor_surface)

    def _fade_in(self, in_surface):
        self._bit_blipper.fade_in(self._context.get_screen(), in_surface,
                                  self._monitor_position)

    def _fade_out(self, current_surface, out_surface):
        self._bit_blipper.fade_out(self._context.get_screen(), current_surface,
                                   out_surface, self._monitor_position)

    def _draw_collected(self, surface):
        text = str(self._collected) + '/' + str(self._item_amount)
        font_renderer = self._collect_font.render(text, 1, self._collect_color)
        y = (2*32 + font_renderer.get_height()) / 2
        y = surface.get_height() - y - 4  # Minus indentation
        x = 5*32 - font_renderer.get_width() - 4  # Minus indentation
        surface.blit(font_renderer, (x, y))

    def _stop(self, context):
        """Validate whether game should stop or continue. Check whether
        player has pressed ESC to abort or quit with mouse. If time is up
        the game is aborted."""
        for e in pygame.event.get():
            if e.type == QUIT:
                screen = context.get_screen()
                screen_backup = utilities.get_screen_backup(screen)
                if utilities.show_quit_dialog(context):
                    context.get_model()._active = 0  # Exit game.
                    return True  # Quit
                else:
                    screen.blit(screen_backup, (0, 0))
                    pygame.display.update()
            elif e.type == KEYDOWN and e.key == K_ESCAPE:
                return True  # Aborted
        # Check whether volume is being changed.
        self._context.inquire_audio_volume_change()
        return self._context.get_time_left() <= 0

    class ScreenDialog():
        """Screen dialog"""
        def __init__(self, context, size, position):
            self.size = size
            self.position = position
            quizz = context.get_quizz()

            self.dialog = pygame.Surface(size)
            self.font = context.get_font('clacon', 21)
            self.screen = pygame.display.get_surface()
            self.dialog_position = position

            max_width = size[0]
            text = quizz.get_random_clue()
            text = utilities.word_wrap_text(text, max_width, self.font)
            self.text_arr = text.split('\n')

            height = len(self.text_arr) * self.font.get_height()
            width = max(self.font.size(line)[0] for line in self.text_arr)
            self.text_surface = pygame.Surface((width, height))
            self.max_up_scroll = min(0, size[1] - height)
            self.y = 0  # Current scroll position

            color = (50, 155, 20)
            utilities.rendered_text(self.text_arr, self.text_surface,
                                    self.font, color)

        def show(self):
            text_rect = self.text_surface.get_rect()

            keys = pygame.key.get_pressed()
            if keys[K_UP]:
                self.y = max(self.max_up_scroll, self.y - 10)
            elif keys[K_DOWN]:
                self.y = min(0, self.y + 10)

            self.dialog.fill((0, 0, 0))
            self.dialog.blit(self.text_surface, text_rect.move((5, self.y)))
            self.screen.blit(self.dialog, self.dialog_position)
