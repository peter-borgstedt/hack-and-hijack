# -*- coding: iso-8859-1 -*

'''
Configuration reader and configuration containers.

Summary (conclusion and details): see more in lab_3_assignment module
- Read lines from a configuration file and structure them into a dictionary.
- Dirty text will be filtered out, which give the possibility to add comments.
- Empty section is also included in the dictionary, with the key: None
- Configuration content must comply to following Pattern:
[section]
key=value
key=<<
value
>>

Some possible TODO's:
- Possibility to define macros.
Fictional examples:

[define my_macro_1()]
var1=hello
var2=world

[define my_macro_2(var1, var2)]
var1={var1}
var2={var2}

[my_section
[use my_macro_1]
[use my_macro_2(var1, var2]

- Possibility to define constants and fetch constants from sections.
Fictional examples:

const_a=A constant

[]
const_b=Another constant

[section_a]
const_c=A third constant
const_d=A fourth constant

[section_b]
var1=[None:MY_CONSTANT]
var2=[:const_b]
var2=[section_a:const_c]
var3=[section_a:const_d]

@author: Peter Borgstedt (peter.borgstedt@gmail.com)
'''

import re
from ast import literal_eval

__all__ = ['ConfigReader']


class Properties():
  def __init__(self, properties):
    self._properties = properties

  def get(self, key, **kwargs):
    value = self._properties.get(key, None)
    return kwargs.get('default', None) if value is None else value

  def get_keys(self):
    return list(self._properties.keys())

  def get_prefixed(self, prefix, split):
    prefixed = {}
    for key in list(self._properties.keys()):
      if not key.startswith(prefix):
        continue
      stripped_key = key.lstrip(prefix + split)
      if stripped_key is not None:
        arr = stripped_key.rsplit(split)
        arr_size = max(len(arr) - 1, 0)
        if arr_size > 0:
          sub_values = self.put_if_absent(prefixed, arr[0], {})
          for i in range(1, arr_size):
            sub_values = self.put_if_absent(sub_values, arr[i], {})
          sub_values[arr[arr_size]] = self._properties[key]
        else:
          prefixed[arr[arr_size]] = self._properties[key]
    return prefixed

  def put_if_absent(self, dictionary, key, value):
    if not dictionary.get(key, None):
      dictionary[key] = value
    return value

  def get_eval(self, key, **kwargs):
    value = self.get(key)
    if value is None:
      return kwargs.get('default', None)
    else:
      return literal_eval(value)


class Config():
  def __init__(self, config):
    self._config = {}
    for key in list(config.keys()):
      value = Properties(config[key])
      self._config[key] = value

  def get_prefixed_properties(self, prefix):
    prefixed_properties = {}
    for key in list(self._config.keys()):
      if key is not None:
        arr = key.rsplit('*', 1)
        if len(arr) > 1 and arr[0] == prefix:
          prefixed_properties[arr[1]] = self.get_properties(key)
    return Properties(prefixed_properties)

  def get_properties(self, section):
    return self._config.get(section, None)

  def get_property(self, section, key):
    properties = self.get_properties(section)
    if properties is not None:
      return properties.get(key)
    # Is this necessary? Will probably set variable to None anyway.
    return None

  def get_eval_property(self, section, key):
    value = self.get_property(section, key)
    if value is not None:
      return literal_eval(value)
    return None


class ConfigReader():

  class LineReader():

    def __init__(self, f):
      self.f = f

    def read_next(self):
      line = next(self.f, None)
      line = self.remove_comment(line)
      self.current = None if line is None else line.rstrip('\r\n')
      return self.current

    def get_current(self):
      return self.current

    def unprocessed(self):
      return self.current is not None

    @staticmethod
    def remove_comment(line):
      if line is not None:
        try:
          idx = line.index('\#')
          if (idx > 0):
            line = line[:idx] + line[idx + 1:]
          else:
            line = line[:line.index('#')]
        except ValueError:
          # TODO: Ugly? Maybe check if index is > 0 instead?
          pass  # Do nothing for now, no comment found.
      return line

  class ConfigAssembler():

    def __init__(self, f):
      self.line_reader = ConfigReader.LineReader(f)
      self.macros = {}

    def read(self):
      content = dict()
      content[None] = self.get_section()
      while self.line_reader.unprocessed():
        line = self.line_reader.get_current()
        match = re.match(
            '^\[define (?P<macro>.+)\((?P<variables>.+)?\)\]$',
            line, re.IGNORECASE)
        if match:
          self.get_macro(match, line)
        else:
          match = re.match("^\[(?P<section>.*)\].*$", line,
                           re.DOTALL)
          if (match):
            content[match.group('section')] = self.get_section()
      return content

    def get_section(self):
      section = {}
      while True:
        line = self.read_next_line()
        if line is None:
          break
        elif isinstance(line, dict):
          section[line['key']] = line['value']
        elif re.match("^\[(?P<section>.*)\].*$", line, re.DOTALL):
          break
      return section

    def get_macro(self, result, _line):
      """Unfinished.
      TODO: Complete this. I'll leave it here as I want to use the
      configuration for other projects."""
      values = {}
      _variables = [var.strip() for var in
                    result.group('variables').split(',')]
      # print variables
      self.macros.update({result.group('macro'): values})
      while True:
        pair = self.next_line_value(True)
        if isinstance(pair, list):
          values.update({pair[0]: pair[1]})
        elif pair is None or pair.startswith('['):
          break
      # print self.macros

    def use_macro(self, line):
      """Unfinished.
      TODO: Complete this. I'll leave it here as I want to use the
      configuration for other projects."""
      result = re.match(
          '^\[app_(?P<app>.+)_(dpfieldmap|offline)_(?P<cust>.+$)', line,
          re.IGNORECASE)
      if result:
        values = {}
        while True:
          pair = self.next_line_value(True)
          print(pair)
          match = re.match(
              '^\[use (?P<macro>.+)(.*)$', line, re.IGNORECASE)
          if (match):
            # print result.group('app')
            continue

          if pair == -1:
            break
          elif pair == -2:
            continue
          else:
            values.update({pair[0]: pair[1]})

    def read_next_line(self):
      line = self.next_line_value(True)
      if isinstance(line, list):
        key = line[0]
        value = line[1]
        if value.startswith('<<'):
          value = value[2:]
          while not value.endswith('>>'):
            n = self.line_reader.read_next()
            value += '\n' + n if len(value) > 2 else n
          value = value.rstrip('\r\n')
          idx = value.rindex('>>')
          if idx > -1:
            value = value[:idx]
        return {'key': key, 'value': value}
      return line

    def next_line_value(self, split):
      line = self.line_reader.read_next()
      if line is not None:
        if split:
          pair = line.split("=", 1)
          if (len(pair) == 2):
            return pair
      return line

  @staticmethod
  def read_config(config_file):
    f = open(config_file, 'r')
    config_assembler = ConfigReader.ConfigAssembler(f)
    return Config(config_assembler.read())
