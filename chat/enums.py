
from enum import IntEnum

class SpeakerTypes(IntEnum):
  HUMAN = 1
  BOT = 2
  SYSTEM = 3

  @classmethod
  def choices(cls):
    return [(key.value, key.name) for key in cls]