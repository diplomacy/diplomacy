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
import React from "react";
import Scrollchor from 'react-scrollchor';
import {SelectLocationForm} from "../forms/select_location_form";
import {SelectViaForm} from "../forms/select_via_form";
import {Order} from "../utils/order";
import {Button} from "../../core/widgets";
import {Bar, Row} from "../../core/layouts";
import {Content} from "../../core/content";
import {Tab, Tabs} from "../../core/tabs";
import {Map} from "../map/map";
import {extendOrderBuilding, ORDER_BUILDER, POSSIBLE_ORDERS} from "../utils/order_building";
import {PowerActionsForm} from "../forms/power_actions_form";
import {MessageForm} from "../forms/message_form";
import {UTILS} from "../../../diplomacy/utils/utils";
import {Message} from "../../../diplomacy/engine/message";
import {PowerOrder} from "../widgets/power_order";
import {MessageView} from "../widgets/message_view";
import {STRINGS} from "../../../diplomacy/utils/strings";
import {Diplog} from "../../../diplomacy/utils/diplog";
import {Table} from "../../core/table";
import {PowerView} from "../utils/power_view";
import {FancyBox} from "../../core/fancybox";
import {DipStorage} from "../utils/dipStorage";

const HotKey = require('react-shortcut');

/* Order management in game page.
 * When editing orders locally, we have to compare it to server orders
 * to determine when we need to update orders on server side. There are
 * 9 comparison cases, depending on orders:
 * SERVER    LOCAL      DECISION
 * null      null       0 (same)
 * null      {}         1 (different, user wants to send "no orders" on server)
 * null      {orders}   1 (different, user defines new orders locally)
 * {}        null       0 (assumed same: user is not allowed to "delete" a "no orders": he can only add new orders)
 * {}        {}         0 (same)
 * {}        {orders}   1 (different, user defines new orders locally and wants to overwrite the "no-orders" on server)
 * {orders}  null       1 (different, user wants to delete all server orders, will result to "no-orders")
 * {orders}  {}         1 (different, user wants to delete all server orders, will result to "no-orders")
 * {orders}  {orders}   same if we have exactly same orders on both server and local
  * */

const TABLE_POWER_VIEW = {
    name: ['Power', 0],
    controller: ['Controller', 1],
    order_is_set: ['With orders', 2],
    wait: ['Waiting', 3]
};

function Help() {
    return (
        <div>
            <p>When building an order, press <strong>ESC</strong> to reset build.</p>
            <p>Press letter associated to an order type to start building an order of this type.
                <br/> Order type letter is indicated in order type name after order type radio button.
            </p>
            <p>In Phase History tab, use keyboard left and right arrows to navigate in past phases.</p>
        </div>
    );
}

export class ContentGame extends Content {

    constructor(props) {
        super(props);
        // Load local orders from local storage (if available).
        const savedOrders = this.props.data.client ? DipStorage.getUserGameOrders(
            this.props.data.client.channel.username,
            this.props.data.game_id,
            this.props.data.phase
        ) : null;
        let orders = null;
        if (savedOrders) {
            orders = {};
            for (let entry of Object.entries(savedOrders)) {
                let powerOrders = null;
                const powerName = entry[0];
                if (entry[1]) {
                    powerOrders = {};
                    for (let orderString of entry[1]) {
                        const order = new Order(orderString, true);
                        powerOrders[order.loc] = order;
                    }
                }
                orders[powerName] = powerOrders;
            }
        }
        this.schedule_timeout_id = null;
        this.state = {
            tabMain: null,
            tabPastMessages: null,
            tabCurrentMessages: null,
            messageHighlights: {},
            historyPhaseIndex: null,
            historyShowOrders: true,
            historySubView: 0,
            historyCurrentLoc: null,
            historyCurrentOrders: null,
            wait: null, // {power name => bool}
            orders: orders, // {power name => {loc => {local: bool, order: str}}}
            power: null,
            orderBuildingType: null,
            orderBuildingPath: [],
            fancy_title: null,
            fancy_function: null,
            on_fancy_close: null,
        };

        // Bind some class methods to this instance.
        this.closeFancyBox = this.closeFancyBox.bind(this);
        this.displayFirstPastPhase = this.displayFirstPastPhase.bind(this);
        this.displayLastPastPhase = this.displayLastPastPhase.bind(this);
        this.displayLocationOrders = this.displayLocationOrders.bind(this);
        this.getMapInfo = this.getMapInfo.bind(this);
        this.notifiedGamePhaseUpdated = this.notifiedGamePhaseUpdated.bind(this);
        this.notifiedLocalStateChange = this.notifiedLocalStateChange.bind(this);
        this.notifiedNetworkGame = this.notifiedNetworkGame.bind(this);
        this.notifiedNewGameMessage = this.notifiedNewGameMessage.bind(this);
        this.notifiedPowersControllers = this.notifiedPowersControllers.bind(this);
        this.onChangeCurrentPower = this.onChangeCurrentPower.bind(this);
        this.onChangeMainTab = this.onChangeMainTab.bind(this);
        this.onChangeOrderType = this.onChangeOrderType.bind(this);
        this.onChangePastPhase = this.onChangePastPhase.bind(this);
        this.onChangePastPhaseIndex = this.onChangePastPhaseIndex.bind(this);
        this.onChangeShowPastOrders = this.onChangeShowPastOrders.bind(this);
        this.onChangeTabCurrentMessages = this.onChangeTabCurrentMessages.bind(this);
        this.onChangeTabPastMessages = this.onChangeTabPastMessages.bind(this);
        this.onClickMessage = this.onClickMessage.bind(this);
        this.onDecrementPastPhase = this.onDecrementPastPhase.bind(this);
        this.onIncrementPastPhase = this.onIncrementPastPhase.bind(this);
        this.onOrderBuilding = this.onOrderBuilding.bind(this);
        this.onOrderBuilt = this.onOrderBuilt.bind(this);
        this.onProcessGame = this.onProcessGame.bind(this);
        this.onRemoveAllOrders = this.onRemoveAllOrders.bind(this);
        this.onRemoveOrder = this.onRemoveOrder.bind(this);
        this.onSelectLocation = this.onSelectLocation.bind(this);
        this.onSelectVia = this.onSelectVia.bind(this);
        this.onSetNoOrders = this.onSetNoOrders.bind(this);
        this.reloadServerOrders = this.reloadServerOrders.bind(this);
        this.renderOrders = this.renderOrders.bind(this);
        this.sendMessage = this.sendMessage.bind(this);
        this.setOrders = this.setOrders.bind(this);
        this.setSelectedLocation = this.setSelectedLocation.bind(this);
        this.setSelectedVia = this.setSelectedVia.bind(this);
        this.setWaitFlag = this.setWaitFlag.bind(this);
        this.vote = this.vote.bind(this);
    }

