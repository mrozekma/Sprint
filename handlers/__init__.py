from os import listdir

__all__ = map(lambda x: x[:-3], filter(lambda x: x[-3:] == '.py' and x != '__init__.pyc' and x[0] != '#' and x[0] != '.', listdir('handlers')))
