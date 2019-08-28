Python client
=============

Diplomacy project provides a Python client implementation to communicate with a deployed Diplomacy server game.

Client is implemented with 1 function and 3 classes:

- the connection function (:func:`diplomacy.client.connection.connect`)
- the connection class (:class:`.Connection`)
- the channel class (:class:`.Channel`)
- the network game class (:class:`.NetworkGame`)

They are intended to be used in following steps:

- Connect to a server using the function :func:`diplomacy.client.connection.connect` which
  returns a :class:`.Connection` object.
- Log in to server using the :meth:`.Connection.authenticate` of the connection object, which returns a
  :class:`.Channel` object.
- Use channel object to manage your account, get info about server games, and join games. Channel especially provides
  method :meth:`.Channel.join_game` to join a game, which returns a :class:`.NetworkGame` object.
- Ultimately, use the network game object to play remotely with the game you joined.

All client methods that communicate with server (we will name them "remote methods") are asynchronous methods.
To use them synchronously, you must call these methods using keyword ``await``
in some upper-level asynchronous methods (defined with keyword ``async``).

Then, the general model of a script using the client will look like this:

.. code-block:: python

    # asyncio will be used to run asynchronous main function synchronously.
    import asyncio

    # This is the asynchronous main function, defined with keyword ``async``.
    async def main():
        # Asynchronous code goes here, ie.
        # - call to connect function
        # - call to Connection methods
        # - call to Channel methods
        # - call to NetworkGame methods
        pass

    # Then we can run asynchronous main function with asyncio.
    asyncio.run(main())


Each remote method in Connection, Channel and NetworkGame classes sends a specific request, then waits for either a server
valid response, or a server error response (if server was unable to handle the request). If server replies with
a valid response, then further handling may be applied and the method call will finally return something (or None if
nothing was expected from server):

.. code-block:: python

    # Pseudo-code (in main() function)
    returned_value = await client.method()

Otherwise, method call will raise the received server error. Possible server errors are classes derived from class
:class:`.ResponseException`, and the class itself for generic untyped errors. You can check the list of all classes
derived from :class:`.ResponseException` in module :mod:`diplomacy.utils.exceptions`. You can add a ``try-catch`` block
around an asynchronous client method call if you want more controls on server errors.

Example:

.. code-block:: python

    # Required import.
    from diplomacy.utils import exceptions
    # Pseudo-code (int main() function).
    try:
        returned_value = await client.method()
    except exceptions.UserException as specificUserException:
        # ...
    except exceptions.ResponseException as anyOtherServerError:
        # ...

Below we will describe the main remote methods needed to use the Python client. You can check client documentation
to get all available remote methods, and then check request documentation to get all information about
request parameters, data replied by server, and value returned by the remote method.

Remote methods documentation is dispatched in related classes
:class:`.Connection`, :class:`.Channel` and :class:`.NetworkGame`.

Requests documentation is in module :mod:`diplomacy.communication.requests`.

Connect to a server
-------------------

First step is to connect to a server, using asynchronous function :func:`diplomacy.client.connection.connect`
which requires server host name and port as parameters. Function will return a :class:`.Connection` object.

.. code-block:: python

    import asyncio
    from diplomacy.client.connection import connect
    async def main():
        connection = await connect(hostname='localhost', port=8432)
    asyncio.run(main())

Authenticate
------------

Using Connection object, you can authenticate to server with asynchronous method :meth:`.Connection.authenticate`
which takes 3 parameters:

- ``username``
- ``password``
- ``create_user`` (boolean, default ``False``). If ``True``, server will try to create a new user with given credentials
  instead of checking for a login. User will be created only if given user name is not already used. If
  ``False``, server will check for login and will send an exception if username and/or password is invalid.

Method will return a :class:`.Channel` object.

.. code-block:: python

    import asyncio
    from diplomacy.client.connection import connect
    async def main():
        connection = await connect('localhost', 8432)
        channel = await connection.authenticate('new_user', 'new_password', create_user=True)
    asyncio.run(main())

Channel class
-------------

Using Channel object, you can search server games, join a server game, or even create a nwe game.

