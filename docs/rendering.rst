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

Other options are unchanged: ``incl_abbrev`` controls province abbreviations,
``output_format`` accepts ``'svg'``, and ``output_path`` optionally writes the
result to disk. Default engine actions that were not submitted as orders are not
drawn; see :doc:`orders`.
