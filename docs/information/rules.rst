Game rules
==========

We describe below the available game rules that can be passed to parameter ``rules`` when creating a game.

Fore more info, see:

- class :class:`.Game` about default rules for a game.
- class :class:`.ServerGame` about default rules for a server game.
- Remote game creation method in Python client: :meth:`.Channel.create_game`.

POWER_CHOICE
------------

With this rule, user will be allowed to choose a player when joining the game.

Without this rule, if user specifies a power, then server will instead assign him a randomly selected power
taken between available playable powers.

MULTIPLE_POWERS_PER_PLAYER
--------------------------

With this rule, a user can control more than 1 power in a game. He can join a game more than once (but once per
opened channel) and ask for a different power each time.

Without this rule, a user can control at most 1 power per game.

NO_OBSERVATIONS
---------------

If this rule is used, no observers are allowed for the game. Note that game masters
can still observe the game as omniscient observers even if this rule is present.

SOLITAIRE
---------

**Forces these rules:** ``NO_DEADLINE``, ``CD_DUMMIES``, ``ALWAYS_WAIT``

With this rule, game will be a solitaire game.

A solitaire game is a game where all powers are dummy powers. No one could join a solitaire server game,
except game masters. It's best suited for simulations, testing, or to play alone as a game master.

A solitaire server game won't advance automatically, so a game master will need to force processing by sending a
:class:`.ProcessGame` request.

START_MASTER
------------

With this rule, a server game can starts only if a game master set game status to ``active``. This can be done using
game method :meth:`.NetworkGame.start_game`.

Without this rule, server game will start as soon as the required number of players joined the game.

NO_PRESS
--------

**Forbids these rules:** ``PUBLIC_PRESS``

With this rule, players won't be allowed to send messages.

PUBLIC_PRESS
------------

**Forbids these rules:** ``NO_PRESS``

With this rule, players are allowed to send messages.

DONT_SKIP_PHASES
----------------

If this rule is used, all phases (including phases where all players need
to issue blank orders) will be played, and empty phases won't be skipped.

IGNORE_ERRORS
-------------

With this rule, order errors will be silently ignored.

BUILD_ANY
---------

With this rule, powers may build new units at any owned supply center, not simply at their home supply centers.

CIVIL_DISORDER
--------------

**Forces these rules:** ``CD_DUMMIES``

With this rule, any power that has not submitted orders:

- when the game's Master submits a PROCESS command, or
- when the deadline has passed (or, if a grace period is
  specified in the TIMING line of the game's
  status file, after the expiration of
  the grace period),

will have its orders entered automatically.  During movement phases, all
units will HOLD, during retreat phases, all dislodged units will DISBAND,
and during adjustment phases, all builds will be WAIVED, and all removals
will be entered using random choice from among the power's on-board units,
with preference given to retaining units that are situated on supply centers.

CD_DUMMIES
----------

Assuming no powers have set their WAIT flag, orders will be
processed as **soon** as all NON-DUMMY
players have submitted orders.  Any dummy power will be considered in civil disorder (as described
above) at that time.  Note the distinction -- CIVIL_DISORDER
will default the orders of all powers (whether dummy or not), while
CD_DUMMIES will default the orders only of the dummy powers.

NO_DEADLINE
-----------

In certain cases, e.g. for testing and solving Diplomacy puzzles (solitaire games),
there's no need for a deadline. It's up to the game master to process each turn after
all (relevant) orders are submitted, or for all players to submit their orders
without setting their WAIT flag. This behavior can be
influenced with the NO_WAIT and ALWAYS_WAIT options.

Note that, adding rule ``NO_DEADLINE`` is equivalent to setting game deadline to zero (``0``).

.. _rule_real_time:

REAL_TIME
---------

**Forbids these rules:** ``ALWAYS_WAIT``

With this rule, wait flag is set to ``False`` by default for all non-dummy powers after each game processing.

.. _rule_always_wait:

ALWAYS_WAIT
-----------

**Forbids these rules:** ``REAL_TIME``

With this rule, wait flag is set to ``True`` by default for all non-dummy powers after each game processing.

DUMMY_REAL_TIME
---------------

With this rule, wait flag is set to ``False`` by default for all dummy powers after each game processing.

Without this rule, wait flag for dummy powers is set to ``True`` when a new phase starts.

HOLD_WIN
--------

With this rule, to win a game using this rule, a player must achieve the winning condition two game-years in a row.

SHARED_VICTORY
--------------

With this rule, the game ends immediately after the first
player reaches the victory condition. If any other player fulfills this
condition at the same time (in games where this number is lower than
the default of half of the number of SCs plus one), they are jointly
declared winners (or participants in a draw, depending on definitions),
irrespective of the fact that one may have a higher total than the
other. This replaces the normal victory criterion where only a
single player can be victorious and ties result in the continuation
of the game.

NO_CHECK (for ``standard`` map only)
------------------------------------

This rule emulates face-to-face play, in which players could (by
accident or design) issue invalid orders to their units.  This rule
is also useful in NO_PRESS games to allow for limited player
communication.

When they are entered, movement phase orders are only very minimally
checked for validity.  The ONLY checks that are made at the time an
order is entered are:

- Every component of the order must be understood.  That is, the
  order must appear to be a Diplomacy move, convoy, support or
  hold order, and all placenames must be identifiable on the map
  in use. This check catches inadvertent misspellings, such as "URK" for "UKR".
  In fact, this is known as the "Urk check."

- Any placename abbreviation that is potentially ambiguous is declared
  erroneous and must be changed.  For example, the order "TYR H" is rejected
  because it may be an order for an army in Tyrolia to hold, or for a
  fleet in the Tyrrhenian Sea to hold.

- A support for a fleet move may not specify the destination coast of
  the fleet.  This error must also be corrected.

Therefore, most errors (including the omission of the fleet-path of
a convoying army from its order!) are not detected until the phase
is ready to process, at which time the erroneous orders will be ignored.
All units that had been given erroneous or multiple orders will
HOLD (and may receive support), and all erroneous orders will
be reported in the results, flagged as (*invalid*).
