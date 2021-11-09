# -*- coding: iso-8859-1 -*

import pygame
from pygame.locals import SRCALPHA
from utilities import TimeCount

global DEBUG
DEBUG = False

__all__ = ['Debug']

"""
Containing some useful debugging funnctionality.

Practices:
+ Comply to PEP 0008 for programming with modules, classes, methods and
  functions (Style Guide for Python Codestyle), see:
  https://www.python.org/dev/peps/pep-0008
+ Comply to PEP 0257 (Docstring convention), see:
  https://www.python.org/dev/peps/pep-0257

@author: Peter Borgstedt (peter.borgstedt@gmail.com)
"""


class Debug():
  """Class contain some useful debugging methods.
  Note that the global value DEBUG is used in several places in the code
  showing debug information real time in console."""

  def __init__(self):
    self.fps = {}
    self.font = pygame.font.SysFont("MONOSPACE", 20, bold=True)

  def draw_grid(self, size):
    """Draw grid on given area/size."""
    w, h = size
    x_max, y_max = w / 32, h / 32
    grid = pygame.Surface(size, SRCALPHA)

    for y in range(1, y_max):
      point_list = [(0, y*32), (w, y*32)]
      pygame.draw.lines(grid, (255, 0, 0), False, point_list, 1)

    for x in range(1, x_max):
      point_list = [(x*32, 0), (x*32, h)]
      pygame.draw.lines(grid, (255, 0, 0), False, point_list, 1)
    return grid

  def render_fps(self, ident, surface, position):
    """Render FPS either on screen or in console. Only useful if
    clock is turned of, with combination of utilities.TimeCount with delay
    FPS/1000 on selected places in code give more accurate FPS when run
    in that certain FPS rate (pygame.time.Clock)."""

    data = self.fps.get(ident, None)
    if data is None:
      self.fps[ident] = data = [0, 0, TimeCount(1000, True)]

    time_str = 'FPS: %s' % data[0]
    if surface is None:
      print time_str
    else:
      font_renderer = self.font.render(time_str, 1, (255, 255, 255))
      font_renderer.fill((0, 0, 0))
      if position is None:
        _, _, fw, fh = font_renderer.get_rect()
        w, h = surface.get_size()
        position = (w-fw, h-fh)
      surface.blit(font_renderer, position)

    data[1] += 1
    if (data[2].is_obsolete()):
      data[0] = data[1]
      data[1] = 0
