# -*- coding: iso-8859-1 -*

import pygame

import utilities

from pygame.locals import KEYDOWN, QUIT, K_a, K_b, K_c, K_d
from random import shuffle, choice

"""
Contains functionality for displaying and performing a quizz.

Practices:
+ Comply to PEP 0008 for programming with modules, classes, methods and
  functions (Style Guide for Python Codestyle), see:
  https://www.python.org/dev/peps/pep-0008
+ Comply to PEP 0257 (Docstring convention), see:
  https://www.python.org/dev/peps/pep-0257

@author: Peter Borgstedt (peter.borgstedt@gmail.com)
"""


class Quizz():
  """A quizz with questions that the player must answer on.
  They will be displayed randomly."""

  def __init__(self, context):
    self._context = context
    config = context.get_config()
    self._config = config.get_prefixed_properties('quizz')
    self._text_font = context.get_font('clacon', 21)
    self._led_font = context.get_font('digital', 40)
    self._build_quizz()

  def get_random_clue(self):
    """Get a random clue for one of the questions."""
    return choice(self.questions).clue

  def _build_quizz(self):
    """Build quizz context."""
    self.questions = []
    for key in self._config.get_keys():
      self.questions.append(Question(self._config.get(key)))

  def run(self):
    """Run quizz."""
    self.dirty_rectangles = []
    screen = pygame.display.get_surface()
    image = pygame.image.load('tiles/quizz.png')

    background = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    background.blit(screen, (0, 0))
    background.fill((0, 0, 0, 175))
    background.blit(image, (0, 0))
    background = background.convert_alpha()

    screen.blit(background, (0, 0))

    shuffle(self.questions)  # Shuffle questions
    correct_answers = 0
    answers = ''
    for question in self.questions:
      self.draw(screen, background, question, answers)
      next_question = True
      while next_question:
        for e in pygame.event.get():
          if e.type == QUIT:
            if utilities.show_quit_dialog(self._context):
              self._context.get_model()._active = 0
              return False
          elif e.type == KEYDOWN and e.key in (K_a, K_b, K_c, K_d):
            answers += e.unicode.upper()
            if e.unicode.upper() == question.answer.upper():
              correct_answers += 1
            next_question = False
            break
      self.draw(screen, background, question, answers)
    return correct_answers == 4

  def draw(self, screen, background, question, answers):
    """Draw the scenery."""
    x, y = (3*32, 3*32)
    # Word wrap on length of 14 grids (448px)
    q = utilities.word_wrap_text(question.question, 14*32, self._text_font)
    q_sur = self._draw_text(self._text_font, q, (255, 255, 255))
    q_w, q_h = q_sur.get_size()
    c_sur = self._draw_choices(question, self._text_font)
    c_w, c_h = c_sur.get_size()

    for dirty_rectangle in self.dirty_rectangles:
      screen.blit(background, (x, y), dirty_rectangle)
    self.dirty_rectangles = []
    self.dirty_rectangles.append((x, y, max(q_w, c_w), q_h + c_h))

    screen.blit(q_sur, (x, y))
    screen.blit(c_sur, (x, y + q_h))

    self._draw_answers(screen, background, answers)
    pygame.display.update()

  def _draw_choices(self, question, font):
    """Draw choices to choice, these are the letters."""
    text = ''
    for key in sorted(question.choices.keys()):
      text += '<c:(255,0,0)>[' + key + ']</c> '
      text += question.choices[key] + '\n\n'
    # Word wrap on 500px width
    text = utilities.word_wrap_text(text, 14*32, font, indentation=' '*4)
    return self._draw_text(font, text, (128, 128, 128))

  def _draw_text(self, font, text, color):
    """Draw text, support tags."""
    text_arr = text.split("\n")
    height = len(text_arr) * font.get_height()
    width = utilities.get_length_without_tags(text_arr, font)
    text_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    utilities.rendered_text(text_arr, text_surface, font, color)
    return text_surface

  def _draw_answers(self, screen, background, answers):
    """Draw possible answers to choice from."""
    x, y = 22*32, 7*32 + 16
    font_render = self._led_font.render(answers, 1, (10, 80, 100))
    font_rect = (x, y, 32*6, 32)
    screen.blit(background, (x, y), font_rect)
    screen.blit(font_render, (x, y))


class Question():
  """Contain question, answers, a correct answer and a clue."""

  def __init__(self, properties):
    self.question = properties.get('question')
    self.answer = properties.get('answer')
    self.choices = properties.get_eval('choices')
    self.clue = properties.get('clue')
