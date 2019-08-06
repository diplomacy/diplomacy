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

export function getCoordinates(extra) {
    const coordinates = {};
    for (let provinceDefiniton of extra[TAG_PROVINCE_DATA][TAG_PROVINCE]) {
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

export function getSymbolSizes(extra) {
    const sizes = {};
    for (let definition of extra[TAG_ORDERDRAWING][TAG_SYMBOLSIZE]) {
        sizes[definition.name] = {
            width: parseInt(definition.width),
            height: parseInt(definition.height)
        };
    }
    return sizes;
}

export function getColors(extra) {
    const colors = {};
    for (let definition of extra[TAG_ORDERDRAWING][TAG_POWERCOLORS][TAG_POWERCOLOR]) {
        colors[definition.power.toUpperCase()] = definition.color;
    }
    return colors;
}

export function offset(floatString, offset) {
    return "" + (parseFloat(floatString) + offset);
}

export function setInfluence(classes, mapData, loc, power_name) {
    const province = mapData.getProvince(loc);
    if (!province)
        throw new Error(`Unable to find province ${loc}`);
    if (!['LAND', 'COAST'].includes(province.type))
        return;
    const id = province.getID(classes);
    if (!id)
        throw new Error(`Unable to find SVG path for loc ${id}`);
    classes[id] = power_name ? power_name.toLowerCase() : 'nopower';
}

export function getClickedID(event) {
    let node = event.target;
    if (!node.id && node.parentNode.id && node.parentNode.tagName === 'g')
        node = node.parentNode;
    let id = node.id;
    return id ? id.substr(0, 3) : null;
}

export function parseLocation(txt) {
    if (txt.length > 2 && txt[1] === ' ' && ['A', 'F'].includes(txt[0]))
        return txt.substr(2);
    return txt;
}