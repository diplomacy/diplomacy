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
import {UTILS} from "../../diplomacy/utils/utils";
import $ from "jquery";
import {extendOrderBuilding} from "../utils/order_building";
import {Diplog} from "../../diplomacy/utils/diplog";

function parseLocation(txt) {
    if (txt.length > 2 && txt[1] === ' ' && ['A', 'F'].includes(txt[0]))
        return txt.substr(2);
    return txt;
}

export class DOMOrderBuilder {

    constructor(svgElement, onOrderBuilding, onOrderBuilt, onSelectLocation, onSelectVia, onError) {
        this.svg = svgElement;
        this.cbOrderBuilding = onOrderBuilding;
        this.cbOrderBuilt = onOrderBuilt;
        this.cbSelectLocation = onSelectLocation;
        this.cbSelectVia = onSelectVia;
        this.cbError = onError;

        this.game = null;
        this.mapData = null;
        this.orderBuilding = null;

        this.provinceColors = {};
        this.clickedID = null;
        this.clickedNeighbors = [];

        this.onProvinceClick = this.onProvinceClick.bind(this);
        this.onLabelClick = this.onLabelClick.bind(this);
        this.onUnitClick = this.onUnitClick.bind(this);
    }

    saveProvinceColors() {
        // Get province colors.
        const elements = this.svg.getElementsByTagName('path');
        for (let element of elements) {
            this.provinceColors[element.id] = element.getAttribute('class');
        }
    }

    provinceNameToMapID(name) {
        return `_${name.toLowerCase()}___${this.svg.parentNode.id}`;
    }

    mapID(id) {
        return `${id}___${this.svg.parentNode.id}`;
    }

    onOrderBuilding(svgPath, powerName, orderPath) {
        this.cbOrderBuilding(powerName, orderPath);
    }

    onOrderBuilt(svgPath, powerName, orderString) {
        this.cbOrderBuilt(powerName, orderString);
    }

    onError(svgPath, error) {
        this.cbError(error.toString());
    }

    handleSvgPath(svgPath) {
        const orderBuilding = this.orderBuilding;
        if (!orderBuilding.builder)
            return this.onError(svgPath, 'No orderable locations.');

        const province = this.mapData.getProvince(svgPath.id);
        if (!province)
            return;

        const stepLength = orderBuilding.builder.steps.length;
        if (orderBuilding.path.length >= stepLength)
            throw new Error(`Order building: current steps count (${orderBuilding.path.length}) should be less than` +
                ` expected steps count (${stepLength}) (${orderBuilding.path.join(', ')}).`);

        const lengthAfterClick = orderBuilding.path.length + 1;
        let validLocations = [];
        const testedPath = [orderBuilding.type].concat(orderBuilding.path);
        const value = UTILS.javascript.getTreeValue(this.game.ordersTree, testedPath);
        if (value !== null) {
            const checker = orderBuilding.builder.steps[lengthAfterClick - 1];
            try {
                const possibleLocations = checker(province, orderBuilding.power);
                for (let possibleLocation of possibleLocations) {
                    possibleLocation = possibleLocation.toUpperCase();
                    if (value.includes(possibleLocation))
                        validLocations.push(possibleLocation);
                }
            } catch (error) {
                return this.onError(svgPath, error);
            }
        }
        if (!validLocations.length)
            return this.onError(svgPath, 'Disallowed.');

        if (validLocations.length > 1 && orderBuilding.type === 'S' && orderBuilding.path.length >= 2) {
            // We are building a support order and we have a multiple choice for a location.
            // Let's check if next location to choose is a coast. To have a coast:
            // - all possible locations must start with same 3 characters.
            // - we expect at least province name in possible locations (e.g. 'SPA' for 'SPA/NC').
            // If we have a coast, we will remove province name from possible locations.
            let isACoast = true;
            let validLocationsNoProvinceName = [];
            for (let i = 0; i < validLocations.length; ++i) {
                let location = validLocations[i];
                if (i > 0) {
                    // Compare 3 first letters with previous location.
                    if (validLocations[i - 1].substring(0, 3).toUpperCase() !== validLocations[i].substring(0, 3).toUpperCase()) {
                        // No same prefix with previous location. We does not have a coast.
                        isACoast = false;
                        break;
                    }
                }
                if (location.length !== 3)
                    validLocationsNoProvinceName.push(location);
            }
            if (validLocations.length === validLocationsNoProvinceName.length) {
                // We have not found province name.
                isACoast = false;
            }
            if (isACoast) {
                // We want to choose location in a coastal province. Let's remove province name.
                validLocations = validLocationsNoProvinceName;
            }
        }

        if (validLocations.length > 1) {
            if (this.cbSelectLocation) {
                return this.cbSelectLocation(validLocations, orderBuilding.power, orderBuilding.type, orderBuilding.path);
            } else {
                Diplog.warn(`Forced to select first valid location.`);
                validLocations = [validLocations[0]];
            }
        }
        let orderBuildingType = orderBuilding.type;
        if (lengthAfterClick === stepLength && orderBuildingType === 'M') {
            const moveOrderPath = ['M'].concat(orderBuilding.path, validLocations[0]);
            const moveTypes = UTILS.javascript.getTreeValue(this.game.ordersTree, moveOrderPath);
            if (moveTypes !== null) {
                if (moveTypes.length === 2) {
                    // This move can be done either regularly or VIA a fleet. Let user choose.
                    return this.cbSelectVia(validLocations[0], orderBuilding.power, orderBuilding.path);
                } else {
                    orderBuildingType = moveTypes[0];
                }
            }
        }
        this.clickedID = svgPath.id;

        this.cleanBuildingView();
        if (lengthAfterClick < stepLength)
            this.renderBuildingView(validLocations[0]);
        extendOrderBuilding(
            orderBuilding.power, orderBuildingType, orderBuilding.path, validLocations[0],
            this.cbOrderBuilding, this.cbOrderBuilt, this.cbError
        );

    }

