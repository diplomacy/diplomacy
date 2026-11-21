// ==============================================================================
// Copyright (C) 2019 - Philip Paquette, Steven Bocco
//
//  This program is free software: you can redistribute it and/or modify it under
//  the terms of the GNU Affero General Public License as published by the Free
//  Software Foundation, either version 3 of the License, or (at your option) any
//  later version.
//
//  This program is distributed in the hope that it will be useful, but WITHOUT
//  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
//  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
//  details.
//
//  You should have received a copy of the GNU Affero General Public License along
//  with this program.  If not, see <https://www.gnu.org/licenses/>.
// ==============================================================================
import $ from "jquery";
import {STRINGS} from "../../diplomacy/utils/strings";
import {Game} from "../../diplomacy/engine/game";

function validateSavedGame(savedGame, filename, index) {
    const prefix = `Invalid saved game #${index + 1} in ${filename}`;
    if (!savedGame || typeof savedGame !== 'object' || Array.isArray(savedGame))
        throw new Error(`${prefix}: expected a JSON object.`);
    if (!Array.isArray(savedGame.phases) || !savedGame.phases.length)
        throw new Error(`${prefix}: expected a nonempty phases array.`);
    savedGame.phases.forEach((phase, phaseIndex) => {
        if (!phase || typeof phase !== 'object' || Array.isArray(phase))
            throw new Error(`${prefix}: phase #${phaseIndex + 1} must be an object.`);
        if (!phase.state || typeof phase.state !== 'object' || Array.isArray(phase.state))
            throw new Error(`${prefix}: phase #${phaseIndex + 1} must have an object state.`);
        const phaseName = phase.state.name || phase.name;
        if (typeof phaseName !== 'string' || !phaseName)
            throw new Error(`${prefix}: phase #${phaseIndex + 1} must have a usable name.`);
    });
}

function parseSavedGames(text, filename) {
    const savedGames = [];
    try {
        savedGames.push(JSON.parse(text));
    } catch (wholeFileError) {
        void wholeFileError;
        // A whole-file parse fails for one object per nonempty line (JSONL), including
        // appended .json files. Parse every nonempty line so malformed later lines reject.
        const lines = text.split(/\r?\n/);
        for (let i = 0; i < lines.length; ++i) {
            if (!lines[i].trim())
                continue;
            try {
                savedGames.push(JSON.parse(lines[i]));
            } catch (error) {
                throw new Error(`Unable to parse line ${i + 1} of ${filename}: ${error.message}`);
            }
        }
    }
    if (!savedGames.length)
        throw new Error(`No saved games found in ${filename}.`);
    savedGames.forEach((savedGame, index) => validateSavedGame(savedGame, filename, index));
    return savedGames;
}

function savedGameId(savedGame) {
    return savedGame.id == null ? '(unknown)' : String(savedGame.id);
}

function savedGameLabel(savedGames, index) {
    const id = savedGameId(savedGames[index]);
    const matching = savedGames.filter(savedGame => savedGameId(savedGame) === id);
    if (matching.length === 1)
        return id;
    let position = 0;
    for (let i = 0; i <= index; ++i) {
        if (savedGameId(savedGames[i]) === id)
            ++position;
    }
    return `${id} (${position}/${matching.length})`;
}

function selectSavedGame(savedGames) {
    if (savedGames.length === 1)
        return savedGames[0];
    const choices = [];
    for (let i = 0; i < savedGames.length; ++i)
        choices.push(`${i + 1}) ${savedGameLabel(savedGames, i)}`);
    const answer = window.prompt(
        `Multiple saved games found. Enter the number of the game to load:\n${choices.join('\n')}`
    );
    if (answer === null)
        return null;
    const selection = answer.trim();
    const selectedIndex = /^\d+$/.test(selection) ? Number(selection) : 0;
    if (selectedIndex < 1 || selectedIndex > savedGames.length) {
        throw new Error(
            `Invalid saved game selection "${answer}". Enter a whole number from 1 to ${savedGames.length}.`
        );
    }
    return savedGames[selectedIndex - 1];
}

function buildGame(savedData) {
    const gameObject = {};
    gameObject.game_id = `(local) ${savedData.id}`;
    gameObject.map_name = savedData.map;
    gameObject.rules = savedData.rules;
    gameObject.state_history = {};
    gameObject.message_history = {};
    gameObject.order_history = {};
    gameObject.result_history = {};

    // Load all saved phases (expect the latest one) to history fields.
    for (let i = 0; i < savedData.phases.length - 1; ++i) {
        const savedPhase = savedData.phases[i];
        const gameState = savedPhase.state;
        const phaseOrders = savedPhase.orders || {};
        const phaseResults = savedPhase.results || {};
        const phaseMessages = {};
        if (savedPhase.messages) {
            for (let message of savedPhase.messages) {
                phaseMessages[message.time_sent] = message;
            }
        }
        if (!gameState.name)
            gameState.name = savedPhase.name;
        gameObject.state_history[gameState.name] = gameState;
        gameObject.message_history[gameState.name] = phaseMessages;
        gameObject.order_history[gameState.name] = phaseOrders;
        gameObject.result_history[gameState.name] = phaseResults;
    }

    // Load latest phase separately and use it later to define the current game phase.
    const latestPhase = savedData.phases[savedData.phases.length - 1];
    const latestGameState = latestPhase.state;
    const latestPhaseOrders = latestPhase.orders || {};
    const latestPhaseResults = latestPhase.results || {};
    const latestPhaseMessages = {};
    if (latestPhase.messages) {
        for (let message of latestPhase.messages) {
            latestPhaseMessages[message.time_sent] = message;
        }
    }
    if (!latestGameState.name)
        latestGameState.name = latestPhase.name;
    // TODO: NB: What if latest phase in loaded JSON contains order results? Not sure if it is well handled.
    gameObject.result_history[latestGameState.name] = latestPhaseResults;

    gameObject.messages = [];
    gameObject.role = STRINGS.OBSERVER_TYPE;
    gameObject.status = STRINGS.COMPLETED;
    gameObject.timestamp_created = 0;
    gameObject.deadline = 0;
    gameObject.n_controls = 0;
    gameObject.registration_password = '';
    const game = new Game(gameObject);

    // Set game current phase and state using latest phase found in JSON file.
    game.setPhaseData({
        name: latestGameState.name,
        state: latestGameState,
        orders: latestPhaseOrders,
        messages: latestPhaseMessages
    });
    return game;
}

export function loadGameFromDisk() {
    return new Promise((onLoad, onError) => {
        const input = $(document.createElement('input'));
        input.attr("type", "file");
        input.change(event => {
            const file = event.target.files && event.target.files[0];
            if (!file) {
                onLoad(null);
                return;
            }
            if (!/\.(json|jsonl)$/i.test(file.name)) {
                onError(new Error(`Invalid saved game filename ${file.name}. Expected a .json or .jsonl file.`));
                return;
            }
            const reader = new FileReader();
            reader.onload = () => {
                try {
                    const savedGames = parseSavedGames(reader.result, file.name);
                    const savedGame = selectSavedGame(savedGames);
                    onLoad(savedGame ? buildGame(savedGame) : null);
                } catch (error) {
                    onError(error);
                }
            };
            reader.onerror = () => onError(new Error(`Unable to read saved game file ${file.name}.`));
            reader.onabort = () => onError(new Error(`Reading saved game file ${file.name} was aborted.`));
            try {
                reader.readAsText(file);
            } catch (error) {
                onError(error);
            }
        });
        input.trigger('click');
    });
}
