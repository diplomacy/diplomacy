Game engine
===========

Load a game
-----------

The main entry point and main symbol of the whole Diplomacy project is
the game engine represented by class :class:`.Game`.

.. code-block:: python

    from diplomacy import Game
    game = Game()

When creating a game, you can specify a game ID (as a string) with parameter `game_id`. If not provided, a game ID
will be automatically generated.

.. code-block:: python

    from diplomacy import Game
    g1 = Game()
    g2 = Game(game_id='my_game_id')

By default, game engine is created to play on ``standard`` map, but you can specify a map with parameter ``map_name``.

.. code-block:: python

    from diplomacy import Game
    g1 = Game()
    g2 = Game(map_name='standard')
    g3 = Game(map_name='modern')

To get the list of currently available map names, you can use :meth:`.Map.available_map_names`:

.. code-block:: python

    from diplomacy import Map
    print(Map.available_map_names())

Retrieve game information
-------------------------

Once game is loaded, you can get various information.

- Game map name is saved into :attr:`.Game.map_name`.
- Game ID is saved into :attr:`.Game.game_id`. You may use it anywhere you need to identify this game specifically.
- Current phase is saved into :attr:`.Game.phase` as a long name. To get convenient mostly-used short phase name,
  use :meth:`.Game.get_current_phase` or property :attr:`.Game.current_short_phase`.
- You can get the list of map powers using :meth:`.Game.get_map_power_names`.
- You can get list of current units, supply centers, orders or orderable provinces (provinces that can receive orders)
  for all powers or for a specific power using specific methods:

  - :meth:`.Game.get_units`
  - :meth:`.Game.get_centers`
  - :meth:`.Game.get_orders`
  - :meth:`.Game.get_orderable_locations`

  When called for all powers, these methods return a dictionary mapping each power name to a list of queried data.
  When called for one power, these methods return only the list of queried data for given power.

Example:

.. code-block:: python

    from diplomacy import Game
    g = Game()
    print('Map:', g.map_name)
    print('Current phase long name:', g.phase)
    print('Current phase short name:', g.get_current_phase())
    print('Playable powers:', list(g.get_map_power_names()))
    print('All units', g.get_units())
    print('All centers', g.get_centers())
    print('All current orders', g.get_orders())
    print('All orderable locations', g.get_orderable_locations())
    print('France units', g.get_units('FRANCE'))
    print('France centers', g.get_centers('FRANCE'))
    print('France current orders', g.get_orders('FRANCE'))
    print('France orderable locations', g.get_orderable_locations('FRANCE'))


Render game
-----------

If you play on a renderable map, then you can render game current state using :meth:`.Game.render`.

Not all playable maps can be currently rendered. To get list of renderable maps, call :meth:`.Map.available_map_names`
with parameter ``to_render`` set to ``True``:

.. code-block:: python

    from diplomacy import Map
    print(Map.available_map_names(to_render=True))

Method :meth:`.Game.render` can receive some important parameters:

- incl_orders: (default ``True``) to render current orders.
- incl_abbrev: (default ``False``) to display province short names.
  It may be useful to set it to ``True`` if you are learning how to play on a map you don't correctly know.
- output_name: (default ``None``): name of output image file. Mandatory if you want to get rendered image into
  a file. Output file wille be written in ``<output_name>.svg``.

Example:

.. code-block:: python

    from diplomacy import Game
    g = Game()
    g.render(incl_abbrev=True, output_name='game_%s' % g.get_current_phase())

Set orders
----------

You can set orders for a specific power using :meth:`.Game.set_orders`, by passing a power name and a list of orders.

- Each order must be related to one province, and you must not pass many orders for a same province.
- Orders are valid only for current game phase.
- If ordered power already contains order for a unit and your new orders list contains an order for that unit too,
  then previous order will be overwritten with new order. You can prevent this behaviour by setting parameter
  ``replace`` to ``False``, and then units already ordered won't be reordered.