    getPathFromProvince(province) {
        let path = this.svg.getElementById(this.provinceNameToMapID(province.name));
        if (!path) {
            for (let alias of province.aliases) {
                path = this.svg.getElementById(this.provinceNameToMapID(alias));
                if (path)
                    break;
            }
        }
        return path;
    }

    onProvinceClick(event) {
        this.handleSvgPath(event.target);
    }

    onLabelClick(event) {
        const province = this.mapData.getProvince(event.target.textContent);
        if (province) {
            const path = this.getPathFromProvince(province);
            if (path)
                this.handleSvgPath(path);
        }
    }

    onUnitClick(event) {
        const province = this.mapData.getProvince(event.target.getAttribute('diplomacyUnit'));
        if (province) {
            let path = this.getPathFromProvince(province);
            if (!path && province.isCoast())
                path = this.svg.getElementById(this.provinceNameToMapID(province.parent.name));
            if (path) {
                this.handleSvgPath(path);
            }
        }
    }

    cleanBuildingView() {
        if (this.clickedID) {
            const path = this.svg.getElementById(this.clickedID);
            if (path)
                path.setAttribute('class', this.provinceColors[this.clickedID]);
        }
        for (let neighborName of this.clickedNeighbors) {
            const province = this.mapData.getProvince(neighborName);
            if (!province)
                continue;
            const path = this.getPathFromProvince(province);
            if (path)
                path.setAttribute('class', this.provinceColors[path.id]);
        }
        this.clickedNeighbors = [];
    }

    renderBuildingView(extraLocation) {
        if (this.clickedID) {
            const path = this.svg.getElementById(this.clickedID);
            if (path)
                path.setAttribute('class', 'provinceRed');
        }
        const selectedPath = [this.orderBuilding.type].concat(this.orderBuilding.path);
        if (extraLocation)
            selectedPath.push(extraLocation);
        const possibleNeighbors = UTILS.javascript.getTreeValue(this.game.ordersTree, selectedPath);
        if (!possibleNeighbors)
            return;
        this.clickedNeighbors = possibleNeighbors.map(neighbor => parseLocation(neighbor));
        if (this.clickedNeighbors.length) {
            for (let neighbor of this.clickedNeighbors) {
                let neighborProvince = this.mapData.getProvince(neighbor);
                if (!neighborProvince)
                    throw new Error('Unknown neighbor province ' + neighbor);
                let path = this.getPathFromProvince(neighborProvince);
                if (!path && neighborProvince.isCoast())
                    path = this.getPathFromProvince(neighborProvince.parent);
                if (!path)
                    throw new Error(`Unable to find SVG path related to province ${neighborProvince.name}.`);
                path.setAttribute('class', neighborProvince.isWater() ? 'provinceBlue' : 'provinceGreen');
            }
        }
    }

    update(game, mapData, orderBuilding) {
        this.game = game;
        this.mapData = mapData;
        this.orderBuilding = orderBuilding;
        this.saveProvinceColors();
        // If there is a building path, then we are building, so we don't clean anything.
        this.cleanBuildingView();
        if (this.orderBuilding.path.length)
            this.renderBuildingView();
        // I don't yet know why I should place this here. Maybe because unit are re-rendered manually at every reloading ?
        $(`#${this.svg.parentNode.id} svg use[diplomacyUnit]`).click(this.onUnitClick);
    }

    init(game, mapData, orderBuilding) {
        $(`#${this.svg.parentNode.id} svg path`).click(this.onProvinceClick);
        $(`#${this.mapID('BriefLabelLayer')} text`).click(this.onLabelClick);
        this.update(game, mapData, orderBuilding);
    }

}