    static gameTitle(game) {
        let title = `${game.game_id} | ${game.phase} | ${game.status} | ${game.role} | ${game.map_name}`;
        const remainingTime = game.deadline_timer;
        if (remainingTime === undefined)
            title += ` (deadline: ${game.deadline} sec)`;
        else if (remainingTime)
            title += ` (remaining ${remainingTime} sec)`;
        return title;
    }

    static saveGameToDisk(game, page) {
        if (game.client) {
            game.client.save()
                .then((savedData) => {
                    const domLink = document.createElement('a');
                    domLink.setAttribute(
                        'href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(JSON.stringify(savedData)));
                    domLink.setAttribute('download', `${game.game_id}.json`);
                    domLink.style.display = 'none';
                    document.body.appendChild(domLink);
                    domLink.click();
                    document.body.removeChild(domLink);
                })
                .catch(exc => page.error(`Error while saving game: ${exc.toString()}`));
        } else {
            page.error(`Cannot save this game.`);
        }
    }

    static builder(page, data) {
        return {
            title: ContentGame.gameTitle(data),
            navigation: [
                ['Help', () => page.loadFancyBox('Help', () => <Help/>)],
                ['Load a game from disk', page.loadGameFromDisk],
                ['Save game to disk', () => ContentGame.saveGameToDisk(data)],
                [`${UTILS.html.UNICODE_SMALL_LEFT_ARROW} Games`, page.loadGames],
                [`${UTILS.html.UNICODE_SMALL_LEFT_ARROW} Leave game`, () => page.leaveGame(data.game_id)],
                [`${UTILS.html.UNICODE_SMALL_LEFT_ARROW} Logout`, page.logout]
            ],
            component: <ContentGame page={page} data={data}/>
        };
    }

    static getServerWaitFlags(engine) {
        const wait = {};
        const controllablePowers = engine.getControllablePowers();
        for (let powerName of controllablePowers) {
            wait[powerName] = engine.powers[powerName].wait;
        }
        return wait;
    }

    static getServerOrders(engine) {
        const orders = {};
        const controllablePowers = engine.getControllablePowers();
        for (let powerName of controllablePowers) {
            const powerOrders = {};
            let countOrders = 0;
            const power = engine.powers[powerName];
            for (let orderString of power.orders) {
                const serverOrder = new Order(orderString, false);
                powerOrders[serverOrder.loc] = serverOrder;
                ++countOrders;
            }
            orders[powerName] = (countOrders || power.order_is_set) ? powerOrders : null;
        }
        return orders;
    }

    static getOrderBuilding(powerName, orderType, orderPath) {
        return {
            type: orderType,
            path: orderPath,
            power: powerName,
            builder: orderType && ORDER_BUILDER[orderType]
        };
    }

    closeFancyBox() {
        this.setState({
            fancy_title: null,
            fancy_function: null,
            on_fancy_close: null,
            orderBuildingPath: []
        });
    }

    setSelectedLocation(location, powerName, orderType, orderPath) {
        if (!location)
            return;
        extendOrderBuilding(
            powerName, orderType, orderPath, location,
            this.onOrderBuilding, this.onOrderBuilt, this.getPage().error
        );
        this.setState({
            fancy_title: null,
            fancy_function: null,
            on_fancy_close: null
        });
    }

    setSelectedVia(moveType, powerName, orderPath, location) {
        if (!moveType || !['M', 'V'].includes(moveType))
            return;
        extendOrderBuilding(
            powerName, moveType, orderPath, location,
            this.onOrderBuilding, this.onOrderBuilt, this.getPage().error
        );
        this.setState({
            fancy_title: null,
            fancy_function: null,
            on_fancy_close: null
        });
    }

    onSelectLocation(possibleLocations, powerName, orderType, orderPath) {
        const title = `Select location to continue building order: ${orderPath.join(' ')} ... (press ESC or close button to cancel building)`;
        const func = () => (<SelectLocationForm locations={possibleLocations}
                                                onSelect={(location) => this.setSelectedLocation(location, powerName, orderType, orderPath)}/>);
        this.setState({
            fancy_title: title,
            fancy_function: func,
            on_fancy_close: this.closeFancyBox
        });
    }

    onSelectVia(location, powerName, orderPath) {
        const title = `Select move type for move order: ${orderPath.join(' ')}`;
        const func = () => (
            <SelectViaForm onSelect={(moveType) => this.setSelectedVia(moveType, powerName, orderPath, location)}/>);
        this.setState({
            fancy_title: title,
            fancy_function: func,
            on_fancy_close: this.closeFancyBox
        });
    }

    __get_orders(engine) {
        const orders = ContentGame.getServerOrders(engine);
        if (this.state.orders) {
            for (let powerName of Object.keys(orders)) {
                const serverPowerOrders = orders[powerName];
                const localPowerOrders = this.state.orders[powerName];
                if (localPowerOrders) {
                    for (let localOrder of Object.values(localPowerOrders)) {
                        localOrder.local = (
                            !serverPowerOrders
                            || !serverPowerOrders.hasOwnProperty(localOrder.loc)
                            || serverPowerOrders[localOrder.loc].order !== localOrder.order
                        );
                    }
                }
                orders[powerName] = localPowerOrders;
            }
        }
        return orders;
    }

    __get_wait(engine) {
        return this.state.wait ? this.state.wait : ContentGame.getServerWaitFlags(engine);
    }

    getMapInfo() {
        return this.props.page.availableMaps[this.props.data.map_name];
    }

    clearScheduleTimeout() {
        if (this.schedule_timeout_id) {
            clearInterval(this.schedule_timeout_id);
            this.schedule_timeout_id = null;
        }
    }

    updateDeadlineTimer() {
        const engine = this.props.data;
        --engine.deadline_timer;
        if (engine.deadline_timer <= 0) {
            engine.deadline_timer = 0;
            this.clearScheduleTimeout();
        }
        this.getPage().setTitle(ContentGame.gameTitle(engine));
    }

    reloadDeadlineTimer(networkGame) {
        networkGame.querySchedule()
            .then(dataSchedule => {
                const schedule = dataSchedule.schedule;
                const server_current = schedule.current_time;
                const server_end = schedule.time_added + schedule.delay;
                const server_remaining = server_end - server_current;
                this.props.data.deadline_timer = server_remaining * schedule.time_unit;
                if (!this.schedule_timeout_id)
                    this.schedule_timeout_id = setInterval(() => this.updateDeadlineTimer(), schedule.time_unit * 1000);
            })
            .catch(() => {
                if (this.props.data.hasOwnProperty('deadline_timer'))
                    delete this.props.data.deadline_timer;
                this.clearScheduleTimeout();
                // this.getPage().error(`Error while updating deadline timer: ${error.toString()}`);
            });
    }

    networkGameIsDisplayed(networkGame) {
        return this.getPage().pageIsGame(networkGame.local);
    }

    notifiedNetworkGame(networkGame, notification) {
        if (this.networkGameIsDisplayed(networkGame)) {
            const msg = `Game (${networkGame.local.game_id}) received notification ${notification.name}.`;
            this.props.page.loadGame(networkGame.local, {info: msg});
            this.reloadDeadlineTimer(networkGame);
        }
    }

    notifiedPowersControllers(networkGame, notification) {
        if (networkGame.local.isPlayerGame() && (
            !networkGame.channel.game_id_to_instances.hasOwnProperty(networkGame.local.game_id)
            || !networkGame.channel.game_id_to_instances[networkGame.local.game_id].has(networkGame.local.role)
        )) {
            // This power game is now invalid.
            this.props.page.disconnectGame(networkGame.local.game_id);
            if (this.networkGameIsDisplayed(networkGame)) {
                this.props.page.loadGames(null,
                    {error: `Player game ${networkGame.local.game_id}/${networkGame.local.role} was kicked. Deadline over?`});
            }
        } else {
            this.notifiedNetworkGame(networkGame, notification);
        }
    }

    notifiedGamePhaseUpdated(networkGame, notification) {
        networkGame.getAllPossibleOrders()
            .then(allPossibleOrders => {
                networkGame.local.setPossibleOrders(allPossibleOrders);
                if (this.networkGameIsDisplayed(networkGame)) {
                    this.getPage().loadGame(
                        networkGame.local, {info: `Game update (${notification.name}) to ${networkGame.local.phase}.`}
                    );
                    this.__store_orders(null);
                    this.setState({orders: null, wait: null, messageHighlights: {}});
                    this.reloadDeadlineTimer(networkGame);
                }
            })
            .catch(error => this.getPage().error('Error when updating possible orders: ' + error.toString()));
    }

    notifiedLocalStateChange(networkGame) {
        networkGame.getAllPossibleOrders()
            .then(allPossibleOrders => {
                networkGame.local.setPossibleOrders(allPossibleOrders);
                if (this.networkGameIsDisplayed(networkGame)) {
                    this.getPage().loadGame(
                        networkGame.local, {info: `Possible orders re-loaded.`}
                    );
                    this.reloadDeadlineTimer(networkGame);
                }
            })
            .catch(error => this.getPage().error('Error when updating possible orders: ' + error.toString()));
    }

    notifiedNewGameMessage(networkGame, notification) {
        let protagonist = notification.message.sender;
        if (notification.message.recipient === 'GLOBAL')
            protagonist = notification.message.recipient;
        const messageHighlights = Object.assign({}, this.state.messageHighlights);
        if (!messageHighlights.hasOwnProperty(protagonist))
            messageHighlights[protagonist] = 1;
        else
            ++messageHighlights[protagonist];
        this.setState({messageHighlights: messageHighlights});
        this.notifiedNetworkGame(networkGame, notification);
    }

    bindCallbacks(networkGame) {
        if (!networkGame.callbacksBound) {
            networkGame.addOnClearedCenters(this.notifiedLocalStateChange);
            networkGame.addOnClearedOrders(this.notifiedLocalStateChange);
            networkGame.addOnClearedUnits(this.notifiedLocalStateChange);
            networkGame.addOnPowersControllers(this.notifiedPowersControllers);
            networkGame.addOnGameMessageReceived(this.notifiedNewGameMessage);
            networkGame.addOnGameProcessed(this.notifiedGamePhaseUpdated);
            networkGame.addOnGamePhaseUpdate(this.notifiedGamePhaseUpdated);
            networkGame.addOnGameStatusUpdate(this.notifiedNetworkGame);
            networkGame.addOnOmniscientUpdated(this.notifiedNetworkGame);
            networkGame.addOnPowerOrdersUpdate(this.notifiedNetworkGame);
            networkGame.addOnPowerOrdersFlag(this.notifiedNetworkGame);
            networkGame.addOnPowerVoteUpdated(this.notifiedNetworkGame);
            networkGame.addOnPowerWaitFlag(this.notifiedNetworkGame);
            networkGame.addOnVoteCountUpdated(this.notifiedNetworkGame);
            networkGame.addOnVoteUpdated(this.notifiedNetworkGame);
            networkGame.callbacksBound = true;
            networkGame.local.markAllMessagesRead();
        }
    }

    onChangeCurrentPower(event) {
        this.setState({power: event.target.value});
    }

    onChangeMainTab(tab) {
        this.setState({tabMain: tab});
    }

    onChangeTabCurrentMessages(tab) {
        this.setState({tabCurrentMessages: tab});
    }

    onChangeTabPastMessages(tab) {
        this.setState({tabPastMessages: tab});
    }

    sendMessage(networkGame, recipient, body) {
        const engine = networkGame.local;
        const message = new Message({
            phase: engine.phase,
            sender: engine.role,
            recipient: recipient,
            message: body
        });
        const page = this.props.page;
        networkGame.sendGameMessage({message: message})
            .then(() => {
                page.loadGame(engine, {success: `Message sent: ${JSON.stringify(message)}`});
            })
            .catch(error => page.error(error.toString()));
    }

    __store_orders(orders) {
        // Save local orders into local storage.
        const username = this.props.data.client.channel.username;
        const gameID = this.props.data.game_id;
        const gamePhase = this.props.data.phase;
        if (!orders) {
            return DipStorage.clearUserGameOrders(username, gameID);
        }
        for (let entry of Object.entries(orders)) {
            const powerName = entry[0];
            let powerOrdersList = null;
            if (entry[1]) {
                powerOrdersList = Object.values(entry[1]).map(order => order.order);
            }
            DipStorage.clearUserGameOrders(username, gameID, powerName);
            DipStorage.addUserGameOrders(username, gameID, gamePhase, powerName, powerOrdersList);
        }
    }

    reloadServerOrders() {
        const serverOrders = ContentGame.getServerOrders(this.props.data);
        this.__store_orders(serverOrders);
        this.setState({orders: serverOrders});
    }

    setOrders() {
        const serverOrders = ContentGame.getServerOrders(this.props.data);
        const orders = this.__get_orders(this.props.data);

        for (let entry of Object.entries(orders)) {
            const powerName = entry[0];
            const localPowerOrders = entry[1] ? Object.values(entry[1]).map(orderEntry => orderEntry.order) : null;
            const serverPowerOrders = serverOrders[powerName] ? Object.values(serverOrders[powerName]).map(orderEntry => orderEntry.order) : null;
            let same = false;

            if (serverPowerOrders === null) {
                // No orders set on server.
                if (localPowerOrders === null)
                    same = true;
                // Otherwise, we have local orders set (even empty local orders).
            } else if (serverPowerOrders.length === 0) {
                // Empty orders set on server.
                // If local orders are null or empty, then we assume
                // it's the same thing as empty order set on server.
                if (localPowerOrders === null || !localPowerOrders.length)
                    same = true;
                // Otherwise, we have local non-empty orders set.
            } else {
                // Orders set on server. Identical to local orders only if we have exactly same orders on server and locally.
                if (localPowerOrders && localPowerOrders.length === serverPowerOrders.length) {
                    localPowerOrders.sort();
                    serverPowerOrders.sort();
                    const length = localPowerOrders.length;
                    same = true;
                    for (let i = 0; i < length; ++i) {
                        if (localPowerOrders[i] !== serverPowerOrders[i]) {
                            same = false;
                            break;
                        }
                    }
                }
            }

            if (same) {
                Diplog.warn(`Orders not changed for ${powerName}.`);
                continue;
            }
            Diplog.info('Sending orders for ' + powerName + ': ' + JSON.stringify(localPowerOrders));
            this.props.data.client.setOrders({power_name: powerName, orders: localPowerOrders || []})
                .then(() => {
                    this.props.page.success('Orders sent.');
                })
                .catch(err => {
                    this.props.page.error(err.toString());
                })
                .then(() => {
                    this.reloadServerOrders();
                });
        }
    }

    onProcessGame() {
        this.props.data.client.process()
            .then(() => this.props.page.success('Game processed.'))
            .catch(err => {
                this.props.page.error(err.toString());
            });
    }

    onRemoveOrder(powerName, order) {
        const orders = this.__get_orders(this.props.data);
        if (orders.hasOwnProperty(powerName)
            && orders[powerName].hasOwnProperty(order.loc)
            && orders[powerName][order.loc].order === order.order) {
            delete orders[powerName][order.loc];
            if (!UTILS.javascript.count(orders[powerName]))
                orders[powerName] = null;
            this.__store_orders(orders);
            this.setState({orders: orders});
        }
    }

    onRemoveAllOrders() {
        const orders = {};
        const controllablePowers = this.props.data.getControllablePowers();
        for (let powerName of controllablePowers) {
            orders[powerName] = null;
        }
        this.__store_orders(orders);
        this.setState({orders: orders});
    }

    onOrderBuilding(powerName, path) {
        const pathToSave = path.slice(1);
        this.props.page.success(`Building order ${pathToSave.join(' ')} ...`);
        this.setState({orderBuildingPath: pathToSave});
    }

    onOrderBuilt(powerName, orderString) {
        const state = Object.assign({}, this.state);
        state.orderBuildingPath = [];
        state.fancy_title = null;
        state.fancy_function = null;
        state.on_fancy_close = null;
        if (!orderString) {
            Diplog.warn('No order built.');
            this.setState(state);
            return;
        }
        const engine = this.props.data;
        const localOrder = new Order(orderString, true);
        const allOrders = this.__get_orders(engine);
        if (!allOrders.hasOwnProperty(powerName)) {
            Diplog.warn(`Unknown power ${powerName}.`);
            this.setState(state);
            return;
        }

        if (!allOrders[powerName])
            allOrders[powerName] = {};
        allOrders[powerName][localOrder.loc] = localOrder;
        state.orders = allOrders;
        this.props.page.success(`Built order: ${orderString}`);
        this.__store_orders(allOrders);
        this.setState(state);
    }

    onSetNoOrders(powerName) {
        const orders = this.__get_orders(this.props.data);
        orders[powerName] = {};
        this.__store_orders(orders);
        this.setState({orders: orders});
    }

    onChangeOrderType(form) {
        this.setState({
            orderBuildingType: form.order_type,
            orderBuildingPath: [],
            fancy_title: null,
            fancy_function: null,
            on_fancy_close: null
        });
    }

    vote(decision) {
        const engine = this.props.data;
        const networkGame = engine.client;
        const controllablePowers = engine.getControllablePowers();
        const currentPowerName = this.state.power || (controllablePowers.length ? controllablePowers[0] : null);
        if (!currentPowerName)
            throw new Error(`Internal error: unable to detect current selected power name.`);
        networkGame.vote({power_name: currentPowerName, vote: decision})
            .then(() => this.getPage().success(`Vote set to ${decision} for ${currentPowerName}`))
            .catch(error => {
                Diplog.error(error.stack);
                this.getPage().error(`Error while setting vote for ${currentPowerName}: ${error.toString()}`);
            });
    }

    setWaitFlag(waitFlag) {
        const engine = this.props.data;
        const networkGame = engine.client;
        const controllablePowers = engine.getControllablePowers();
        const currentPowerName = this.state.power || (controllablePowers.length ? controllablePowers[0] : null);
        if (!currentPowerName)
            throw new Error(`Internal error: unable to detect current selected power name.`);
        networkGame.setWait(waitFlag, {power_name: currentPowerName})
            .then(() => this.getPage().success(`Wait flag set to ${waitFlag} for ${currentPowerName}`))
            .catch(error => {
                Diplog.error(error.stack);
                this.getPage().error(`Error while setting wait flag for ${currentPowerName}: ${error.toString()}`);
            });
    }

    __change_past_phase(newPhaseIndex, subView) {
        this.setState({
            historyPhaseIndex: newPhaseIndex,
            historySubView: (subView ? subView : 0),
            historyCurrentLoc: null,
            historyCurrentOrders: null
        });
    }

    onChangePastPhase(event) {
        this.__change_past_phase(event.target.value);
    }

    onChangePastPhaseIndex(increment) {
        const selectObject = document.getElementById('select-past-phase');
        if (selectObject) {
            if (!this.state.historyShowOrders) {
                // We must change map sub-view before showed phase index.
                const currentSubView = this.state.historySubView;
                const newSubView = currentSubView + (increment ? 1 : -1);
                if (newSubView === 0 || newSubView === 1) {
                    // Sub-view correctly updated. We don't yet change showed phase.
                    return this.setState({historySubView: newSubView});
                }
                // Sub-view badly updated (either from 0 to -1, or from 1 to 2). We must change phase.
            }
            // Let's simply increase or decrease index of showed past phase.
            const index = selectObject.selectedIndex;
            const newIndex = index + (increment ? 1 : -1);
            if (newIndex >= 0 && newIndex < selectObject.length) {
                selectObject.selectedIndex = newIndex;
                this.__change_past_phase(parseInt(selectObject.options[newIndex].value, 10), (increment ? 0 : 1));
            }
        }
    }

    onIncrementPastPhase(event) {
        this.onChangePastPhaseIndex(true);
        if (event && event.preventDefault)
            event.preventDefault();
    }

    onDecrementPastPhase(event) {
        this.onChangePastPhaseIndex(false);
        if (event && event.preventDefault)
            event.preventDefault();
    }

    displayFirstPastPhase() {
        this.__change_past_phase(0, 0);
    }

    displayLastPastPhase() {
        this.__change_past_phase(-1, 1);
    }

    onChangeShowPastOrders(event) {
        this.setState({historyShowOrders: event.target.checked, historySubView: 0});
    }

    renderOrders(engine, currentPowerName) {
        const serverOrders = ContentGame.getServerOrders(this.props.data);
        const orders = this.__get_orders(engine);
        const wait = this.__get_wait(engine);

        const render = [];
        render.push(<PowerOrder key={currentPowerName} name={currentPowerName} wait={wait[currentPowerName]}
                                orders={orders[currentPowerName]}
                                serverCount={serverOrders[currentPowerName] ? UTILS.javascript.count(serverOrders[currentPowerName]) : -1}
                                onRemove={this.onRemoveOrder}/>);
        return render;
    }

    onClickMessage(message) {
        if (!message.read) {
            message.read = true;
            let protagonist = message.sender;
            if (message.recipient === 'GLOBAL')
                protagonist = message.recipient;
            this.getPage().loadGame(this.props.data);
            if (this.state.messageHighlights.hasOwnProperty(protagonist) && this.state.messageHighlights[protagonist] > 0) {
                const messageHighlights = Object.assign({}, this.state.messageHighlights);
                --messageHighlights[protagonist];
                this.setState({messageHighlights: messageHighlights});
            }
        }
    }

    displayLocationOrders(loc, orders) {
        this.setState({
            historyCurrentLoc: loc || null,
            historyCurrentOrders: orders && orders.length ? orders : null
        });
    }

    renderPastMessages(engine) {
        const messageChannels = engine.getMessageChannels();
        let tabNames = null;
        if (engine.isPlayerGame()) {
            tabNames = [];
            for (let powerName of Object.keys(engine.powers)) if (powerName !== engine.role)
                tabNames.push(powerName);
            tabNames.sort();
            tabNames.push('GLOBAL');
        } else {
            tabNames = Object.keys(messageChannels);
        }
        const currentTabId = this.state.tabPastMessages || tabNames[0];

        return (
            <div className={'panel-messages'} key={'panel-messages'}>
                {/* Messages. */}
                <Tabs menu={tabNames} titles={tabNames} onChange={this.onChangeTabPastMessages} active={currentTabId}>
                    {tabNames.map(protagonist => (
                        <Tab key={protagonist} className={'game-messages'} display={currentTabId === protagonist}>
                            {(!messageChannels.hasOwnProperty(protagonist) || !messageChannels[protagonist].length ?
                                    (<div className={'no-game-message'}>No
                                        messages{engine.isPlayerGame() ? ` with ${protagonist}` : ''}.</div>) :
                                    messageChannels[protagonist].map((message, index) => (
                                        <MessageView key={index} owner={engine.role} message={message} read={true}/>
                                    ))
                            )}
                        </Tab>
                    ))}
                </Tabs>
            </div>
        );
    }

    renderCurrentMessages(engine) {
        const messageChannels = engine.getMessageChannels();
        let tabNames = null;
        let highlights = null;
        if (engine.isPlayerGame()) {
            tabNames = [];
            for (let powerName of Object.keys(engine.powers)) if (powerName !== engine.role)
                tabNames.push(powerName);
            tabNames.sort();
            tabNames.push('GLOBAL');
            highlights = this.state.messageHighlights;
        } else {
            tabNames = Object.keys(messageChannels);
            let totalHighlights = 0;
            for (let count of Object.values(this.state.messageHighlights))
                totalHighlights += count;
            highlights = {messages: totalHighlights};
        }
        const unreadMarked = new Set();
        const currentTabId = this.state.tabCurrentMessages || tabNames[0];

        return (
            <div className={'panel-messages'} key={'panel-messages'}>
                {/* Messages. */}
                <Tabs menu={tabNames} titles={tabNames} onChange={this.onChangeTabCurrentMessages} active={currentTabId}
                      highlights={highlights}>
                    {tabNames.map(protagonist => (
                        <Tab id={`panel-current-messages-${protagonist}`} key={protagonist} className={'game-messages'}
                             display={currentTabId === protagonist}>
                            {(!messageChannels.hasOwnProperty(protagonist) || !messageChannels[protagonist].length ?
                                    (<div className={'no-game-message'}>No
                                        messages{engine.isPlayerGame() ? ` with ${protagonist}` : ''}.</div>) :
                                    (messageChannels[protagonist].map((message, index) => {
                                        let id = null;
                                        if (!message.read && !unreadMarked.has(protagonist)) {
                                            if (engine.isOmniscientGame() || message.sender !== engine.role) {
                                                unreadMarked.add(protagonist);
                                                id = `${protagonist}-unread`;
                                            }
                                        }
                                        return <MessageView key={index}
                                                            owner={engine.role}
                                                            message={message}
                                                            id={id}
                                                            onClick={this.onClickMessage}/>;
                                    }))
                            )}
                        </Tab>
                    ))}
                </Tabs>
                {/* Link to go to first unread received message. */}
                {unreadMarked.has(currentTabId) && (
                    <Scrollchor className={'link-unread-message'}
                                to={`${currentTabId}-unread`}
                                target={`panel-current-messages-${currentTabId}`}>
                        Go to 1st unread message
                    </Scrollchor>
                )}
                {/* Send form. */}
                {engine.isPlayerGame() && (
                    <MessageForm sender={engine.role} recipient={currentTabId} onSubmit={form =>
                        this.sendMessage(engine.client, currentTabId, form.message)}/>)}
            </div>
        );
    }

    renderPastMap(gameEngine, showOrders) {
        return <Map key={'past-map'}
                    id={'past-map'}
                    game={gameEngine}
                    mapInfo={this.getMapInfo(gameEngine.map_name)}
                    onError={this.getPage().error}
                    onHover={showOrders ? this.displayLocationOrders : null}
                    showOrders={Boolean(showOrders)}
                    orders={(gameEngine.order_history.contains(gameEngine.phase) && gameEngine.order_history.get(gameEngine.phase)) || null}
        />;
    }

    renderCurrentMap(gameEngine, powerName, orderType, orderPath) {
        const rawOrders = this.__get_orders(gameEngine);
        const orders = {};
        for (let entry of Object.entries(rawOrders)) {
            orders[entry[0]] = [];
            if (entry[1]) {
                for (let orderObject of Object.values(entry[1]))
                    orders[entry[0]].push(orderObject.order);
            }
        }
        return <Map key={'current-map'}
                    id={'current-map'}
                    game={gameEngine}
                    mapInfo={this.getMapInfo(gameEngine.map_name)}
                    onError={this.getPage().error}
                    orderBuilding={ContentGame.getOrderBuilding(powerName, orderType, orderPath)}
                    onOrderBuilding={this.onOrderBuilding}
                    onOrderBuilt={this.onOrderBuilt}
                    showOrders={true}
                    orders={orders}
                    onSelectLocation={this.onSelectLocation}
                    onSelectVia={this.onSelectVia}/>;
    }

    renderTabPhaseHistory(toDisplay, initialEngine) {
        const pastPhases = initialEngine.state_history.values().map(state => state.name);
        if (initialEngine.phase === 'COMPLETED') {
            pastPhases.push('COMPLETED');
        }
        let phaseIndex = 0;
        if (initialEngine.displayed) {
            if (this.state.historyPhaseIndex === null || this.state.historyPhaseIndex >= pastPhases.length) {
                phaseIndex = pastPhases.length - 1;
            } else {
                if (this.state.historyPhaseIndex < 0) {
                    phaseIndex = pastPhases.length + this.state.historyPhaseIndex;
                } else {
                    phaseIndex = this.state.historyPhaseIndex;
                }
            }
        }
        const engine = (
            phaseIndex === initialEngine.state_history.size() ?
                initialEngine : initialEngine.cloneAt(initialEngine.state_history.keyFromIndex(phaseIndex))
        );
        let orders = {};
        let orderResult = null;
        if (engine.order_history.contains(engine.phase))
            orders = engine.order_history.get(engine.phase);
        if (engine.result_history.contains(engine.phase))
            orderResult = engine.result_history.get(engine.phase);
        let countOrders = 0;
        for (let powerOrders of Object.values(orders)) {
            if (powerOrders)
                countOrders += powerOrders.length;
        }
        const powerNames = Object.keys(orders);
        powerNames.sort();

        const getOrderResult = (order) => {
            if (orderResult) {
                const pieces = order.split(/ +/);
                const unit = `${pieces[0]} ${pieces[1]}`;
                if (orderResult.hasOwnProperty(unit)) {
                    const resultsToParse = orderResult[unit];
                    if (!resultsToParse.length)
                        resultsToParse.push('');
                    const results = [];
                    for (let r of resultsToParse) {
                        if (results.length)
                            results.push(', ');
                        results.push(<span key={results.length} className={r || 'success'}>{r || 'OK'}</span>);
                    }
                    return <span className={'order-result'}> ({results})</span>;
                }
            }
            return '';
        };

        const orderView = [
            (<form key={1} className={'form-inline mb-4'}>
                <Button title={UTILS.html.UNICODE_LEFT_ARROW} onClick={this.onDecrementPastPhase} pickEvent={true}
                        disabled={phaseIndex === 0}/>
                <div className={'form-group'}>
                    <select className={'form-control custom-select'}
                            id={'select-past-phase'}
                            value={phaseIndex}
                            onChange={this.onChangePastPhase}>
                        {pastPhases.map((phaseName, index) => <option key={index} value={index}>{phaseName}</option>)}
                    </select>
                </div>
                <Button title={UTILS.html.UNICODE_RIGHT_ARROW} onClick={this.onIncrementPastPhase} pickEvent={true}
                        disabled={phaseIndex === pastPhases.length - 1}/>
                <div className={'form-group'}>
                    <input className={'form-check-input'} id={'show-orders'} type={'checkbox'}
                           checked={this.state.historyShowOrders} onChange={this.onChangeShowPastOrders}/>
                    <label className={'form-check-label'} htmlFor={'show-orders'}>Show orders</label>
                </div>
            </form>),
            ((this.state.historyShowOrders && (
                (countOrders && (
                    <div key={2} className={'past-orders container'}>
                        {powerNames.map(powerName => !orders[powerName] || !orders[powerName].length ? '' : (
                            <div key={powerName} className={'row'}>
                                <div className={'past-power-name col-sm-2'}>{powerName}</div>
                                <div className={'past-power-orders col-sm-10'}>
                                    {orders[powerName].map((order, index) => (
                                        <div key={index}>{order}{getOrderResult(order)}</div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                )) || <div key={2} className={'no-orders'}>No orders for this phase!</div>
            )) || '')
        ];
        const messageView = this.renderPastMessages(engine);

        let detailsView = null;
        if (this.state.historyShowOrders && countOrders) {
            detailsView = (
                <Row>
                    <div className={'col-sm-6'}>{orderView}</div>
                    <div className={'col-sm-6'}>{messageView}</div>
                </Row>
            );
        } else {
            detailsView = orderView.slice();
            detailsView.push(messageView);
        }

        return (
            <Tab id={'tab-phase-history'} display={toDisplay}>
                <Row>
                    <div className={'col-xl'}>
                        {this.state.historyCurrentOrders && (
                            <div className={'history-current-orders'}>{this.state.historyCurrentOrders.join(', ')}</div>
                        )}
                        {this.renderPastMap(engine, this.state.historyShowOrders || this.state.historySubView)}
                    </div>
                    <div className={'col-xl'}>{detailsView}</div>
                </Row>
                {toDisplay && <HotKey keys={['arrowleft']} onKeysCoincide={this.onDecrementPastPhase}/>}
                {toDisplay && <HotKey keys={['arrowright']} onKeysCoincide={this.onIncrementPastPhase}/>}
                {toDisplay && <HotKey keys={['home']} onKeysCoincide={this.displayFirstPastPhase}/>}
                {toDisplay && <HotKey keys={['end']} onKeysCoincide={this.displayLastPastPhase}/>}
            </Tab>
        );
    }

    renderTabCurrentPhase(toDisplay, engine, powerName, orderType, orderPath) {
        const powerNames = Object.keys(engine.powers);
        powerNames.sort();
        const orderedPowers = powerNames.map(pn => engine.powers[pn]);
        return (
            <Tab id={'tab-current-phase'} display={toDisplay}>
                <Row>
                    <div className={'col-xl'}>
                        {this.renderCurrentMap(engine, powerName, orderType, orderPath)}
                    </div>
                    <div className={'col-xl'}>
                        {/* Orders. */}
                        <div className={'panel-orders mb-4'}>
                            <Bar className={'p-2'}>
                                <strong className={'mr-4'}>Orders:</strong>
                                <Button title={'reset'} onClick={this.reloadServerOrders}/>
                                <Button title={'delete all'} onClick={this.onRemoveAllOrders}/>
                                <Button color={'primary'} title={'update'} onClick={this.setOrders}/>
                                {(!this.props.data.isPlayerGame() && this.props.data.observer_level === STRINGS.MASTER_TYPE &&
                                    <Button color={'danger'} title={'process game'}
                                            onClick={this.onProcessGame}/>) || ''}
                            </Bar>
                            <div className={'orders'}>{this.renderOrders(this.props.data, powerName)}</div>
                            <div className={'table-responsive'}>
                                <Table className={'table table-striped table-sm'}
                                       caption={'Powers info'}
                                       columns={TABLE_POWER_VIEW}
                                       data={orderedPowers}
                                       wrapper={PowerView.wrap}/>
                            </div>
                        </div>
                        {/* Messages. */}
                        {this.renderCurrentMessages(engine)}
                    </div>
                </Row>
            </Tab>
        );
    }

    render() {
        const engine = this.props.data;
        const phaseType = engine.getPhaseType();
        const controllablePowers = engine.getControllablePowers();
        if (this.props.data.client)
            this.bindCallbacks(this.props.data.client);

        if (engine.phase === 'FORMING')
            return <main>
                <div className={'forming'}>Game not yet started!</div>
            </main>;

        const tabNames = [];
        const tabTitles = [];
        let hasTabPhaseHistory = false;
        let hasTabCurrentPhase = false;
        if (engine.state_history.size()) {
            hasTabPhaseHistory = true;
            tabNames.push('phase_history');
            tabTitles.push('Phase history');
        }
        if (controllablePowers.length && phaseType) {
            hasTabCurrentPhase = true;
            tabNames.push('current_phase');
            tabTitles.push('Current phase');
        }
        if (!tabNames.length) {
            // This should never happen, but let's display this message.
            return <main>
                <div className={'no-data'}>No data in this game!</div>
            </main>;
        }
        const mainTab = this.state.tabMain && tabNames.includes(this.state.tabMain) ? this.state.tabMain : tabNames[tabNames.length - 1];

        const currentPowerName = this.state.power || (controllablePowers.length && controllablePowers[0]);
        let currentPower = null;
        let orderTypeToLocs = null;
        let allowedPowerOrderTypes = null;
        let orderBuildingType = null;
        let buildCount = null;
        if (hasTabCurrentPhase) {
            currentPower = engine.getPower(currentPowerName);
            orderTypeToLocs = engine.getOrderTypeToLocs(currentPowerName);
            allowedPowerOrderTypes = Object.keys(orderTypeToLocs);
            // canOrder = allowedPowerOrderTypes.length
            if (allowedPowerOrderTypes.length) {
                POSSIBLE_ORDERS.sortOrderTypes(allowedPowerOrderTypes, phaseType);
                if (this.state.orderBuildingType && allowedPowerOrderTypes.includes(this.state.orderBuildingType))
                    orderBuildingType = this.state.orderBuildingType;
                else
                    orderBuildingType = allowedPowerOrderTypes[0];
            }
            buildCount = engine.getBuildsCount(currentPowerName);
        }

        return (
            <main>
                {(hasTabCurrentPhase && (
                    <div className={'row align-items-center mb-3'}>
                        <div className={'col-sm-2'}>
                            {(controllablePowers.length === 1 &&
                                <div className={'power-name'}>{controllablePowers[0]}</div>) || (
                                <select className={'form-control custom-select'} id={'current-power'}
                                        value={currentPowerName} onChange={this.onChangeCurrentPower}>
                                    {controllablePowers.map(
                                        powerName => <option key={powerName} value={powerName}>{powerName}</option>)}
                                </select>
                            )}
                        </div>
                        <div className={'col-sm-10'}>
                            <PowerActionsForm orderType={orderBuildingType}
                                              orderTypes={allowedPowerOrderTypes}
                                              onChange={this.onChangeOrderType}
                                              onNoOrders={() => this.onSetNoOrders(currentPowerName)}
                                              onSetWaitFlag={() => this.setWaitFlag(!currentPower.wait)}
                                              onVote={this.vote}
                                              role={engine.role}
                                              power={currentPower}/>
                        </div>
                    </div>
                )) || ''}
                {(hasTabCurrentPhase && (
                    <div>
                        {(allowedPowerOrderTypes.length && (
                            <span>
                                <strong>Orderable locations</strong>: {orderTypeToLocs[orderBuildingType].join(', ')}
                            </span>
                        ))
                        || (<strong>&nbsp;No orderable location.</strong>)}
                        {phaseType === 'A' && (
                            (buildCount === null && (
                                <strong>&nbsp;(unknown build count)</strong>
                            ))
                            || (buildCount === 0 ? (
                                <strong>&nbsp;(nothing to build or disband)</strong>
                            ) : (buildCount > 0 ? (
                                <strong>&nbsp;({buildCount} unit{buildCount > 1 && 's'} may be built)</strong>
                            ) : (
                                <strong>&nbsp;({-buildCount} unit{buildCount < -1 && 's'} to disband)</strong>
                            )))
                        )}
                    </div>
                )) || ''}
                <Tabs menu={tabNames} titles={tabTitles} onChange={this.onChangeMainTab} active={mainTab}>
                    {/* Tab Phase history. */}
                    {(hasTabPhaseHistory && this.renderTabPhaseHistory(mainTab === 'phase_history', engine)) || ''}
                    {/* Tab Current phase. */}
                    {(hasTabCurrentPhase && this.renderTabCurrentPhase(
                        mainTab === 'current_phase',
                        engine,
                        currentPowerName,
                        orderBuildingType,
                        this.state.orderBuildingPath
                    )) || ''}
                </Tabs>
                {this.state.fancy_title && (
                    <FancyBox title={this.state.fancy_title} onClose={this.state.on_fancy_close}>
                        {this.state.fancy_function()}
                    </FancyBox>)}
            </main>
        );
    }

    componentDidMount() {
        super.componentDidMount();
        if (this.props.data.client)
            this.reloadDeadlineTimer(this.props.data.client);
        this.props.data.displayed = true;
        // Try to prevent scrolling when pressing keys Home and End.
        document.onkeydown = (event) => {
            if (['home', 'end'].includes(event.key.toLowerCase())) {
                // Try to prevent scrolling.
                if (event.hasOwnProperty('cancelBubble'))
                    event.cancelBubble = true;
                if (event.stopPropagation)
                    event.stopPropagation();
                if (event.preventDefault)
                    event.preventDefault();
            }
        };
    }

    componentDidUpdate() {
        this.props.data.displayed = true;
    }

    componentWillUnmount() {
        this.clearScheduleTimeout();
        this.props.data.displayed = false;
        document.onkeydown = null;
    }

}
