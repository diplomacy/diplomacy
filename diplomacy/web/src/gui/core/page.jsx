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
/** Main class to use to create app GUI. **/

import React from "react";
import {ContentConnection} from "../diplomacy/contents/content_connection";
import {ContentGames} from "../diplomacy/contents/content_games";
import {ContentGame} from "../diplomacy/contents/content_game";
import {UTILS} from "../../diplomacy/utils/utils";
import {Diplog} from "../../diplomacy/utils/diplog";
import {STRINGS} from "../../diplomacy/utils/strings";
import {Game} from "../../diplomacy/engine/game";
import Octicon, {Person} from '@githubprimer/octicons-react';
import $ from "jquery";
import {FancyBox} from "./fancybox";
import {DipStorage} from "../diplomacy/utils/dipStorage";

const CONTENTS = {
    connection: ContentConnection,
    games: ContentGames,
    game: ContentGame
};

export class Page extends React.Component {

    constructor(props) {
        super(props);
        this.connection = null;
        this.channel = null;
        this.availableMaps = null;
        this.state = {
            // fancybox,
            fancyTitle: null,
            onFancyBox: null,
            // Page messages
            error: null,
            info: null,
            success: null,
            title: null,
            // Page content parameters
            contentName: 'connection',
            contentData: null,
            // Games.
            games: {}, // Games found.
            myGames: {}  // Games locally stored.
        };
        this.loadPage = this.loadPage.bind(this);
        this.loadConnection = this.loadConnection.bind(this);
        this.loadGames = this.loadGames.bind(this);
        this.loadGame = this.loadGame.bind(this);
        this.loadGameFromDisk = this.loadGameFromDisk.bind(this);
        this.logout = this.logout.bind(this);
        this.error = this.error.bind(this);
        this.info = this.info.bind(this);
        this.success = this.success.bind(this);
        this.unloadFancyBox = this.unloadFancyBox.bind(this);
    }

    static wrapMessage(message) {
        return message ? `(${UTILS.date()}) ${message}` : '';
    }

    static __sort_games(games) {
        // Sort games with not-joined games first, else compare game ID.
        games.sort((a, b) => (((a.role ? 1 : 0) - (b.role ? 1 : 0)) || a.game_id.localeCompare(b.game_id)));
        return games;
    }

    copyState(updatedFields) {
        return Object.assign({}, this.state, updatedFields || {});
    }

    //// Methods to check page type.

    __page_is(contentName, contentData) {
        return this.state.contentName === contentName && (!contentData || this.state.contentData === contentData);
    }

    pageIsConnection(contentData) {
        return this.__page_is('connection', contentData);
    }

    pageIsGames(contentData) {
        return this.__page_is('games', contentData);
    }

    pageIsGame(contentData) {
        return this.__page_is('game', contentData);
    }

    //// Methods to load a global fancybox.

    loadFancyBox(title, callback) {
        this.setState({fancyTitle: title, onFancyBox: callback});
    }

    unloadFancyBox() {
        this.setState({fancyTitle: null, onFancyBox: null});
    }

    //// Methods to load a page.

    loadPage(contentName, contentData, messages) {
        messages = messages || {};
        messages.error = Page.wrapMessage(messages.error);
        messages.info = Page.wrapMessage(messages.info);
        messages.success = Page.wrapMessage(messages.success);
        Diplog.printMessages(messages);
        this.setState(this.copyState({
            error: messages.error,
            info: messages.info,
            success: messages.success,
            contentName: contentName,
            contentData: contentData,
            title: null,
            fancyTitle: null,
            onFancyBox: null
        }));
    }

    loadConnection(contentData, messages) {
        this.loadPage('connection', contentData, messages);
    }

    loadGames(contentData, messages) {
        this.loadPage('games', contentData, messages);
    }

    loadGame(gameInfo, messages) {
        this.loadPage('game', gameInfo, messages);
    }

