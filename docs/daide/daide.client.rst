DAIDE Client
============

The project `DAIDE Client <https://github.com/diplomacy/daide-client>`_ provides implementation of bots compatible
with the DAIDE protocol in a unix-like environment. Provided bots are *dumbbot*, *holdbot*, *randbot*.

Compile the Clients
-------------------

.. code-block:: bash

    $ cmake --build .

Execute a Client
----------------

.. code-block:: bash

    $ dumbbot|holdbot|randbot [-sServerName|-iIPAddress] [-pPortNumber] [-lLogLevel] [-cPOW] [-rPOW:passcode]

-s<ServerName>
      The server name to connect to (incompatible with ``-iIPAddress``).
-i<IPAddress>
      The ip address of the server to connect to (incompatible with ``-sServerName``).
-p<PortNumber>
      The game port number.

      When used with the Diplomacy Engine, the API entry :meth:`Connection.get_daide_port
      <diplomacy.client.connection.Connection.get_daide_port>` will provide the port number
      to use for a game id
-l<LogLevel>
      Either ``0`` or ``1`` to disable of enable logs respectively.
-c<POW>
      The short name of the power to use when joining the game.

      Accepted values are: ``AUS``, ``ENG``, ``FRA``, ``GER``, ``ITA``, ``RUS``, ``TUR``
-r<POW:passcode>
      The short name of the power with passcode to rejoin a disconnected game.

      | Accepted values for ``POW`` are: ``AUS``, ``ENG``, ``FRA``, ``GER``, ``ITA``, ``RUS``, ``TUR``
      | The passcode is provided by the server upon joining a game

Communications Protocols
------------------------

Connection Protocol
^^^^^^^^^^^^^^^^^^^

==============================================================  ==============================================================
Client Request / *Event*                                        Server Responses / Server Notifications
==============================================================  ==============================================================
:class:`NME request<diplomacy.daide.requests.NME>`              | :class:`YES (NME) response<diplomacy.daide.responses.YES>`
                                                                  , :class:`MAP response<diplomacy.daide.responses.MAP>`
                                                                | or
                                                                | :class:`REJ (NME) response<diplomacy.daide.responses.REJ>`
--------------------------------------------------------------  --------------------------------------------------------------
:class:`MDF request<diplomacy.daide.requests.MDF>`              :class:`MDF response<diplomacy.daide.responses.MDF>`
--------------------------------------------------------------  --------------------------------------------------------------
:class:`YES (MAP) request<diplomacy.daide.requests.YES>`
--------------------------------------------------------------  --------------------------------------------------------------
:class:`REJ (MAP) request<diplomacy.daide.requests.REJ>`
--------------------------------------------------------------  --------------------------------------------------------------
*Game starts*                                                   :class:`HLO notification<diplomacy.daide.notifications.HLO>`
==============================================================  ==============================================================

Once connected to the DAIDE server, the client will send :class:`NME request<diplomacy.daide.requests.NME>` to
identify itself and join the game. The server will reply with :class:`YES (NME) response<diplomacy.daide.responses.YES>`
or :class:`REJ (NME) response<diplomacy.daide.responses.REJ>` respectively for an accepted or rejected request.

If the request is accepted, the server will add a :class:`MAP response<diplomacy.daide.responses.MAP>` to its reply
identifying the map that will be used. The client will then send :class:`YES (MAP) request<diplomacy.daide.requests.YES>`
to accept and join the game or :class:`MDF request<diplomacy.daide.requests.MDF>` in the case the client doesn't
know the map.

The server will reply to :class:`MDF request<diplomacy.daide.requests.MDF>` with :class:`MDF response
<diplomacy.daide.responses.MDF>`. The client will send :class:`YES (MAP) request<diplomacy.daide.requests.YES>`
to accept the map definition and join the game or :class:`REJ (MAP) request<diplomacy.daide.requests.REJ>`
otherwise.

Once the game starts, the server will send a :class:`HLO notification<diplomacy.daide.notifications.HLO>` to notify
the start of the game to the client.

Phase Protocol
^^^^^^^^^^^^^^

==============================================================  ==============================================================
Client Request / *Event*                                        Server Responses / Server Notifications
==============================================================  ==============================================================
*Phase starts*                                                  :class:`SCO notification<diplomacy.daide.notifications.SCO>`
                                                                , :class:`NOW notification<diplomacy.daide.notifications.NOW>`
                                                                , :class:`TME notification<diplomacy.daide.notifications.TME>`
--------------------------------------------------------------  --------------------------------------------------------------
:class:`SUB request<diplomacy.daide.requests.SUB>`              series of :class:`THX response<diplomacy.daide.responses.THX>`
                                                                , :class:`MIS response <diplomacy.daide.responses.MIS>`
--------------------------------------------------------------  --------------------------------------------------------------
:class:`MIS request<diplomacy.daide.requests.MIS>`              :class:`MIS response<diplomacy.daide.responses.MIS>`
--------------------------------------------------------------  --------------------------------------------------------------
:class:`NOT(GOF) request<diplomacy.daide.requests.NOT>`         :class:`YES(NOT(GOF)) response<diplomacy.daide.responses.YES>`
--------------------------------------------------------------  --------------------------------------------------------------
:class:`GOF request<diplomacy.daide.requests.GOF>`              :class:`YES(GOF) response<diplomacy.daide.responses.YES>`
--------------------------------------------------------------  --------------------------------------------------------------
:class:`HST request<diplomacy.daide.requests.HST>`              | :class:`ORD response<diplomacy.daide.responses.ORD>`
                                                                  , :class:`SCO response<diplomacy.daide.responses.SCO>`
                                                                  , :class:`NOW response<diplomacy.daide.responses.NOW>`
                                                                | or
                                                                | :class:`REJ(HST) response<diplomacy.daide.responses.REJ>`
