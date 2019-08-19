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
