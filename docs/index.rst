Welcome to Diplomacy package!
=============================

Diplomacy is a strategic board game when you play a country (power) on a map with the goal to conquer at least half to
all the supply centers present on the map. To achieve this goal, you control power units (armies and/or fleets) that
you can use to occupy empty provinces (locations), attack provinces occupied by other powers, or support other units
occupying or attacking a position.

This is a complex game with many rules and corner cases to take into account, and, thus, an interesting subject for
both entertainment (between humans) and studies (e.g. how to create an artificial intelligence good enough to beat
humans). This project aims to provide a complete and working Python implementation of Diplomacy game with following
features:

- A working game engine easy to use to get familiar with game rules, test corner cases, and simulate complete parties.
- An interface to allow the game to be played online, using:

  - a Python server implementation to handle many games
  - a Python client implementation to play remotely using all the power and facilities of Python
  - a web front-end to play remotely using a human user-friendly interface

- Some integration interface to play with other server/client implementations, especially:

  - a DAIDE server to play with DAIDE client bots
  - a webdiplomacy API to play with `webdiplomacy <http://webdiplomacy.net/>`_ server implementation

.. toctree::
   :maxdepth: -1
   :caption: API Documentation

   api/diplomacy.client
   api/diplomacy.communication
   api/diplomacy.daide
   api/diplomacy.engine
   api/diplomacy.integration
   api/diplomacy.utils

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
