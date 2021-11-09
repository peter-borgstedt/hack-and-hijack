# -*- coding: iso-8859-1 -*

import pygame

from utilities import TimeCount
from random import randint, uniform

"""
Contains transition and background effects.

Practices:
+ Comply to PEP 0008 for programming with modules, classes, methods and
  functions (Style Guide for Python Codestyle), see:
  https://www.python.org/dev/peps/pep-0008
+ Comply to PEP 0257 (Docstring convention), see:
  https://www.python.org/dev/peps/pep-0257

@author: Peter Borgstedt (peter.borgstedt@gmail.com)
"""

class BitBlipper():
  """Transition effect that draw 0 and 1 on the screen."""

  def __init__(self, context, clip_rect):
    self.clip_rect = clip_rect
    self.font = context.get_font('clacon', 15)
    self.bit_blipps = []
    self.active_bit_blipps = []
    self.count = TimeCount(1000/5, True)  # 5 fps
    self.res = 32
    self._build()

  def reset(self):
    for bit_blipp in self.bit_blipps:
      bit_blipp.fade_count.last = None

  def _build(self):
    """Build bit blipp context."""
    i_x, i_y, i_w, i_h = self.clip_rect
    for y in range(i_y, i_h, self.res):
      for x in range(i_x, i_w, self.res):
        bit_blipp = self._BitBlipp(self._get_sequence(), (x, y))
        self.bit_blipps.append(bit_blipp)
    self.active_bit_blipps = list(self.bit_blipps)

  def _seperate(self, inner_surface, bit_blipps, out_position):
    """Separate inner and outer surface segments."""
    sw, sh = inner_surface.get_size()
    p_x, p_y = out_position
    p_width, p_height = p_x + sw, p_y + sh

    outer = []
    inner = []
    for bit_blipp in bit_blipps:
      x, y = bit_blipp.position
      if x < p_x or x >= p_width or y < p_y or y >= p_height:
        outer.append(bit_blipp)
      else:
        inner.append(bit_blipp)
    return (outer, inner)

  def _get_sequence(self):
    """Generate bit sequence, each bit has a animation sequence of 10
    images."""
    sequence = []
    for _ in range(0, 10):
      s = pygame.Surface((self.res, self.res))
      color = pygame.Color(5, 100, 105, 255)
      color = color.correct_gamma(uniform(0.5, 3.0))
      bit = self.font.render(str(randint(0, 1)), 1, color)
      px = (self.res - bit.get_width())/2
      py = (self.res - bit.get_height())/2
      s.blit(bit, (px, py))
      sequence.append(s)
    return sequence

  def _fade_surface_out(self, screen, done, bit_blipps):
    """Fade out the bit blipp transition effect."""
    tmp = list(bit_blipps)
    length = len(tmp)
    while length > 0:
      # Get events so window events can be forwarded, otherwise it
      # will be locked while fading. We use pygame.event.get() and not
      # pygame.event.push(), we do not care about the events so they
      # will be thrown away.
      pygame.event.get()
      remaining = tmp
      tmp = []
      for blip in remaining:
        if self.count.is_obsolete():
          for blip in done:
            blip.draw(screen)
        if blip.fade_count.is_obsolete():
          length -= 1
          blip.draw(screen)
          done.append(blip)
        else:
          tmp.append(blip)
      pygame.display.update(self.clip_rect)

  def _fade_surface_in(self, screen, out_surface, inner, outer):
    length = len(inner)
    while length > 0:
      # Get events so window events can be forwarded, otherwise it
      # will be locked while fading. We use pygame.event.get() and not
      # pygame.event.push(), we do not care about the events so they
      # will be thrown away.
      pygame.event.get()
      remaining = inner
      if self.count.is_obsolete():
        for bit_blipp in outer:
          bit_blipp.draw(screen)
        for bit_blipp in remaining:
          bit_blipp.draw(screen)

      inner = []
      for bit_blipp in remaining:
        if bit_blipp.fade_count.is_obsolete():
          length -= 1
          out = pygame.Surface((self.res, self.res))
          clip = (bit_blipp.position, (self.res, self.res))
          out.blit(out_surface, (0, 0), clip)
          screen.blit(out, bit_blipp.position)
        else:
          inner.append(bit_blipp)
      pygame.display.update(self.clip_rect)

  def fade_in(self, screen, out_surface, out_position):
    """Fade in the bit blipp transition effect."""
    self._fade_surface_out(screen, [], self.bit_blipps)
    outer, inner = self._seperate(out_surface, self.bit_blipps,
                                  out_position)

    for bit_blipp in inner:
      bit_blipp.fade_count.last = None

    init_surface = pygame.Surface(screen.get_size())
    init_surface.blit(out_surface, out_position)
    self._fade_surface_in(screen, init_surface, inner, outer)
    self.active_bit_blipps = outer

  def fade_out(self, screen, inner_surface, out_surface, out_position):
    """Fade out the bit blipp transition effect."""
    outer, inner = self._seperate(inner_surface, self.bit_blipps,
                                  out_position)
    for bit_blipp in inner:
      bit_blipp.fade_count.last = None
    self._fade_surface_out(screen, outer, inner)

    for bit_blipp in self.bit_blipps:
      bit_blipp.fade_count.last = None
    self._fade_surface_in(screen, out_surface, self.bit_blipps, [])

  def draw(self, surface):
    """Draw bits, for a nice animation effects in the bacground."""
    if self.count.is_obsolete():
      for bit_blipp in self.active_bit_blipps:
        bit_blipp.draw(surface)

  class _BitBlipp():
    """Nested class, containing a bit blipp. However there's not point
    in nesting class in Python. We have not reference to outer class."""

    def __init__(self, sequence, position):
      self.sequence = sequence
      self.index = 0
      self.position = position
      self.fade_count = TimeCount(randint(0, 1500), False)

    def draw(self, surface):
      """Draw individual BitBlipp image from current index and then
      calculate next index."""
      surface.blit(self.sequence[self.index], self.position)
      self.index = (self.index + 1) % 10
