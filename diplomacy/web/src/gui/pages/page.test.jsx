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
import {Page} from "./page";
import {loadGameFromDisk} from "../utils/load_game_from_disk";

jest.mock("../utils/load_game_from_disk", () => ({
    loadGameFromDisk: jest.fn()
}));

describe('Page.loadGameFromDisk', () => {
    it('does not navigate or report an error when the load is cancelled', async () => {
        loadGameFromDisk.mockResolvedValue(null);
        const page = new Page({});
        page.load = jest.fn();
        page.error = jest.fn();

        await page.loadGameFromDisk();

        expect(page.load).not.toHaveBeenCalled();
        expect(page.error).not.toHaveBeenCalled();
    });
});
