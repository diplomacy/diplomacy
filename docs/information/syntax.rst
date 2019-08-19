.. _project_syntax:

Syntax used in this project for orders and phase
================================================

Structure of a game turn
------------------------

Diplomacy is a turn game where each turn is divided into many phases.
There are 3 types of phases, each allowing specific orders:

- movement phase, the main game phase, where most "active' actions can be ordered to units. Allowed orders are:

  - **Move**: move a unit from a province to another
  - **Hold**: keep a unit where she is
  - **Support move**: support another moving unit
  - **Support hold**: support another holding unit
  - **Convoy** (for fleet only): allow an army to move from a coast to another coast

- retreat phase, occurring optionally after a movement phase if there are some dislodged units allowed to retreat
  to other provinces. Allowed orders are:

  - **retreat**: move a dislodged unit from a province to another adjacent unoccupied province
  - **destroy**: destroy a dislodged unit

- adjustment phase, where each power can check its units and take effective ownership of conquered supply centers.
  Allowed orders are:

  - **build army**: build an armny in an unoccupied supply center
  - **build fleet**: build a fleet in an unoccupied coastal supply center
  - **disband unit**: destroy a unit

A game turn usually consists of one or many movement phases (depending on game variant). Each movement phase may be
followed by a retreat phase if there are some dislodged units to manage. After all movement phases are processed,
the turn may end with an adjustment phase if there are units that may be built or disbanded, according to current
game state.

Syntax of a phase name
----------------------

A phase long name typically has format ``<SEASON> <YEAR> <PHASE TYPE>``, where:

- ``<SEASON>`` is usually a real-world season name (e.g. ``SPRING``), used to make phase name unique
  (e.g. if game variant allows multiple movement phases per year).
- ``<YEAR>`` is a year number left-padded with zero up to 4 digits (e.g. ``1990``, ``0050``).
- ``<PHASE TYPE>`` describe the phase type (e.g. ``MOVEMENT``, ``RETREATS`` or ``ADJUSTMENTS``).

A short phase name typically consists of 6 characters taken from long name:

- The first letter of season
- The four digits of year
- The first letter of phase type

For example, on ``standard`` map, a turn is a year divided into 2 movement phases (spring then fall) and
an adjustement phase on winter. In year 1901, we will have following names:

- ``SPRING 1901 MOVEMENT`` (``S1901M``)
- ``SPRING 1901 RETREATS`` (``S1901R``) *if necessary*
- ``FALL 1901 MOVEMENT`` (``F1901M``)
- ``FALL 1901 RETREATS`` (``F1901R``) *if necessary*
- ``WINTER 1901 ADJUSTMENTS`` (``W1901A``)


Syntax of orders
----------------

In this project, oders can be set by calling method ``Game.set_orders`` with power name and list of orders.
There is a recommended syntax to use to set orders:

- Power name should be the full upper-case name of power to orders
- In an order string, the unit type should be ``A`` for an army and ``F`` for a fleet.
- In an order string, a province should be specified using the province short name. It is usually a
  3-letters uppercase string. If you need to indicate a specific coast for a province that has many coasts,
  then short name should be a 6-letters string with format ``<PROVINCE SHORT NAME>/<COAST SHORT NAME>``. Coast
  short name is a 2-letters uppercase string, either ``EC``, ``WC``, ``NC``, ``SC`` (for East cooast, West coast,
  North coast, South coast). For example, on ``standard`` map, province Paris should be indicated with ``PAR``,
  and South coast of St. Petersburg should be indicated using ``STP/SC``.

These are the recommanded syntax for each order type. ``<U>`` is a unit type.

- **Move**: ``<U> <SRC_LOC> - <DST_LOC>``. If the move is intended to be done using a convoy,
  you must append ``VIA`` to the order. Examples: ``A PAR - BUR``, ``A PAR - SPA/NC VIA``.
- **Hold**: ``<U> <LOC> H``. Example ``A PAR H``.
- **Support move**: ``<U> <LOC> S <U> <SRC_LOC> - <DST_LOC>``. Example: ``A PAR S A MAR - BRE``.
- **Support hold**: ``<U> <LOC> S <U> <OTHER_LOC>``. Example ``A PAR S A MAR``.
- **Convoy**: ``F <LOC> C A <SRC_LOC> - <DST_LOC>``. Example ``F NAT C A PAR - SPA/SC``.
- **retreat**: ``<U> <SRC_LOC> R <DST_LOC>``. Example: ``A PAR R MAR``.
- **destroy** and **disband**: ``<U> <LOC> D``. Example: ``A PAR D``.
- **build**: ``<U> <LOC> B``. Examples: ``A PAR B``, ``F SPA/NC B``.
