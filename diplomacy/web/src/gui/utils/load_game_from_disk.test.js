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
/* eslint-env jest */
import {loadGameFromDisk} from "./load_game_from_disk";
import $ from "jquery";

jest.mock("jquery", () => {
    const createdInputs = [];
    const jquery = (element) => {
        if (element && element.nodeName === 'INPUT')
            createdInputs.push(element);
        return {
            attr(name, value) {
                element.setAttribute(name, value);
                return this;
            },
            change(handler) {
                element.changeHandler = handler;
                return this;
            },
            trigger(name) {
                if (name === 'click')
                    element.clickedBeforeChange = !element.changeHandler;
                return this;
            }
        };
    };
    jquery.createdInputs = createdInputs;
    return {__esModule: true, default: jquery};
});

const OriginalFileReader = global.FileReader;
const readers = [];

function savedGame(id, phaseName = 'S1901M') {
    return {
        id: id,
        map: 'standard',
        rules: [],
        phases: [{name: phaseName, state: {name: phaseName}}]
    };
}

function jsonl(...games) {
    return games.map(game => JSON.stringify(game)).join('\n') + '\n';
}

function startLoad(filename) {
    const promise = loadGameFromDisk();
    const input = $.createdInputs[$.createdInputs.length - 1];
    Object.defineProperty(input, 'files', {configurable: true, value: [{name: filename}]});
    input.changeHandler({target: input});
    return {promise: promise, reader: readers[readers.length - 1], input: input};
}

function loadFile(filename, content) {
    const request = startLoad(filename);
    request.reader.result = content;
    request.reader.onload();
    return request;
}

beforeEach(() => {
    $.createdInputs.length = 0;
    readers.length = 0;
    global.FileReader = class {
        constructor() {
            readers.push(this);
        }
        readAsText(file) {
            this.file = file;
        }
    };
});

afterEach(() => {
    global.FileReader = OriginalFileReader;
    jest.restoreAllMocks();
});

