# -*- coding: iso-8859-1 -*

import pygame
from ast import literal_eval
import re


"""
A module containing useful utility methods.

Practices:
+ Comply to PEP 0008 for programming with modules, classes, methods and
  functions (Style Guide for Python Codestyle), see:
  https://www.python.org/dev/peps/pep-0008
+ Comply to PEP 0257 (Docstring convention), see:
  https://www.python.org/dev/peps/pep-0257

@author: Peter Borgstedt (peter.borgstedt@gmail.com)
"""


def get_grid_data(target_rect, matrix):
  """Retrieve blocks from grid positions for a rectangle. For the moment the
  rectangle must be a resolution of 32x32.
  Because of this limitation the maximum of 4 (+1 target) blocks/sprites and
  a minimum of 1 (+1 target) can be retrieved.
  TODO: Use width and height if the target_rect if larger than 32x32, fetch
  colliding sprites for the entire rectangle.
  TODO: Something smarter and dynamic than using None checkers.
  """
  data = []
  p_y1, p_y2, p_x1, p_x2 = get_grid_position(target_rect)

  y1 = matrix.get(p_y1, None)
  if y1 is None:
    return  # This is okay, a block may not exist

  append_not_none(data, y1.get(p_x1, None))  # 1x1
  if p_x2 is not None:  # 1x2
    append_not_none(data, y1.get(p_x2, None))

  if p_y2 is not None:
    y2 = matrix.get(p_y2, None)  # 2x1
    if y2 is not None:
      append_not_none(data, y2.get(p_x1, None))
      if p_x2 is not None:  # 2x2
        append_not_none(data, y2.get(p_x2, None))
  return data


def word_wrap_text(text, max_width, font, **kwargs):
  """Simple word wrapper. Filters out any tags in the text, they are not
  included when calculating the line clip.
  TODO: Include bold and italic tags in calculation for accurate wrapping.
  """
  indentation = kwargs.get('indentation', '')
  new_text = ''
  for line in text.split("\n"):
    new_lines = ''
    new_line = ''
    words = line.split(" ")
    for word in words:
      tmp = re.sub('<[^>]*>', '', new_line + word)  # Remove tags
      if font.size(tmp)[0] < max_width:
        new_line += word + ' '
      else:
        new_lines += new_line.rstrip() + '\n'
        new_line = indentation + word + ' '
    new_text += new_lines + new_line.rstrip() + '\n'
  return new_text


def get_length_without_tags(text_arr, font):
  """Strip tags in text_arr and return width."""
  return max(font.size(re.sub('<[^>]*>', '', line))[0] for line in text_arr)


def rendered_text(text_arr, text_surface, font, color):
  """Render text with some simply tags.
  Currently support tags: <b>bold</b>, <c: (r,g,b)>color</c>
  TODO: Add more tags like italic or font size?
  """
  y = 0
  tmp_color = color
  for line in text_arr:
    x = 0
    line_arr = list([_f for _f in re.split('(<[^>]*>)', line) if _f])
    for line_segment in line_arr:
      match = re.match('^<(?P<tag>.+)>$', line_segment)
      if match is not None:
        tag = match.group('tag')
        if tag == '/b':
          font.set_bold(False)
        elif tag == 'b':
          font.set_bold(True)
        elif tag.startswith('/c'):
          tmp_color = color
        elif tag.startswith('c:'):
          tmp_color = literal_eval(tag.split(':')[1])
        continue
      font_renderer = font.render(line_segment, 1, tmp_color)
      text_surface.blit(font_renderer, (x, y))
      x += font.size(line_segment)[0]
    y += font.get_height()


def add_to_set_in_dict(_dict, value, key):
  """Add value to in dictionary, if not set exist one will be created
  and added to dictionary."""
  values = _dict.get(key, None)
  if values is None:
    values = set()
    _dict[key] = values
  values.add(value)


def get_grid_position(target_rect):
  """Get grid positions of a 32x32 rectangle.
  If rectangle position is 48x48 this will collide with:
  y0x0, y1x0, y1x0, y1x1). Position is calculated mathematically and
  retrieved from matrix for increased performance."""
  y1 = int(target_rect.y / 32)
  y2 = int(y1 + 1) if float(target_rect.y) % 32 >= 0 else None
  x1 = int(target_rect.x / 32)
  x2 = int(x1 + 1) if float(target_rect.x) % 32 >= 0 else None
  return (y1, y2, x1, x2)


def get_center_of(larger_surface, smaller_surface):
  """Get center of two surfaces."""
  return get_center_of_size(larger_surface.get_size(),
                            smaller_surface.get_size())


def get_center_of_size(larger_size, smaller_size):
  """Get center of two sizes/areas."""
  a_w, a_h = larger_size
  b_w, b_h = smaller_size
  return ((a_w - b_w) / 2, (a_h - b_h) / 2)


def append_not_none(lst, data):
  """Append to list if value is not None"""
  if data is not None:
    lst.append(data)


def get_screen_backup(screen):
  """Create backup of screen content."""
  backup = pygame.Surface(screen.get_size())
  backup.blit(screen, (0, 0))
  return backup.convert()


def show_quit_dialog(context):
  """Show quit dialog, return either True or False depending on answer.
  The Dialog is interacted through mouse."""
  dialog_size = (9*32, 4*32)
  dialog_text = 'Vill du avsluta spelet?'
  option_dialog = OptionDialog(context, dialog_size, dialog_text,
                               lambda: lambda: _quit(context, True),
                               lambda: False)
  return option_dialog.show()


def _quit(context, return_boolean):
  """Quit function, setting model to not active. Used in show_quit_dialog."""
  context.get_model()._active = 0
  return return_boolean