--------------------------------------------------------------  --------------------------------------------------------------
*Phase ends*                                                    :class:`ORD notification<diplomacy.daide.notifications.ORD>`
==============================================================  ==============================================================

At the beginning of a phase, the server sends a :class:`SCO notification<diplomacy.daide.notifications.SCO>`
followed by :class:`NOW notification<diplomacy.daide.notifications.NOW>` and a :class:`TME notification
<diplomacy.daide.notifications.TME>` to the client. During the game, the server will accept :class:`SUB request
<diplomacy.daide.requests.SUB>`, :class:`MIS request<diplomacy.daide.requests.MIS>`, :class:`NOT(GOF) request
<diplomacy.daide.requests.NOT>`, :class:`GOF request<diplomacy.daide.requests.GOF>` and :class:`HST request
<diplomacy.daide.requests.HST>`.

The server will reply to :class:`SUB request<diplomacy.daide.requests.SUB>` with a series of :class:`THX response
<diplomacy.daide.responses.THX>`, one for each order submitted, and :class:`MIS response <diplomacy.daide.responses.MIS>`.

The server will reply to :class:`MIS request<diplomacy.daide.requests.MIS>` with :class:`MIS response
<diplomacy.daide.responses.MIS>`.

The server will reply to :class:`NOT(GOF) request<diplomacy.daide.requests.NOT>` and :class:`GOF request
<diplomacy.daide.requests.GOF>` with :class:`YES(NOT(GOF)) response<diplomacy.daide.responses.YES>` and
:class:`YES(GOF) response <diplomacy.daide.responses.YES>` respectively.

The server will reply to :class:`HST request<diplomacy.daide.requests.HST>` with :class:`ORD response
<diplomacy.daide.responses.ORD>` followed by :class:`SCO response<diplomacy.daide.responses.SCO>` and
:class:`NOW response<diplomacy.daide.responses.NOW>` if the request is valid or :class:`REJ(HST) response
<diplomacy.daide.responses.REJ>` otherwise.

At the end of a phase, the server sends :class:`ORD notification<diplomacy.daide.notifications.ORD>`.

Press Message Protocol
^^^^^^^^^^^^^^^^^^^^^^

==============================================================  ==============================================================
Client Request / *Event*                                        Server Responses / Server Notifications
==============================================================  ==============================================================
:class:`SND request<diplomacy.daide.requests.SND>`              | :class:`YES (SND) response<diplomacy.daide.responses.YES>`
                                                                | or
                                                                | :class:`REJ (SND) response<diplomacy.daide.responses.REJ>`
--------------------------------------------------------------  --------------------------------------------------------------
*Press message received*                                        :class:`FRM notification<diplomacy.daide.notifications.FRM>`
==============================================================  ==============================================================

Once the game started, the server will start accepting :class:`SND request<diplomacy.daide.requests.SND>`. The
server will reply with :class:`YES (SND) response<diplomacy.daide.responses.YES>` or :class:`REJ (SND)
response<diplomacy.daide.responses.REJ>`. Then the server will send :class:`FRM notification<diplomacy.daide.notifications.FRM>`
to the specified client.

Closure Protocol
^^^^^^^^^^^^^^^^

==============================================================  ==============================================================
Client Request / *Event*                                        Server Responses / Server Notifications
==============================================================  ==============================================================
:class:`SND request<diplomacy.daide.requests.SND>`              | :class:`YES (SND) response<diplomacy.daide.responses.YES>`
                                                                | or
                                                                | :class:`REJ (SND) response<diplomacy.daide.responses.REJ>`
--------------------------------------------------------------  --------------------------------------------------------------
*Game completes*                                                | :class:`DRW notification<diplomacy.daide.notifications.DRW>`
                                                                  ,
                                                                  :class:`SMR notification<diplomacy.daide.notifications.SMR>`
                                                                  ,
                                                                  :class:`OFF notification<diplomacy.daide.notifications.OFF>`
                                                                | or
                                                                | :class:`SLO notification<diplomacy.daide.notifications.SLO>`
                                                                  ,
                                                                  :class:`SMR notification<diplomacy.daide.notifications.SMR>`
                                                                  ,
                                                                  :class:`OFF notification<diplomacy.daide.notifications.OFF>`
--------------------------------------------------------------  --------------------------------------------------------------
*Game is cancelled*                                             :class:`OFF notification<diplomacy.daide.notifications.OFF>`
==============================================================  ==============================================================

If the game is completed, the server will send :class:`DRW notification<diplomacy.daide.notifications.DRW>` if the
game ended with a draw or :class:`SLO notification<diplomacy.daide.notifications.SLO>` if the game ended with a
single player remaining. The server will then send :class:`SMR notification<diplomacy.daide.notifications.SMR>`
followed by :class:`OFF notification<diplomacy.daide.notifications.OFF>`.

If the game gets cancelled, the server will send :class:`OFF notification<diplomacy.daide.notifications.OFF>`.