- Impossible orders (e.g. move order from a province to another non-adjacent one) and orders syntaxically invalid
  will be silently skipped.

Allowed orders depend on current phase. To get familiar with order types and syntax, we strongly recommend that
you read the `game rules <../_static/rules.pdf>`_ and the
:doc:`quick description of recommended syntax used by this project <../information/syntax>`.

Example:

.. code-block:: python

    from diplomacy import Game
    g = Game()
    # Let's render game before setting any orders. No order will be rendered.
    g.render(incl_abbrev=True, output_name='g1')
    # Then let's set 2 orders for France, 1 for Germany, and 2 for Russia.
    g.set_orders('FRANCE', ['A PAR - BUR', 'F BRE - MAO'])
    g.set_orders('GERMANY', ['A MUN S A PAR - BUR'])
    g.set_orders('RUSSIA', ['A WAR H', 'A MOS S A WAR'])
    # Then let's render game again. Then orders will be displayed.
    g.render(incl_abbrev=True, output_name='g2')
    # We can also check that all orders were correctly set.

If you are not sure about which orders are allowed, you can use the extremely powerful method
:meth:`.Game.get_all_possible_orders`, which return a dictionary mapping each province short name to a list of
all possible orders for that province. Empty list means there is not possible order for related province for
current game phase. All orders will be already written in recommended format, and you will just have to pick
some of them!

.. code-block:: python

    from diplomacy import Game
    g = Game()
    print(g.get_all_possible_orders())

To clear orders for all powers of a specific one, you can use :meth:`.Game.clear_orders`.

.. code-block:: python

    from diplomacy import Game
    g = Game()
    g.set_orders('FRANCE', ['A PAR - BUR', 'F BRE - MAO'])
    g.set_orders('GERMANY', ['A MUN S A PAR - BUR'])
    g.set_orders('RUSSIA', ['A WAR H', 'A MOS S A WAR'])
    print(g.get_orders())
    g.clear_orders('FRANCE')
    print(g.get_orders())
    g.clear_orders()
    print(g.get_orders())


Process game
------------

Whether or not orders are set, a game can be processed using :meth:`.Game.process`. A processing consist of
computing current game phase and advance to next phase. Processing will execute all available valid orders,
move units and change controlled powers according to executed orders, update supply centers if necessary
(in adjustment phases only), determine the next phase to run and move game to that phase by updating all
relevant attributes. For certain phases, processing may also execute a default order where order was
required. For example, on retreats phase, if no order was set for a dislodged unit (e.g. a retreat order),
then unit will be destroyed by default.

Example:

.. code-block:: python

    from diplomacy import Game
    g = Game()
    print(g.get_current_phase())
    # Game will advance to fall with map being unchanged, as no order was set.
    g.process()
    print(g.get_current_phase())
    g.set_orders('FRANCE', ['A MAR - SPA'])
    g.set_orders('RUSSIA', ['A WAR - GAL'])
    g.set_orders('GERMANY', ['A MUN - BOH'])
    # Game will advance to winter, without skipping it, as France has gained a supply center and can build at MAR.
    g.process()
    print(g.get_current_phase())
    g.set_orders('FRANCE', ['F MAR B'])
    # Game will now advance to spring of next year.
    g.process()
    print(g.get_current_phase())
    # Let's make Germany attack Austria at VIE with support of Russia.
    g.set_orders('GERMANY', ['A BOH - VIE'])
    g.set_orders('RUSSIA', ['A GAL S A BOH - VIE'])
    # Game will now advance to a retreat phase, because Austria unit at VIE was dislodged.
    g.process()
    print(g.get_current_phase())
    # We will process without setting any order. So, by default, Austria unit will be destroyed.
    # Game will advance to fall.
    g.process()
    print(g.get_current_phase())
    # We will advance again without any order. Game will go to winter, as Germany has won a supply center.
    g.process()
    print(g.get_current_phase())
    # We will advance again without any order.
    # Germany could have built 1 unit, but it's not mandatory, so no default order will be set for that power.
    g.process()
    print(g.get_current_phase())
    g.render(output_name='g_%s' % g.get_current_phase(), incl_abbrev=True)

