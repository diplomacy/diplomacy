DAIDE clients
=============

This page describes how to build and run DAIDE protocol bots from the
`diplomacy/daide-client <https://github.com/diplomacy/daide-client>`_ project
and how to connect them to a Diplomacy game. It is a short refresh of the
original DAIDE client guide contributed by Satya Ortiz-Gagne in
`PR 101 <https://github.com/diplomacy/diplomacy/pull/101>`_.

.. note::

   The client source was audited at commit
   ``02b36aec6cb5e3a0d2cfcc526f0bdccbf0598d8c`` (``master``). The build and
   protocol notes below were checked against that source, not against a live
   bot run. The client was not executed against this server while preparing
   this page, so treat the protocol section as an implementation map rather
   than a compatibility guarantee. Source links are pinned to the audited
   revision.

Build the clients
-----------------

Requirements: CMake 3.14 or newer and a C++14 compiler.

.. code-block:: bash

   git clone https://github.com/diplomacy/daide-client.git
   cd daide-client
   git checkout 02b36aec6cb5e3a0d2cfcc526f0bdccbf0598d8c
   cmake -S . -B build
   cmake --build build

The build creates ``dumbbot``, ``holdbot`` and ``randbot`` in the client's
``bin/`` directory. The CMake project sets the runtime output directory to
that ``bin/`` directory, so a build overwrites the prebuilt binaries tracked
by the client repository. Do not commit those replaced files.

See `CMakeLists.txt at 02b36aec
<https://github.com/diplomacy/daide-client/blob/02b36aec6cb5e3a0d2cfcc526f0bdccbf0598d8c/CMakeLists.txt>`_
for the build definition.

Run a client
------------

.. code-block:: text

   bin/dumbbot [-sServerName|-iIPAddress] [-pPortNumber] [-lLogLevel] [-rPOW:passcode]

The same flags apply to ``holdbot`` and ``randbot``. Flags are concatenated
with their values, for example ``-p16713`` and ``-rENG:123456``.

``-sServerName``
   The server name to connect to. This cannot be combined with ``-i``.
   Defaults to ``localhost``.

``-iIPAddress``
   The server IP address to connect to. This cannot be combined with ``-s``.

``-pPortNumber``
   The TCP port of the game's DAIDE server. This is not the API port (usually
   8432). The client defaults to port 16713 when ``-p`` is omitted.

``-lLogLevel``
   ``0`` disables logging and ``1`` enables it.

``-rPOW:passcode``
   Attempts to reconnect to a running game as power ``POW``. ``POW`` is a
   three-letter power name such as ``ENG`` and ``passcode`` is the number the
   server sent in the game's ``HLO`` message. There is no space around the
   colon.

The audited client has no ``-cPOW`` option. The original PR 101 guide
documented one, but it is not supported by this client revision, so do not
rely on it to choose a power. With ``-rENG:...``, the client also prefixes
its initial name with ``ENG:``. On a normal join, the server treats that as
a best-effort power preference, falling back to the alphabetically first
available power. Thus ``-r`` does not force reconnection: a successful
``NME`` joins normally. This is not strict power selection.

Getting a game's DAIDE port
---------------------------

The API port, 8432 by default, carries the normal client API. It is not the
port a DAIDE bot connects to. For a running game, ask the server for the
game's separate DAIDE port:

.. code-block:: python

   daide_port = yield connection.get_daide_port(game_id)

:meth:`Connection.get_daide_port
<diplomacy.client.connection.Connection.get_daide_port>` is a Tornado
coroutine. It returns the bot port for a running game. If the game id is
invalid or the game's DAIDE server is not running, the request raises
``DaidePortException``. The server opens the DAIDE listener on a free port in
the 8000 to 8999 range.

Then start the bot against that port:

.. code-block:: bash

   daide_port=8123  # Replace with the port returned above.
   bin/holdbot -p"$daide_port"

Protocol overview
-----------------

The names below are DAIDE message tokens. The bundled client and the server's
DAIDE implementation are the authoritative sources for the exact sequences.

Connection
   The three bundled bots identify themselves with ``NME``. The server
   replies ``YES (NME)`` together with ``MAP``, or ``REJ (NME)``. On an
   initial join, the client requests ``MDF`` after receiving ``MAP`` and
   sends ``YES (MAP)`` after processing the definition. When the game
   starts, the server sends ``HLO`` with the power, passcode and variant.
   The base client implementation sends ``OBS`` instead; this server
   rejects observer requests.

Reconnect
   After ``REJ (NME)``, a bot started with ``-r`` sends ``IAM`` with the
   power and the passcode from ``HLO``; without reconnect details it stops.
   The server accepts only a matching passcode belonging to a DAIDE user
   that currently controls the requested power. It replies ``YES (IAM)``
   or ``REJ (IAM)``. At the audited revision, ``REJ (IAM)`` logs an error;
   it does not stop the client or automatically retry.

Phase
   A phase starts with ``SCO``, ``NOW`` and ``TME``. ``SUB`` returns one
   ``THX`` per order plus ``MIS``. ``MIS`` returns ``MIS``. ``GOF`` returns
   ``YES (GOF)`` and ``NOT (GOF)`` returns ``YES (NOT (GOF))``. ``HST``
   returns ``ORD``, ``SCO`` and ``NOW``, or ``REJ (HST)``. The phase ends with
   an ``ORD`` notification.

Press
   ``SND`` returns ``YES (SND)`` or ``REJ (SND)``. The recipient receives the
   press message in ``FRM``.

Closure
   A completed game ends with ``DRW`` for a draw or ``SLO`` for a solo, then
   ``SMR`` and ``OFF``. A cancelled game ends with ``OFF``.

Source references
-----------------

- `daide-client at 02b36aec
  <https://github.com/diplomacy/daide-client/tree/02b36aec6cb5e3a0d2cfcc526f0bdccbf0598d8c>`_
- `base_bot.cpp at 02b36aec
  <https://github.com/diplomacy/daide-client/blob/02b36aec6cb5e3a0d2cfcc526f0bdccbf0598d8c/daide_client/base_bot.cpp>`_
- `Original DAIDE client documentation, PR 101
  <https://github.com/diplomacy/diplomacy/pull/101>`_ by Satya Ortiz-Gagne