describe('loadGameFromDisk', () => {
    it('loads a single pretty-printed JSON game without prompting', async () => {
        const prompt = jest.spyOn(window, 'prompt');
        const request = loadFile('saved.json', JSON.stringify(savedGame('pretty-game'), null, 2));

        const game = await request.promise;

        expect(game.game_id).toBe('(local) pretty-game');
        expect(prompt).not.toHaveBeenCalled();
        expect(request.input.clickedBeforeChange).toBe(false);
    });

    it('lets the user choose a numbered JSONL record', async () => {
        const prompt = jest.spyOn(window, 'prompt').mockReturnValue('2');
        const request = loadFile('games.jsonl', jsonl(savedGame('first'), savedGame('second')));

        const game = await request.promise;

        expect(game.game_id).toBe('(local) second');
        expect(prompt).toHaveBeenCalledTimes(1);
        expect(prompt.mock.calls[0][0]).toContain('1) first');
        expect(prompt.mock.calls[0][0]).toContain('2) second');
    });

    it('loads appended records from a .json file by content', async () => {
        const prompt = jest.spyOn(window, 'prompt').mockReturnValue('2');
        const request = loadFile('games.json', jsonl(savedGame('first'), savedGame('second')));

        const game = await request.promise;

        expect(game.game_id).toBe('(local) second');
        expect(prompt).toHaveBeenCalledTimes(1);
    });

    it('disambiguates duplicate ids and resolves null when the prompt is cancelled', async () => {
        const prompt = jest.spyOn(window, 'prompt').mockReturnValue(null);
        const request = loadFile('games.jsonl', jsonl(savedGame('same'), savedGame('same')));

        await expect(request.promise).resolves.toBeNull();
        expect(prompt.mock.calls[0][0]).toContain('1) same (1/2)');
        expect(prompt.mock.calls[0][0]).toContain('2) same (2/2)');
    });

    it('rejects non-integer and out-of-range selections', async () => {
        const prompt = jest.spyOn(window, 'prompt')
            .mockReturnValueOnce('2abc')
            .mockReturnValueOnce('3');
        const content = jsonl(savedGame('first'), savedGame('second'));

        await expect(loadFile('games.jsonl', content).promise)
            .rejects.toThrow('Invalid saved game selection "2abc". Enter a whole number from 1 to 2.');
        await expect(loadFile('games.jsonl', content).promise)
            .rejects.toThrow('Invalid saved game selection "3". Enter a whole number from 1 to 2.');
        expect(prompt).toHaveBeenCalledTimes(2);
    });

    it('rejects a malformed later line instead of skipping it', async () => {
        const prompt = jest.spyOn(window, 'prompt');
        const content = JSON.stringify(savedGame('first')) + '\n{"id": broken\n';

        for (const filename of ['games.jsonl', 'games.json']) {
            await expect(loadFile(filename, content).promise)
                .rejects.toThrow(`Unable to parse line 2 of ${filename}`);
        }
        expect(prompt).not.toHaveBeenCalled();
    });

    it('rejects empty input and records with invalid phase data', async () => {
        await expect(loadFile('empty.jsonl', '\n\n').promise)
            .rejects.toThrow('No saved games found in empty.jsonl.');

        const noPhases = savedGame('no-phases');
        noPhases.phases = [];
        await expect(loadFile('no-phases.json', JSON.stringify(noPhases)).promise)
            .rejects.toThrow('Invalid saved game #1 in no-phases.json: expected a nonempty phases array.');

        const noPhaseName = savedGame('no-phase-name');
        delete noPhaseName.phases[0].name;
        delete noPhaseName.phases[0].state.name;
        await expect(loadFile('no-phase-name.json', JSON.stringify(noPhaseName)).promise)
            .rejects.toThrow('phase #1 must have a usable name');

        const noStateObject = savedGame('no-state-object');
        noStateObject.phases[0].state = [];
        await expect(loadFile('no-state-object.json', JSON.stringify(noStateObject)).promise)
            .rejects.toThrow('phase #1 must have an object state');

    });

    it('uses phase names for historical and current states without a state name', async () => {
        const legacy = savedGame('legacy');
        delete legacy.phases[0].state.name;
        legacy.phases.push({name: 'F1901M', state: {name: ''}});

        const game = await loadFile('legacy.json', JSON.stringify(legacy)).promise;

        expect(game.state_history.get('S1901M').name).toBe('S1901M');
        expect(game.phase).toBe('F1901M');
    });

    it('validates later JSONL records before prompting', async () => {
        const prompt = jest.spyOn(window, 'prompt');
        const invalid = savedGame('invalid');
        invalid.phases[0].state = [];

        await expect(loadFile('games.jsonl', jsonl(savedGame('first'), invalid)).promise)
            .rejects.toThrow('Invalid saved game #2');
        expect(prompt).not.toHaveBeenCalled();
    });

    it('rejects FileReader error and abort events', async () => {
        const readerError = startLoad('saved.json');
        readerError.reader.onerror();
        await expect(readerError.promise).rejects.toThrow('Unable to read saved game file saved.json.');

        const readerAbort = startLoad('saved.json');
        readerAbort.reader.onabort();
        await expect(readerAbort.promise).rejects.toThrow('Reading saved game file saved.json was aborted.');
    });

    it('rejects invalid filenames and no file selection with the documented outcomes', async () => {
        const invalidFilename = startLoad('saved.txt');
        await expect(invalidFilename.promise)
            .rejects.toThrow('Invalid saved game filename saved.txt');
        await expect(loadFile('saved.json', '').promise)
            .rejects.toThrow('No saved games found in saved.json.');

        const promise = loadGameFromDisk();
        const input = $.createdInputs[$.createdInputs.length - 1];
        input.changeHandler({target: input});
        await expect(promise).resolves.toBeNull();
    });

    it('rejects when Game construction fails', async () => {
        const broken = savedGame('broken');
        delete broken.map;

        await expect(loadFile('broken.json', JSON.stringify(broken)).promise)
            .rejects.toThrow('map_name');
    });
});
