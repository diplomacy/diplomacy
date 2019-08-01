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
import {SvgStandardExtra} from "./SvgStandardExtra";

const TAG_ORDERDRAWING = 'jdipNS:ORDERDRAWING';
const TAG_POWERCOLORS = 'jdipNS:POWERCOLORS';
const TAG_POWERCOLOR = 'jdipNS:POWERCOLOR';
const TAG_SYMBOLSIZE = 'jdipNS:SYMBOLSIZE';
const TAG_PROVINCE_DATA = 'jdipNS:PROVINCE_DATA';
const TAG_PROVINCE = 'jdipNS:PROVINCE';
const TAG_UNIT = 'jdipNS:UNIT';
const TAG_DISLODGED_UNIT = 'jdipNS:DISLODGED_UNIT';
const TAG_SUPPLY_CENTER = 'jdipNS:SUPPLY_CENTER';

export const ARMY = 'Army';
export const FLEET = 'Fleet';

function getCoordinates() {
    const coordinates = {};
    for (let provinceDefiniton of SvgStandardExtra[TAG_PROVINCE_DATA][TAG_PROVINCE]) {
        const name = provinceDefiniton.name.toUpperCase().replace('-', '/');
        coordinates[name] = {};
        if (provinceDefiniton.hasOwnProperty(TAG_UNIT)) {
            coordinates[name].unit = [provinceDefiniton[TAG_UNIT]['x'], provinceDefiniton[TAG_UNIT]['y']];
        }
        if (provinceDefiniton.hasOwnProperty(TAG_DISLODGED_UNIT)) {
            coordinates[name].disl = [provinceDefiniton[TAG_DISLODGED_UNIT]['x'], provinceDefiniton[TAG_DISLODGED_UNIT]['y']];
        }
        if (provinceDefiniton.hasOwnProperty(TAG_SUPPLY_CENTER)) {
            coordinates[name].sc = [provinceDefiniton[TAG_SUPPLY_CENTER]['x'], provinceDefiniton[TAG_SUPPLY_CENTER]['y']];
        }
    }
    return coordinates;
}

function getSymbolSizes() {
    const sizes = {};
    for (let definition of SvgStandardExtra[TAG_ORDERDRAWING][TAG_SYMBOLSIZE]) {
        sizes[definition.name] = {
            width: parseInt(definition.width),
            height: parseInt(definition.height)
        };
    }
    return sizes;
}

function getColors() {
    const colors = {};
    for (let definition of SvgStandardExtra[TAG_ORDERDRAWING][TAG_POWERCOLORS][TAG_POWERCOLOR]) {
        colors[definition.power.toUpperCase()] = definition.color;
    }
    return colors;
}

export const Coordinates = getCoordinates();
export const SymbolSizes = getSymbolSizes();
export const Colors = getColors();

export function offset(floatString, offset) {
    return "" + (parseFloat(floatString) + offset);
}
