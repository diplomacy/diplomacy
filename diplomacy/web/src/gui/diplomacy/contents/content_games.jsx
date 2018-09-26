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
import {Content} from "../../core/content";
import {Tab, Tabs} from "../../core/tabs";
import {Table} from "../../core/table";
import {FindForm} from "../forms/find_form";
import {CreateForm} from "../forms/create_form";
import {InlineGameView} from "../utils/inline_game_view";
import {STRINGS} from "../../../diplomacy/utils/strings";

const TABLE_LOCAL_GAMES = {
    game_id: ['Game ID', 0],
    deadline: ['Deadline', 1],
    rights: ['Rights', 2],
    rules: ['Rules', 3],
    players: ['Players/Expected', 4],
    status: ['Status', 5],
    phase: ['Phase', 6],
    join: ['Join', 7],
    my_games: ['My Games', 8],
};

export class ContentGames extends Content {

    constructor(props) {
        super(props);
        this.state = {tab: null};
        this.changeTab = this.changeTab.bind(this);
        this.onFind = this.onFind.bind(this);
        this.onCreate = this.onCreate.bind(this);
        this.wrapGameData = this.wrapGameData.bind(this);
    }

    static builder(page, data) {
        return {
            title: 'Games',
            navigation: [
                ['load a game from disk', page.loadGameFromDisk],
                ['logout', page.logout]
            ],
            component: <ContentGames page={page} data={data}/>
        };
    }

    onFind(form) {
        for (let field of ['game_id', 'status', 'include_protected', 'for_omniscience'])
            if (!form[field])
                form[field] = null;
        this.getPage().channel.listGames(form)
            .then((data) => {
                this.getPage().success('Found ' + data.length + ' data.');
                this.getPage().addGamesFound(data);
            })
            .catch((error) => {
                this.getPage().error('Error when looking for distant games: ' + error);
            });
    }

    onCreate(form) {
        for (let key of Object.keys(form)) {
            if (form[key] === '')
                form[key] = null;
        }
        if (form.n_controls !== null)
            form.n_controls = parseInt(form.n_controls, 10);
        if (form.deadline !== null)
            form.deadline = parseInt(form.deadline, 10);
        form.rules = ['POWER_CHOICE'];
        for (let rule of STRINGS.PUBLIC_RULES) {
            const rule_id = `rule_${rule.toLowerCase()}`;
            if (form.hasOwnProperty(rule_id)) {
                if (form[rule_id])
                    form.rules.push(rule);
                delete form[rule_id];
            }
        }
        let networkGame = null;
        this.getPage().channel.createGame(form)
            .then((game) => {
                this.getPage().addToMyGames(game.local);
                networkGame = game;
                return networkGame.getAllPossibleOrders();
            })
            .then(allPossibleOrders => {
                networkGame.local.setPossibleOrders(allPossibleOrders);
                this.getPage().loadGame(networkGame.local, {success: 'Game created.'});
            })
            .catch((error) => {
                this.getPage().error('Error when creating a game: ' + error);
            });
    }

    changeTab(tabIndex) {
        this.setState({tab: tabIndex});
    }

    wrapGameData(gameData) {
        return new InlineGameView(this.getPage(), gameData);
    }

    render() {
        const myGames = this.getPage().getMyGames();
        const tab = this.state.tab ? this.state.tab : (myGames.length ? 'my-games' : 'find');
        return (
            <main>
                <Tabs menu={['create', 'find', 'my-games']} titles={['Create', 'Find', 'My Games']}
                      onChange={this.changeTab} active={tab}>
                    <Tab id="tab-games-create" display={tab === 'create'}>
                        <CreateForm onSubmit={this.onCreate}/>
                    </Tab>
                    <Tab id="tab-games-find" display={tab === 'find'}>
                        <FindForm onSubmit={this.onFind}/>
                        <Table className={"table table-striped"} caption={"Games"} columns={TABLE_LOCAL_GAMES}
                               data={this.getPage().getGamesFound()} wrapper={this.wrapGameData}/>
                    </Tab>
                    <Tab id={'tab-my-games'} display={tab === 'my-games'}>
                        <Table className={"table table-striped"} caption={"My games"} columns={TABLE_LOCAL_GAMES}
                               data={myGames} wrapper={this.wrapGameData}/>
                    </Tab>
                </Tabs>
            </main>
        );
    }

}