Find games
++++++++++

You can search games with channel method :meth:`.Channel.list_games` which sends a :class:`.ListGames` request accepting
following optional parametrers:

- ``game_id``: a string to search games whose game ID either contains given string or is included in given string
  (by default, game identifiers are not checked).
- ``status``: a string to search games which have given status. See :const:`diplomacy.utils.strings.ALL_GAME_STATUSES`
  for available statuses. You may be interested to look for games with ``'active'`` status. By default, game
  statuses are not checked.
- ``map_name``: a string to search games which have given map name. By default, game maps are not checked.
- ``include_protected``: a boolean to search games which have a registration password (default ``True``).
- ``for_omniscience``: a boolean to search games where you can be an omniscient observer (default ``False``).
  Game roles are explained below in :ref:`join <join_game>` section.

Method will look for games by combining given parameters (it's an ``AND`` condition). It will return a list
of :class:`ComplexDataGameInfo`, each containing information about a game matching given criteria. Example:

.. code-block:: python

    import asyncio
    from diplomacy.client.connection import connect
    async def main():
        connection = await connect('localhost', 8432)
        channel = await connection.authenticate('new_user', 'new_password', create_user=True)
        games_found = await channel.list_games(status='completed')
        print('Found', len(games_found), 'completed game(s).')
        for game_info in games_found:
            print(game_info.game_id)
    asyncio.run(main())

Find playable powers
++++++++++++++++++++

Not all powers for a server game are necessarly available to be played at a moment. For example, powers that are
already managed by other players are not available anymore for new potential players.

You can get the list of playable powers with channel method :meth:`.Channel.get_playable_powers`,
which sends a :class:`.GetPlayablePowers` request requiring only 1 parameter: the game ID of game to check. Method
will return the list of available playable power names.

Example:

.. code-block:: python

    import asyncio
    from diplomacy.client.connection import connect
    async def main():
        connection = await connect('localhost', 8432)
        channel = await connection.authenticate('new_user', 'new_password', create_user=True)
        games_found = await channel.list_games(status='active')
        if not games_found:
            print('No active game found.')
            return
        a_game_id = games_found[0].game_id
        playable_powers = await channel.get_playable_powers(game_id=a_game_id)
        print('Found', len(playable_powers), 'playable power(s) in game', a_game_id)
        for power_name in playable_powers:
            print(power_name)
    asyncio.run(main())

Game roles and user privileges
++++++++++++++++++++++++++++++

Once you choose a game to join, you need to select which power you want to control. This will set you
as a player controlling given power in this game, but it is also possible to join a game without controlling any
power. In such case, you will be an observer, able to see what is happening in the game. Depending on privileges you
have in the game or in the server, you will be allowed to see either all the data carried by the game, or only a subset
of public data. In first case, you will be an omniscient, in second case, you will be a (simple) observer.

Thus, each user joining a game will be assigned a game role:

- **player role**, if user plays a power.
- **observer role**, if user see public game data.
- **omniscient role**, if user see all game data.

If (and only if) a user joins the game as an omniscient, he may then be allowed to act like a game master, depending
here too on user privileges set on server and in game. The game master can not only see all game data, but also send
requests that require game master privileges (e.g. the request to delete a game).

There are 3 privileges available for a user:

- **administrator**: *(server level)* user is a server administrator, and then has all rights.
  He can send all available requests for channels and for all games, and see everything in any game.
- **moderator**: *(game level)* user is a game master, and then has all rights in this specific game. He can sell
  all game requests and see everything in this game.
- **omniscient**: *(game level)* user is an omniscient for this specific game. He can see everything in this game.

Server maintains the list of administrator user names. If a user name is in this list, then user is at least
an administrator, which is the highest privileges level on the server. Only current administrators can edit this list,
using request :class:`.SetGrade`. By default, the Diplomacy server will be created with one user ``admin``
with password ``password`` and automatically added to administrators list.

Each server game maintains the list of game moderators and the list of game omniscient users. If a user name is in
moderators list, then user is at least a moderator of this game. If a user name is in omniscient list, then user is
at least an omniscient observer of this game. Only game moderators can edit these lists, using request
:class:`.SetGrade`. By default, the user who created the game is automatically added to the moderators list.

Then, server assigns a game role with following procedure:

- If user specifies a power when joining a game, server will try to set him as a player controlling given power. If it's
  not possible, server will send an error.
- If user **does not** specify a power, then server will try to set him as an observer with the highest observation
  privileges possible, ie. with either an observer role (the lowest observation privilege) or an omniscient role
  (the highest observation privilege), following these rules:

  - If user name is in either server administrators, game moderators or game omniscient users, then user will join
    the game as an omniscient.
  - Otherwise, user will join the game as a simple observer.

- If, and only if, user joined the game as an omniscient, then the server will also check if he can be a game master.
  User is allowed to be a game master if his user name is in either server administrators or game moderators.

.. _join_game:

Join a game
+++++++++++

You can join a game using channel method :meth:`.Channel.join_game`, which sends a :class:`.JoinGame` request
accepting 3 parameters:

- ``game_id``: **(required)** the ID of game to join.
- ``registration_password``: *(optional)* the password to join the game, if this game requires a registration
  password.
- ``power_name``: *(optional)* name of power you want to play, determining your role in this game
  (as described in section above).

Method will return a :class:`.NetworkGame` object, which inherits from :class:`.Game` class.
You can check the attribute :attr:`.NetworkGame.role` of this object to get your role, which will be either
a power name, ``'omniscient_type'`` or ``'observer_type'``. You can also directly check your role by calling methods
:meth:`.NetorkGame.is_player_game`, :meth:`.NetorkGame.is_observer_game` or :meth:`.NetorkGame.is_omniscient_game`.

Example:

.. code-block:: python

    import asyncio
    from diplomacy.client.connection import connect
    async def main():
        connection = await connect('localhost', 8432)
        channel = await connection.authenticate('new_user', 'new_password', create_user=True)
        games_found = await channel.list_games(status='active')
        if not games_found:
            print('No active game found.')
            return
        a_game_id = games_found[0].game_id
        playable_powers = await channel.get_playable_powers(game_id=a_game_id)
        if not playable_powers:
            print('No playable powers for this game.')
            return
        power_name = playable_powers[0]
        game = await channel.join_game(game_id=a_game_id, power_name=power_name)
        print('My role is', game.role)
    asyncio.run(main())

Create a game
+++++++++++++

At any moment, you can create a new game using channel method :meth:`.Channel.create_game`, which send a
:class:`.CreateGame` request, accepting following optional parameters:

- **game_id**: game ID to set for the game. By default, a new game ID will be generated.
- **map_name**: name of map on which the game must be played. Default is standard map.
- **n_controls**: number of players required to start the game. By default, equals to the number
  of powers on the game map. If given number is less than number of powers on map, then remaining powers
  (when expected number of players will join the game) will be managed by server as "dummy" powers.
- **deadline**: number of seconds the server will wait before processing a phase. Default is 300 seconds
  (6 minutes). If set to zero (0), there will be no deadline, and game will advance to next phase either
  if there is no more waiting powers at current phase, or if a game master send a :class:`.ProcessGame`
  request to force game processing.
- **registration_password**: password required to join the game. By default, no password will be required.
- **power_name**: power name to control to join the game. By default, no power name is provided, and user
  will join the game as an omniscient user with game master privileges.
- **rules**: game rules. List of strings (called rules) to set up various game behaviours. Available rules
  are described into :doc:`/information/rules`. Default rules used for server games are stored in
  :const:`diplomacy.utils.constants.DEFAULT_GAME_RULES`.
- **state**: initial game state (for expert users)

Method will return a :class:`.NetworkGame` object representing the game you created, an
in which you will be automatically joined depending on ``power_name`` parameter you provide.

Example:

.. code-block:: python

    import asyncio
    from diplomacy.client.connection import connect
    async def main():
        connection = await connect('localhost', 8432)
        channel = await connection.authenticate('new_user', 'new_password', create_user=False)
        game = await channel.create_game(game_id='my_game', n_controls=0, deadline=0)
        games_found = await channel.list_games(status='active')
        game_identifiers = [game_info.game_id for game_info in games_found]
        assert game_identifiers and 'my_game' in game_identifiers, game_identifiers
        print('My role is', game.role)
    asyncio.run(main())


NetworkGame class
-----------------

WHen joining or creating a game, you finally get a :class:`.NetworkGame` object, which is your client version of the
server game, with a specific game role. You can then use this client game to interact with server game. Network game
object interface provides 2 types of methods:

- remote methods, to send game requests to server.
- notification methods, that allows you to add and remove callbacks to handle game notifications sent by server.

Notifications
+++++++++++++

Server can send notifications to a game at any moment, for example after game is processed.

When game receives the notification, it performs necessary internal updates based on notification data, and then
can call a callback to perform additional user-defined tasks.

You can check :mod:`diplomacy.communication.notifications` about all available game notifications.
For each notification class, netork game provide methods ``add_on_<NOTIFICATION_SNAKE_NAME>(callback)``
to add a callback, and ``clear_on_<NOTIFICATION_SNAKE_NAME>()`` to remove any callback for this notification.

.. note::

    When a game receives a game notification, there is always a preliminary checking where game makes any
    updates based on notification data. After updates are done, associated callback (if exists) is then called.

Game deadline, powers ordering and powers wait flags
++++++++++++++++++++++++++++++++++++++++++++++++++++

The main step when playing a diplomacy game is to order powers. When playing with basic :class:`.Game` class, you
can set orders for each power and then just force game processing by calling method :meth:`.Game.process`. While
this way is still possible with remote games if you are a game master, it is not suited to manage multiple players
who don't necessarily have game master privileges to force processing, and it would be annoying to wait for a game
master to force a game processing when all players already submitted their orders.

To handle all these details, server manages server games processing using 3 important information:

- the server game deadline, which define maximum time (in seconds) to wait before processing a single phase
- the order state of each game power, ie. whether or not power does have orders.
- the wait flag of each game power, which tell if power wants to wait (for example, if associated player is
  not sure about orders he submitted and plan to modify them again later) or not (for example, if player is
  sure about submitted orders).

Server uses these information in following procedure for each game for each phase:

- If deadline is nul (zero), then server will only check powers orders states and wait flags.
- If deadline is not null, then server will wait for given deadline.
- In both cases, at any moment, if all powers submitted orders (ie. order state is "True" for all powers)
  and don't wait (ie. wait flag is "False" for all powers), then this means that "games is in no wait state",
  and then server processes the game immediately. So, if game does have a deadline and reaches a no wait state
  before deadline is over, then server will stop waiting, process game now, and advance to next phase.

When game advances to next phase, all orders from previous phase are cleaned, so that order state become False
for all powers, and all wait flags are reset to default game wait flag value, depending on game rules
:ref:`REAL_TIME <rule_real_time>` and :ref:`ALWAYS_WAIT <rule_always_wait>`. Thus, for each phase, a player should
follow these steps:

- Check and set (if necessary) his power wait flag before submitting orders. For example, if game has rule
  ``REAL_TIME``, then wait flag will be False by default, ant player may consider set it to True. Otherwise,
  if he's the last to submit orders and if all powers wait flags are set to False, then server will process
  the game immediately without even letting him time to reconsider his submitted orders.
- Set orders.
- If his power wait flag is True, eventually re-set orders if needed.
- If his power wait flag is True and he's sure about his submitted orders, then set power wait flag to False.

Network game provides all necessary remote methods to handle orders and wait flag. You can see description below
and also check class documentation (:class:`.NetworkGame`).

.. warning::

    A game master can force processing even if game is not in no wait state, ie., even if some powers
    did not have submitted orders and or still have her wait flags to True.

Remote methods
++++++++++++++

Network game remote methods send requests and return responses, just like channel remote methods. However, allowed
requests depend on the game role of the netork game object you use to send them **and** whether or not your are
a game master.

A request sent by a network game remote method will always contains 3 automatically filled parameters:

- ``game_id``: the game ID
- ``game_role``: the game role of the network game object sending the request
- ``phase``: the game phase on client side (used by server for synchronisation checkings)

Then:

- You don't need to fill these parameters.
- Many important requests needs a power name as parameter, especially playing requests like
  :class:`.SetOrders`. If you have a player role, then the name of power you control will be
  used to fill ``game_role``, and then you won't need to explicitly fill ``power_name`` parameter for these
  requests. If you have an omniscient role with game master privileges, then you will need to fill ``power_name``
  parameter, as it will be the only way for server to get which power is queried.
  See requests documentation (:mod:`diplomacy.communication.requests`) about requests requiring
  optional ``power_name`` parameter.

You can check network game documentation (:class:`.NetworkGame`) and associated requests documentation
(:mod:`diplomacy.communication.requests`) about all available remote methods. Some important ones are:

- :meth:`.NetworkGame.set_orders` to set orders for a power.
- :meth:`.NetworkGame.clear_orders` to clear orders for a power.
- :meth:`.NetworkGame.wait` to turn on wait flag for a specific power.
- :meth:`.NetworkGame.no_wait` to turn off wait flag for a specific power.
- :meth:`.NetworkGame.leave` to disconnect from the game. Network game object will become invalid if this request
  succeeds.

Following example uses :meth:`.NetworkGame.set_orders` and :meth:`.NetworkGame.no_wait`.

.. code-block:: python

    import asyncio
    import random
    from diplomacy.client.connection import connect
    from diplomacy.utils import exceptions

    async def login(connection, username, password):
        """ Login to the server """
        try:
            channel = await connection.authenticate(username, password, create_user=True)
        except exceptions.DiplomacyException:
            channel = await connection.authenticate(username, password, create_user=False)
        return channel

    async def main(hostname='localhost', port=8432):
        """ Creates a game on server and play it. """
        power_name = 'FRANCE'
        connection = await connect(hostname, port)
        channel = await login(connection, 'random_user', 'password')

        # Rule POWER_CHOICE allows us to choose a specific power.

        # Rule ALWAYS_WAIT makes sure wait flags are set to True by default for controlled powers.

        # Rule DUMMY_REAL_TIME make sure wait flags are set to False
        # and orders as empty orders by default for dummy powers.

        # With n_controls set to 1 and a power name immediately given, we make sure game will
        # start immediately and we join game as player game controlling given power name.

        # We conveniently set deadline to 0, so that server won't schedule game.
        # Process will then depend only on orders and wait flags.

        game = await channel.create_game(rules={'POWER_CHOICE', 'ALWAYS_WAIT', 'DUMMY_REAL_TIME'},
                                         n_controls=1,
                                         power_name=power_name,
                                         deadline=0)

        assert game.is_game_active
        print('Game ID', game.game_id)

        # Playing game for 20 phases.
        for step in range(20):

            # Stop if game is done.
            if game.is_game_done:
                print('[%s] game done' % power_name)
                break

            # Save current phase. It will be used to check phase change.
            current_phase = game.get_current_phase()

            # Submitting orders. Select orders randomly using game.get_all_possible_orders().
            orders = []
            if game.get_orderable_locations(power_name):
                possible_orders = game.get_all_possible_orders()
                orders = [random.choice(possible_orders[loc]) for loc in
                          game.get_orderable_locations(power_name)
                          if possible_orders[loc]]

            # Submit orders.
            await game.set_orders(power_name=power_name, orders=orders)
            print('[%s/%s] - Submitted: %s' % (power_name, current_phase, orders))
            # Turn off wait flag.
            await game.no_wait()

            assert not game.get_power(power_name).wait

            # Waiting for game to be processed.
            # Server will process game, send relevant notification, and then game will be updated.
            # This may take a few time, and once it's done, game phase should have changed.
            while current_phase == game.get_current_phase():
                await asyncio.sleep(0.1)

        print('[%s]' % power_name, 'phase', game.get_current_phase())

    if __name__ == '__main__':
        asyncio.run(main())

.. note::

    You can also immediately set wait flag when calling set_orders:

    .. code-block:: python

        await game.set_orders(power_name=power_name, orders=orders, wait=False)