Terminate game
--------------

Win a game
^^^^^^^^^^

To win a game, a power must conquer at least half of all supply centers available on the map. You can get the
minimum number of centers required to win in :attr:`.Game.win`. For example, on ``standard`` map,
a power must conquer at least 18 supply centers to win.

.. code-block:: python

    from diplomacy import Game
    g = Game()
    print(g.win)

A soon as a power reaches the minimum required number of supply centers, the game ends, and game phase stored
in :attr:`.Game.phase` is set to string ``'COMPLETED'``.

To check if a game is terminated, you can then compare game phase name to string ``'COMPLETED'``,
or simply check if boolean flag `.Game.is_game_done` is ``True``. The final result of game is stored in
:attr:`.Game.outcome` as a list containing:

- The short name of phase when game ended (ie. latest phase before ``'COMPLETED'`` phase), at first list index
- The winners, at next list indices.

For example, an outcome may be ``['W1964A', 'FRANCE']``, meaning that France wins the game at Winter 1964.


Draw a game
^^^^^^^^^^^

Another way to terminate a game is to declare a draw. A draw is a proclamation that all powers with remaining
units on the map are considered as winners. You can force a game to draw by calling :meth:`.Game.draw`. Game
will terminate the same way as if there was 1 winner, with phase set to ``'COMPLETED'`` and
:attr:`.Game.is_game_done` set to `True`, but outcome may now contain more than 1 winning power, depending on
how many powers remained on map when draw method was called.

You may even go further by explicitly declaring which are the winning powers, using parameter ``winners`` of
:attr:`.Game.draw`. If provided, ``winners`` must be a list of power names to be considered as winners. Outcome
field will then contain current short phase name and the given list of winners.

Example: create a game and draw it immediately:

.. code-block:: python

    from diplomacy import Game
    g = Game()
    g.draw()
    # Game is done.
    print(g.is_game_done)
    # Phase is COMPLETED.
    print(g.phase)
    # Outcome will contains phase S1901M followed by the name of all powers on the map
    # (as they all still have units on the map).
    print(g.outcome)

.. note::

    Short phase name for long phase name ``'COMPLETED'`` is also ``'COMPLETED'``.

    .. code-block:: python

        from diplomacy import Game
        g = Game()
        g.draw()
        assert g.phase == g.get_current_phase() == 'COMPLETED'

Example: eliminate a power, then draw.

.. code-block:: python

    from diplomacy import Game
    g = Game()
    # Let's make AUSTRIA and RUSSIA cooperate to eliminate TURKEY.
    # S1901M
    g.set_orders('AUSTRIA', ['F TRI - ALB', 'A BUD RUM', 'A VIE BUD'])
    g.set_orders('RUSSIA', ['F SEV - BLA', 'A WAR - GAL', 'A MOS - SEV'])
    g.process()
    # F1901M
    g.set_orders('AUSTRIA', ['F ALB - GRE', 'A RUM - BUL', 'A BUD - SER'])
    g.set_orders('RUSSIA', ['A SEV - ARM'])
    g.process()
    # W1901A, pass
    g.process()
    # S1902M, we can start to attack!
    g.set_orders('AUSTRIA', ['F GRE - AEG', 'A BUL - CON', 'A SER - BUL'])
    g.set_orders('RUSSIA', ['F BLA S A BUL - CON'])
    g.process()
    # S1902R will be skipped as Turkey disloged army at CON cannot retreat anywhere.
    # F1902M, we continue and terminate the destruction.
    g.set_orders('AUSTRIA', ['A CON - SMY', 'F AEG S A CON - SMY', 'A BUL - CON'])
    g.set_orders('RUSSIA', ['A ARM - ANK', 'F BLA S A ARM - ANK'])
    g.process()
    # F1902R, we pass.
    g.process()
    # W1902A, turkey does not have units nor centers anymore, thus is eliminated. Pass.
    g.process()
    # S1903M. We can draw now, and there will be only 6 winning powers (all but Turkey).
    g.draw()
    assert g.is_game_done
    assert g.get_current_phase() == 'COMPLETED'
    print(g.outcome)
    g.render(incl_abbrev=True, output_name='d_%s' % (g.get_current_phase()))


