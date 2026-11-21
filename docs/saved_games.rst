Legacy Saved Game Influence
===========================

Some legacy saved games store influence claims with split-coast aliases, duplicates, or
claims from more than one power for the same province. The default importer is unchanged
and does not resolve these legacy conflicts.

For an explicit, opt-in migration, use ``normalize_saved_game_influence`` from
``diplomacy.utils.export``. It returns a deep copy of the saved game and preserves all
metadata, phase history, messages, and unaffected values.

The helper only canonicalizes valid map split-coast locations. For each affected province,
it assigns the province to:

- the unique non-dislodged occupant, if that occupant is one of the claimants, or
- the sole claimant, if the province has no non-dislodged occupant.

Any other case raises ``ValueError`` with the phase and province. This includes multiple
occupants, a sole claimant that is not the occupant, and multiple claimants with no
occupant. The helper never guesses or silently picks a winner.

Migrating a saved-game JSON file
--------------------------------

Keep the original file as a backup and write the normalized result to a new file:

.. code-block:: python

   import json
   from diplomacy.utils.export import normalize_saved_game_influence

   with open('original.json', 'r') as source:
       saved_game = json.load(source)

   normalized = normalize_saved_game_influence(saved_game)

   with open('normalized.json', 'w') as destination:
       json.dump(normalized, destination)

Migrating a full serialized Game
--------------------------------

A full serialized ``Game`` is not in saved-game format. Rebuild the game, export it with
``to_saved_game_format``, then normalize the exported dictionary:

.. code-block:: python

   import json
   from diplomacy.engine.game import Game
   from diplomacy.utils.export import normalize_saved_game_influence, to_saved_game_format

   with open('original_game.json', 'r') as source:
       raw_game = json.load(source)

   game = Game.from_dict(raw_game)
   saved_game = to_saved_game_format(game)
   normalized = normalize_saved_game_influence(saved_game)

   with open('normalized_game.json', 'w') as destination:
       json.dump(normalized, destination)

If normalization raises ``ValueError``, review the reported phase and province manually.
Do not replace the original file automatically and do not add tolerance or a deterministic
winner for ambiguous games.

Loading multiple saved games in the web client
----------------------------------------------

The web client accepts ``.json`` and ``.jsonl`` files. File contents are detected: a file
that parses as one JSON object is loaded as a single saved game, while a file containing
one JSON object per nonempty line is loaded as multiple games. This also supports existing
``.json`` files created by appending saved games. To create a new multi-game file, write
the first game in write mode, then append later games:

.. code-block:: python

   from diplomacy.utils.export import to_saved_game_format

   to_saved_game_format(first_game, output_path='games.jsonl', output_mode='w')
   to_saved_game_format(second_game, output_path='games.jsonl', output_mode='a')

Each call writes one compact JSON record followed by a newline. The first call must use
``output_mode='w'`` to replace any existing file; later calls use ``output_mode='a'`` to
append. The file extension can be ``.jsonl`` or ``.json`` because detection is based on
content. Every record is parsed and validated before the client asks which game to load,
so a malformed line rejects the whole file instead of being skipped.

When a file contains several games, the client lists them with numbered IDs and asks for
the number of the game to load. Duplicate IDs are disambiguated with a position suffix,
such as ``(1/2)`` and ``(2/2)``. Cancelling the prompt leaves the current page unchanged.
