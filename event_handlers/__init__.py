from os import listdir

__all__ = map(lambda x: x[:-3], filter(lambda x: x[-3:] == '.py' and x[0] not in ['#', '.'], listdir('event_handlers')))
