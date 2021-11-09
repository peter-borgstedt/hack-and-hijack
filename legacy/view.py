# -*- coding: iso-8859-1 -*

import pygame

__all__ = ['View']

"""
Contains a view that is used to render a larger surface on smaller one,
it will calculate an area depending on a position and several other factors.

Simply put, it works like a JScrollPane in Java, but this only contain the
functionality surrounding the rectangle/area.

Firstly I used a tampered version of the http://stackoverflow.com/a/14357169,
but in the end i rewrote the whole thing and now it works differently.
But it was a base of learning.

Practices:
+ Comply to PEP 0008 for programming with modules, classes, methods and
  functions (Style Guide for Python Codestyle), see:
  https://www.python.org/dev/peps/pep-0008
+ Comply to PEP 0257 (Docstring convention), see:
  https://www.python.org/dev/peps/pep-0257

@author: Peter Borgstedt (peter.borgstedt@gmail.com)
"""


class View():
  """The view is used when rendering a small portion of a large surface
  into another surface (or directly on the screen). Possibility to
  scroll up, down, left, right and stop on edges. If surface is smaller
  than the applying surface then it is being centered."""

  def __init__(self, window_size, view_size, **kwargs):
    l, t, r, b, = kwargs['offset'] if 'offset' in kwargs else (0, 0, 0, 0)
    self._pos = l, t
    self._view_size = view_size
    w, h = window_size
    self._window_clip = pygame.Rect(l, t, w + r, h + b)
    self._window_rect = pygame.Rect((0, 0), (w + r, h + b))
    self._window_size = (w + r, h + b)
    self._window_half_size = tuple([int(s/2) for s in self._window_size])
    self._h_width_diff = int(view_size[0]/2) - self._window_half_size[0]
    self._h_height_diff = int(view_size[1]/2) - self._window_half_size[1]
    self._width_diff = view_size[0] - self._window_size[0]
    self._height_diff = view_size[1] - self._window_size[1]

  def get_rect(self):
    """Get rectangle view, this used when we retrieve parts from the
    larger surface and render it to on the screen."""
    return self._apply(self._window_rect)

  def get_clip(self):
    """Get clip rectangle, this is when only a portion of the screen
    should be updated."""
    return self._window_clip

  def update(self, target):
    """Update with target position and calculate a new a view rectangle."""
    if isinstance(target, pygame.Rect):
      rect = target
    else:
      rect = target.get_rect()
    self._rect = self._calculate_view(rect)

  def _apply(self, target):
    """Apply view rectangle upon target rectangle."""
    if isinstance(target, pygame.Rect):
      rect = target
    else:
      rect = target._rect
    return self._pos, rect.move(self._rect.topleft)

  def _calculate_view(self, target_rect):
    """Calculate the view rectangle."""
    left, top, _, _ = target_rect
    left = (left + self._window_half_size[0]) - self._window_size[0]
    top = (top + self._window_half_size[1]) - self._window_size[1]

    v_width, v_height = self._view_size
    w_width, w_height = self._window_size

    if v_width < w_width:
      left = max(self._h_width_diff, min(self._h_width_diff, left))
    else:
      left = min(self._width_diff, max(0, left))

    if v_height < w_height:
      top = max(self._h_height_diff, min(self._h_height_diff, top))
    else:
      top = min(self._height_diff, max(0, top))
    return pygame.Rect(left, top, w_width, w_height)
