Default Orders and Order History
================================

The engine resolves a phase even when a power has not submitted an order for every unit.
These defaults are part of adjudication:

- In movement, an unordered unit holds.
- In adjustment, units are removed automatically when a power has more units than centers.
- In retreats, a dislodged unit with no retreat order is disbanded.

Default actions are not submitted orders, so they do not appear as order strings in
``Game.get_orders()`` or ``Game.order_history``. The engine still reports their effects in
the phase results and in the resulting game state.

What the order APIs record
--------------------------

``Game.get_orders(power)`` returns the orders currently recorded for the current phase.
Before processing, this is what was set through ``Game.set_orders()``, after the engine's
normal normalization and filtering. ``Game.process()`` captures that snapshot before
adjudication and returns it in ``GamePhaseData.orders``. The same snapshot is stored in
``Game.order_history[phase]``.

These APIs report engine-recorded submitted orders, after normalization and filtering,
not a raw audit log of every command a client sent. They do not synthesize default actions.
During adjustment and retreat phases, ``get_orders()`` excludes entries prefixed with
``VOID`` and ``WAIVE`` entries; the phase order snapshot inherits that filtering.

Movement: an unordered unit holds
---------------------------------

.. code-block:: python

   from diplomacy.engine.game import Game

   game = Game()
   game.set_orders('FRANCE', ['A PAR - BUR'])
   phase = game.process()

   assert phase.orders['FRANCE'] == ['A PAR - BUR']
   assert 'A MAR' in game.get_units('FRANCE')

France ordered A PAR to Burgundy and submitted no order for A MAR. A MAR held, but no
``A MAR H`` entry was added to ``phase.orders`` or ``game.order_history[phase.name]``.
The absence of a unit from the order snapshot means no order string was recorded for it.

Adjustment: automatic removals
------------------------------

.. code-block:: python

   from diplomacy.engine.game import Game
   from diplomacy.utils.order_results import OK

   game = Game()
   game.clear_centers('FRANCE')
   game.set_current_phase('W1901A')
   phase = game.process()

   assert phase.orders['FRANCE'] == []
   assert not game.get_units('FRANCE')
   assert all(OK in result for result in phase.results.values())

France submitted no adjustment orders, but had units and no centers. The engine removed
all its units to match the center count. Those automatic removals are reported in
``phase.results`` with the ``OK`` order result, not ``DISBAND``. ``DISBAND`` is used for
retreats.

Retreats: default disband
-------------------------

.. code-block:: python

   from diplomacy.engine.game import Game
   from diplomacy.utils.order_results import DISBAND

   game = Game()
   game.clear_units()
   game.clear_centers()
   game.set_units('RUSSIA', ['F SPA/SC'])
   game.set_units('FRANCE', ['F GAS'])
   game.set_units('ENGLAND', ['F BRE', 'A PAR'])

   game.set_orders('RUSSIA', 'F SPA/SC - POR')
   game.set_orders('FRANCE', 'F GAS H')
   game.set_orders('ENGLAND', ['F BRE - GAS', 'A PAR S F BRE - GAS'])
   game.process()  # F GAS is dislodged; the game is now in the retreat phase
   phase = game.process()  # No retreat orders were submitted

   assert phase.orders['FRANCE'] == []
   assert DISBAND in phase.results['F GAS']
   assert 'F GAS' not in game.get_units('FRANCE')

France submitted no retreat order for its dislodged F GAS. The engine disbanded it by
default, but ``phase.orders['FRANCE']`` remains empty. The outcome is available through
the phase results.

Reading results for a processed phase
-------------------------------------

``Game.result`` is cleared and replaced as the game advances. After ``Game.process()``
returns, ``game.result`` belongs to the new current phase, not necessarily the phase that
was just processed. Use phase-pinned data instead:

- the ``GamePhaseData`` returned by ``Game.process()``;
- ``Game.result_history[phase_name]``;
- ``Game.get_phase_from_history(phase_name).results``;
- ``Game.get_phase_history(from_phase, to_phase)``.

``Game.get_order_status(unit=...)`` reads the latest entry in ``Game.result_history``. An
empty list does not prove that the unit held. A successful move and an unordered unit
that held by default both have an empty recorded result. A unit absent from the phase's
results also returns an empty list, so distinguish a recorded empty result from no entry.
Automatic adjustment removals report ``OK``, while default retreat disbands report ``DISBAND``.

To determine whether an order was submitted, inspect the phase snapshot returned by
``Game.process()`` or stored in ``Game.order_history``. To determine what happened, inspect
the phase results together with the game state or unit positions before and after
processing. Do not infer a hold from an empty order status.