    loadGameFromDisk() {
        const input = $(document.createElement('input'));
        input.attr("type", "file");
        input.trigger('click');
        input.change(event => {
            const file = event.target.files[0];
            if (!file.name.match(/\.json$/i)) {
                this.error(`Invalid JSON filename ${file.name}`);
            } else {
                const reader = new FileReader();
                reader.onload = () => {
                    const savedData = JSON.parse(reader.result);
                    const gameObject = {};
                    gameObject.game_id = `(local) ${savedData.id}`;
                    gameObject.map_name = savedData.map;
                    gameObject.rules = savedData.rules;
                    const state_history = {};
                    const message_history = {};
                    const order_history = {};
                    const result_history = {};
                    for (let savedPhase of savedData.phases) {
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
                        state_history[gameState.name] = gameState;
                        order_history[gameState.name] = phaseOrders;
                        message_history[gameState.name] = phaseMessages;
                        result_history[gameState.name] = phaseResults;
                    }
                    gameObject.state_history = state_history;
                    gameObject.message_history = message_history;
                    gameObject.order_history = order_history;
                    gameObject.state_history = state_history;
                    gameObject.result_history = result_history;
                    gameObject.messages = [];
                    gameObject.role = STRINGS.OBSERVER_TYPE;
                    gameObject.status = STRINGS.COMPLETED;
                    gameObject.timestamp_created = 0;
                    gameObject.deadline = 0;
                    gameObject.n_controls = 0;
                    gameObject.registration_password = '';
                    const game = new Game(gameObject);
                    this.loadGame(game);
                };
                reader.readAsText(file);
            }
        });
    }

    //// Methods to sign out channel and go back to connection page.

    __disconnect() {
        // Clear local data and go back to connection page.
        this.connection.close();
        this.connection = null;
        this.channel = null;
        this.availableMaps = null;
        const message = Page.wrapMessage(`Disconnected from channel and server.`);
        Diplog.success(message);
        this.setState(this.copyState({
            error: null,
            info: null,
            success: message,
            contentName: 'connection',
            contentData: null,
            // When disconnected, remove all games previously loaded.
            games: {},
            myGames: {}
        }));
    }

    logout() {
        // Disconnect channel and go back to connection page.
        if (this.channel) {
            this.channel.logout()
                .then(() => this.__disconnect())
                .catch(error => this.error(`Error while disconnecting: ${error.toString()}.`));
        } else {
            this.__disconnect();
        }
    }

    //// Methods to be used to set page title and messages.

    setTitle(title) {
        this.setState({title: title});
    }

    error(message) {
        message = Page.wrapMessage(message);
        Diplog.error(message);
        this.setState({error: message});
    }

    info(message) {
        message = Page.wrapMessage(message);
        Diplog.info(message);
        this.setState({info: message});
    }

    success(message) {
        message = Page.wrapMessage(message);
        Diplog.success(message);
        this.setState({success: message});
    }

    warn(message) {
        this.info(message);
    }

    //// Methods to manage games.

    updateMyGames(gamesToAdd) {
        // Update state myGames with given games. This method does not update local storage.
        const myGames = Object.assign({}, this.state.myGames);
        let gamesFound = null;
        for (let gameToAdd of gamesToAdd) {
            myGames[gameToAdd.game_id] = gameToAdd;
            if (this.state.games.hasOwnProperty(gameToAdd.game_id)) {
                if (!gamesFound)
                    gamesFound = Object.assign({}, this.state.games);
                gamesFound[gameToAdd.game_id] = gameToAdd;
            }
        }
        if (!gamesFound)
            gamesFound = this.state.games;
        this.setState({myGames: myGames, games: gamesFound});
    }

    getMyGames() {
        return Page.__sort_games(Object.values(this.state.myGames));
    }

    getGamesFound() {
        return Page.__sort_games(Object.values(this.state.games));
    }

    addGamesFound(gamesToAdd) {
        const gamesFound = {};
        for (let game of gamesToAdd) {
            gamesFound[game.game_id] = (
                this.state.myGames.hasOwnProperty(game.game_id) ?
                    this.state.myGames[game.game_id] : game
            );
        }
        this.setState({games: gamesFound});
    }

    leaveGame(gameID) {
        if (this.state.myGames.hasOwnProperty(gameID)) {
            const game = this.state.myGames[gameID];
            if (game.client) {
                game.client.leave()
                    .then(() => {
                        this.disconnectGame(gameID);
                        this.loadGames(null, {info: `Game ${gameID} left.`});
                    })
                    .catch(error => this.error(`Error when leaving game ${gameID}: ${error.toString()}`));
            }
        }
    }