class TimeCount():
  """Time counter. Will count to a specific delay time and return true if
  current time is obsolete. Can be looped (auto reseted) or run just once.
  TODO: **kwargs instead of loop, and make the loop True as default."""

  def __init__(self, delay, loop):
    self.last = None
    self.delay = delay
    self.loop = loop  # True/False, will auto reset.

  def is_obsolete(self):
    """Return true if time is obselete, otherwize False."""
    now = pygame.time.get_ticks()
    if self.last is None:
      self.last = now
    elif now - self.last > self.delay:
      if self.loop:
        self.last = now
      return True
    return False


class OptionDialog():
  """Display an dialog with Yes and No options.
  Interaction is done with mouse. When mouse is over the button it paints
  it with a selection color, if the mouse move out it paints back to the
  regular color. The button is painted just once when mouse move into to the
  rectangle and once when moved out.
  A click on the button will stimulating an action for either Yes or No.
  TODO: Maybe lifted these classes another module, or a new one.
  TODO: Add possibility to interact with keys."""

  def __init__(self, context, size, text, yes_action, no_action, **kwargs):
    self._screen = context.get_screen()
    self._context = context
    self._size = size  # Dialog size.
    self._border_size = 2  # Dialog border size in pixels.
    self._border_color = (255, 255, 255)  # Dialog border color.
    self._text = text  # Text displayed in the dialog.
    self._font = context.get_font('clacon', 21)  # Font to be used.
    self._yes_action = yes_action  # Function to run upon yes click.
    self._no_action = no_action  # Function to run upon yes click.
    self._build(**kwargs)

  def _build(self, **kwargs):
    """Build dialog out of dialog context."""
    px, py = get_center_of_size(self._screen.get_size(), self._size)
    py = kwargs.get('y', py)

    dw, dh = self._size
    self._outer_rect = pygame.Rect(px, py, dw, dh)
    self._inner_rect = self._outer_rect.copy().inflate(-4, -4)

    b_size = self._border_size
    b_color = self._border_color

    font_surface = self._font.render(self._text, 1, (255, 255, 255))
    fx, _ = get_center_of_size(self._outer_rect.size,
                               font_surface.get_size())
    fx += self._outer_rect.x

    b_yes_rect = pygame.Rect(px + 32, py + 2*32, 3*32, 1*32)
    b_no_rect = b_yes_rect.copy().move(b_yes_rect.width + 32, 0)

    self._screen.fill((64, 64, 64), rect=self._inner_rect)
    pygame.draw.rect(self._screen, b_color, self._outer_rect, b_size)
    self._screen.blit(font_surface, (fx,  self._outer_rect.y + 16))

    self._button_yes = Button(self, b_yes_rect, self._font, 'Ja')
    self._button_no = Button(self, b_no_rect, self._font, 'Nej')

  def show(self):
    """Show the dialog, return True or False depending on action."""
    black_alpha = pygame.Surface(self._screen.get_size(), pygame.SRCALPHA)
    black_alpha.fill((0, 0, 0, 128))
    self._screen.blit(black_alpha, (0, 0))

    self._button_yes.draw(self._screen)
    self._button_no.draw(self._screen)
    pygame.display.update()

    while True:
      for e in pygame.event.get():
        if e.type == pygame.QUIT:
          self._context.get_model()._active = 0
          return False
        if e.type == pygame.KEYDOWN:
          if e.key == pygame.K_ESCAPE:
            return self._no_action()  # Default ESC as no.
        if e.type == pygame.MOUSEMOTION:
          self._button_yes.mouse_motion(self._screen, e.pos)
          self._button_no.mouse_motion(self._screen, e.pos)
        if e.type == pygame.MOUSEBUTTONDOWN:
          if self._button_yes.mouse_click():
            return self._yes_action()
          if self._button_no.mouse_click():
            return self._no_action()


class Button():
  """Button class for the OptionDialog. Keep track if it has is selected
  or not and raw content depending on state."""
  _C_UNSELECTED = (128, 128, 128)
  _C_SELECTED = (255, 0, 0)

  def __init__(self, option_dialog, rectangle, font, text):
    self._option_dialog = option_dialog
    self._outer_rect = rectangle
    self._inner_rect = self._outer_rect.copy().inflate(-4, -4)
    self._font = font
    self._text = text
    self._selected = False

  def mouse_motion(self, screen, m_pos):
    """Inquire mouse motion event."""
    if self._outer_rect.collidepoint(m_pos):
      if not self._selected:
        self._selected = True
        self._draw_opacity(screen)
        pygame.display.update(self._inner_rect)
    elif self._selected:
      self._selected = False
      self._draw_opacity(screen)
      pygame.display.update(self._inner_rect)

  def mouse_click(self):
    """A click as been made, return True if the button is selected,
    else return False."""
    if self._selected:
      return True
    return False

  def draw(self, screen):
    """Draw button fully, border and opacity."""
    self._draw_border(screen)
    self._draw_opacity(screen)

  def _draw_opacity(self, screen):
    """Draw only button opacity, the color is choosen depending on the
    selection state."""
    screen.fill(self._get_color(), rect=self._inner_rect)
    font_surface = self._font.render(self._text, 1, (255, 255, 255))
    fx, fy = get_center_of_size(self._outer_rect.size,
                                font_surface.get_size())
    fx += self._outer_rect.x
    fy += self._outer_rect.y
    screen.blit(font_surface, (fx, fy))

  def _get_color(self):
    return self._C_SELECTED if self._selected else self._C_UNSELECTED

  def _draw_border(self, screen):
    """Draw only button border."""
    b_size = self._option_dialog._border_size
    b_color = self._option_dialog._border_color
    pygame.draw.rect(screen, b_color, self._outer_rect, b_size)
