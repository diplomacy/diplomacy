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