Example: draw with a specific list of winners.

.. code-block:: python

    from diplomacy import Game
    g = Game()
    g.draw(winners=['TURKEY', 'ENGLAND'])
    print(g.get_current_phase())
    print(g.is_game_done)
    print(g.outcome)

Get orders status
-----------------

If you submit orders on a phase, you may want to know if orders were successfully executed or not. Orders results
are available once phase is processed, and then can be retrieved using :meth:`.Game.get_order_status`. This method
can take 3 optional parameters mutually exclusive (only none or 1 of them can be passed):

- ``power_name``: if provided, only results for this power will be returned as a dictionary mapping each power
  unit to list of results for order submitted to this unit.
- ``unit``: if provided, only list of results for order submitted to this unit is returned.
- ``loc``: if provided, method will look for orderable unit at this location, and then will return found unit with
  list of results for order submitted to this unit. If no orderable unit was found for this location, then location
  will be returned with an empty list.

If no parameters are passed, method will return results for all powers in a dictionary mapping each power name to
power results.

The results list for a unit is a list of flags describing how the order associated to this unit was processed.
Possible flags are listed into :mod:`diplomacy.utils.order_results`.
If no order was submitted to the unit, and if nothing happens to that unit, then list will be empty.
If submitted order was successfully executed, list will either be empty or only contain flag ``OK``
(printed as an empty ``''``).

.. warning::

    As game silently skip impossible orders and orders syntaxically invalid,
    you will get order results only for possible submitted orders.

Example:

.. code-block:: python

    from diplomacy import Game
    g = Game()
    g.set_orders('FRANCE', ['F BRE - SPA', 'A PAR - BRE', 'A MAR - LYO', 'invalid'])
    g.set_orders('RUSSIA', ['F STP - FIN', 'A MOS - UNKNOWN', 'F SEV - PAR', 'A WAR - GAL'])
    print(g.get_orders('FRANCE'))
    print(g.get_orders('RUSSIA'))
    g.process()
    print(g.get_order_status('FRANCE'))
    print(g.get_order_status('RUSSIA'))

More control to game map
------------------------

Game class provide more powerful methods to play with game map, even against normal game life cycle.
Methods include:

- :meth:`.Game.clear_centers` : allows to remove all supply centers for either all powers or a specific power (with parameter ``power_name``).
- :meth:`.Game.clear_units`: allows to remove all units for either all powers or a specific power (with parameter ``power_name``).
- :meth:`.Game.set_centers`: allows to set supply centers for a specific power.

  - Power is specified with parameter ``power_name``.
  - Parameter ``centers`` can be either a supply center short name or a list of short names for supply centers.
  - Boolean parameter ``reset``, if set to ``True``, forces power centers to be cleared before setting new centers.

- :meth:`.Game.set_units` allows to set units for a specific power.

  - Power is specifid with parameter ``power_name``.
  - Parameter ``units`` can be either a unit or a list of units. A unit is a string with format
    ``<UNIT TYPE> <PROVINCE SHORT NAME>``, e.g. ``A PAR`` or ``F STP/NC``.
  - Boolean parameter ``reset``, if set to ``True``, forces power units to be cleared before setting new units.

You can check full documentation of class :class:`.Game` to be aware of all available public methods and what
they allow to do.
