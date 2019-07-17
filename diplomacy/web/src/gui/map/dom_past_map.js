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

export class DOMPastMap {

    constructor(svgElement, onHover) {
        this.svg = svgElement;
        this.cbHover = onHover;
        this.game = null;
        this.orders = null;
        this.mapData = null;
        this.onProvinceHover = this.onProvinceHover.bind(this);
        this.onLabelHover = this.onLabelHover.bind(this);
        this.onUnitHover = this.onUnitHover.bind(this);
    }

    provinceNameToMapID(name) {
        return `_${name.toLowerCase()}___${this.svg.parentNode.id}`;
    }

    mapID(id) {
        return `${id}___${this.svg.parentNode.id}`;
    }

    onHover(name) {
        const orders = [];
        if (this.orders) {
            for (let powerOrders of Object.values(this.orders)) {
                if (powerOrders) {
                    for (let order of powerOrders) {
                        const pieces = order.split(/ +/);
                        if (pieces[1].slice(0, 3) === name.toUpperCase().slice(0, 3))
                            orders.push(order);
                    }
                }
            }
        }
        return orders;
    }

    handleSvgPath(svgPath) {
        const province = this.mapData.getProvince(svgPath.id);
        if (province) {
            this.cbHover(province.name, this.onHover(province.name));
        }
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

    onProvinceHover(event) {
        this.handleSvgPath(event.target);
    }

    onLabelHover(event) {
        const province = this.mapData.getProvince(event.target.textContent);
        if (province) {
            const path = this.getPathFromProvince(province);
            if (path)
                this.handleSvgPath(path);
        }
    }

    onUnitHover(event) {
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

    update(game, mapData, orders) {
        this.game = game;
        this.mapData = mapData;
        this.orders = orders;
        // I don't yet know why I should place this here. Maybe because unit are re-rendered manually at every reloading ?
        $(`#${this.svg.parentNode.id} svg use[diplomacyUnit]`).hover(this.onUnitHover);
    }

    init(game, mapData, orders) {
        $(`#${this.svg.parentNode.id} svg path`).hover(this.onProvinceHover).mouseleave(() => this.cbHover(null, null));
        $(`#${this.mapID('BriefLabelLayer')} text`).hover(this.onLabelHover);
        this.update(game, mapData, orders);
    }

}
