Diplomacy server
================

Game object :class:`.Game` can be to simulate a game and get familiar with game rules and implementation, but it is
not really suited to play in real-world, e.g. against other human players. To achieve this goal, the Diplomacy
project provides a full client/server interface that allows to deploy a server game, and then use remote clients to
connect to server, create and join games, and play against other players, each player controlling a specific power,
while letting server handle the whole gaming policies such as registrations, automated games processing and
notifications.

The Diplomacy server game is a websockets server with a JSON protocol.
The provided clients (Python client and web front-end) come with API and interface suited enough to let you play
without having to deal directly with protocol. Though, if you need more control, you can check :doc:`developer
page about communication protocol used in this project <../developer/communication>`.

Server can be launched using module :mod:`diplomacy.server.run` and will run on default port ``8432``.

.. code-block:: bash

    python -m diplomacy.server.run

You can specify running port with parameter ``--port``.

.. code-block:: bash

    python -m diplomacy.server.run --port 12345

Server can be stopped with ``Ctrl+C``.
