Rendering
=========

A game can be rendered to SVG with :meth:`diplomacy.engine.game.Game.render`:

.. code-block:: python

    from diplomacy import Game

    game = Game()
    svg = game.render()
    with open('game.svg', 'w') as output_file:
        output_file.write(svg)

The same method is available on :class:`diplomacy.engine.renderer.Renderer`.

Order overlays
--------------

``incl_orders`` controls which order overlays are drawn:

* ``True`` (the default) draws the orders issued by every power.
* ``False`` draws no order overlays.
* A power name draws only the orders issued by that power. The name is
  case-insensitive, so ``'france'`` and ``'FRANCE'`` select the same power.
  An unknown name raises :class:`ValueError`.

The filter applies to movement, retreat, support, and convoy orders, and to
adjustment orders such as builds and disbands. It selects orders by the power
issuing them: for example, a French support order for a German unit is drawn when
``incl_orders='FRANCE'`` and hidden when ``incl_orders='GERMANY'``.

Units, dislodged units, influence, and supply centers are always drawn for every
power, regardless of the order filter. The filter is a display option over the
full public game state; it is not a fog-of-war or access-control mechanism.

Other options are also available: ``incl_abbrev`` controls province
abbreviations, ``output_format`` accepts ``'svg'``, ``output_path`` optionally
writes the result to disk, and ``unit_labels`` adds unit-type badges. Default
engine actions that were not submitted as orders are not drawn; see
:doc:`orders`.

Unit labels
-----------

``unit_labels=True`` adds a small high-contrast ``A`` or ``F`` badge to each
regular and dislodged unit actually on the board. Badges sit in the unit's
upper-right corner with a white circle and black text, independent of power
colors. They are not added to order overlays, so build-order previews and other
order symbols are never labeled. ``pointer-events="none"`` keeps badges out of
map interaction.

The default ``False`` leaves the rendered SVG unchanged.

.. code-block:: python

    svg = game.render(unit_labels=True)

Power colors
------------

``game.get_power_color('france')`` returns the SVG's ``POWERCOLOR`` metadata
value for that power. The same accessor is available on ``Renderer``. Names are
case-insensitive; unknown names raise ``ValueError``. A valid power with no SVG
or no color metadata returns ``None``.

These are map-specific metadata/territory colors, not necessarily unit fills:
standard France returns ``'royalblue'``, while its units use ``'deepskyblue'``.
No palette is inferred when metadata is missing. The game reuses an existing
renderer, including a renderer initialized with a custom ``svg_path``. Map
variants use their root map's SVG when they have no SVG of their own.

.. code-block:: python

    from diplomacy import Game

    game = Game()
    france_color = game.get_power_color('FRANCE')  # 'royalblue'