    disconnectGame(gameID) {
        if (this.state.myGames.hasOwnProperty(gameID)) {
            const game = this.state.myGames[gameID];
            if (game.client)
                game.client.clearAllCallbacks();
            this.channel.getGamesInfo({games: [gameID]})
                .then(gamesInfo => {
                    this.updateMyGames(gamesInfo);
                })
                .catch(error => this.error(`Error while leaving game ${gameID}: ${error.toString()}`));
        }
    }

    addToMyGames(game) {
        // Update state myGames with given game **and** update local storage.
        const myGames = Object.assign({}, this.state.myGames);
        const gamesFound = this.state.games.hasOwnProperty(game.game_id) ? Object.assign({}, this.state.games) : this.state.games;
        myGames[game.game_id] = game;
        if (gamesFound.hasOwnProperty(game.game_id))
            gamesFound[game.game_id] = game;
        DipStorage.addUserGame(this.channel.username, game.game_id);
        this.setState({myGames: myGames, games: gamesFound});
    }

    removeFromMyGames(gameID) {
        if (this.state.myGames.hasOwnProperty(gameID)) {
            const games = Object.assign({}, this.state.myGames);
            delete games[gameID];
            DipStorage.removeUserGame(this.channel.username, gameID);
            this.setState({myGames: games});
        }
    }

    hasMyGame(gameID) {
        return this.state.myGames.hasOwnProperty(gameID);
    }

    //// Render method.

    render() {
        const content = CONTENTS[this.state.contentName].builder(this, this.state.contentData);
        const hasNavigation = UTILS.javascript.hasArray(content.navigation);

        // NB: I currently don't find a better way to update document title from content details.
        const successMessage = this.state.success || '-';
        const infoMessage = this.state.info || '-';
        const errorMessage = this.state.error || '-';
        const title = this.state.title || content.title;
        document.title = title + ' | Diplomacy';

        return (
            <div className="page container-fluid" id={this.state.contentName}>
                <div className={'top-msg row'}>
                    <div title={successMessage !== '-' ? successMessage : ''}
                         className={'col-sm-4 msg success ' + (this.state.success ? 'with-msg' : 'no-msg')}
                         onClick={() => this.success()}>
                        {successMessage}
                    </div>
                    <div title={infoMessage !== '-' ? infoMessage : ''}
                         className={'col-sm-4 msg info ' + (this.state.info ? 'with-msg' : 'no-msg')}
                         onClick={() => this.info()}>
                        {infoMessage}
                    </div>
                    <div title={errorMessage !== '-' ? errorMessage : ''}
                         className={'col-sm-4 msg error ' + (this.state.error ? 'with-msg' : 'no-msg')}
                         onClick={() => this.error()}>
                        {errorMessage}
                    </div>
                </div>
                {((hasNavigation || this.channel) && (
                    <div className={'title row'}>
                        <div className={'col align-self-center'}><strong>{title}</strong></div>
                        <div className={'col-sm-1'}>
                            {(!hasNavigation && (
                                <div className={'float-right'}>
                                    <strong>
                                        <u className={'mr-2'}>{this.channel.username}</u>
                                        <Octicon icon={Person}/>
                                    </strong>
                                </div>
                            )) || (
                                <div className="dropdown float-right">
                                    <button className="btn btn-secondary dropdown-toggle" type="button"
                                            id="dropdownMenuButton" data-toggle="dropdown"
                                            aria-haspopup="true" aria-expanded="false">
                                        {(this.channel && this.channel.username && (
                                            <span>
                                                <u className={'mr-2'}>{this.channel.username}</u>
                                                <Octicon icon={Person}/>
                                            </span>
                                        )) || 'Menu'}
                                    </button>
                                    <div className="dropdown-menu dropdown-menu-right"
                                         aria-labelledby="dropdownMenuButton">
                                        {content.navigation.map((nav, index) => {
                                            const navTitle = nav[0];
                                            const navAction = nav[1];
                                            return <a key={index} className="dropdown-item"
                                                      onClick={navAction}>{navTitle}</a>;
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )) || (
                    <div className={'title'}><strong>{title}</strong></div>
                )}
                {content.component}
                {this.state.onFancyBox && (
                    <FancyBox title={this.state.fancyTitle} onClose={this.unloadFancyBox}>
                        {this.state.onFancyBox()}
                    </FancyBox>
                )}
            </div>
        );
    }
}
