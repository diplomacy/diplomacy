import React from 'react';
import PropTypes from 'prop-types';
import {Panels} from "./panelList";
import {PanelChooseMap} from "./panelChooseMap";
import {PanelChoosePlayers} from "./panelChoosePlayers";
import {PanelChoosePower} from "./panelChoosePower";
import {PanelChooseSettings} from "./panelChooseSettings";
import {Maps} from "./mapList";
import {UTILS} from "../../../diplomacy/utils/utils";

export class GameCreationWizard extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            panel: Panels.CHOOSE_MAP,
            game_id: UTILS.createGameID(this.props.username),
            power_name: null,
            n_controls: -1,
            deadline: 0,
            registration_password: '',

            map: Maps[0],
            no_press: false
        };
        this.backward = this.backward.bind(this);
        this.forward = this.forward.bind(this);
        this.updateParams = this.updateParams.bind(this);
    }

    updateParams(params) {
        this.setState(params);
    }

    goToPanel(panelID) {
        if (panelID < Panels.CHOOSE_MAP)
            this.props.onCancel();
        else if (panelID > Panels.CHOOSE_SETTINGS) {
            const rules = ['POWER_CHOICE'];
            if (this.state.no_press)
                rules.push('NO_PRESS');
            if (!this.state.deadline) {
                rules.push('NO_DEADLINE');
                rules.push('REAL_TIME');
            }
            this.props.onSubmit({
                game_id: this.state.game_id,
                map_name: this.state.map.name,
                power_name: this.state.power_name,
                n_controls: this.state.n_controls,
                deadline: this.state.deadline,
                registration_password: this.state.registration_password || null,
                rules: rules
            });
        } else
            this.setState({panel: panelID, registration_password: ''});
    }

    backward(step) {
        this.goToPanel(this.state.panel - (step ? step : 1));
    }

    forward(step) {
        this.goToPanel(this.state.panel + (step ? step : 1));
    }

    renderPanel() {
        switch (this.state.panel) {
            case Panels.CHOOSE_MAP:
                return <PanelChooseMap forward={this.forward}
                                       params={this.state}
                                       onUpdateParams={this.updateParams}
                                       cancel={this.props.onCancel}/>;
            case Panels.CHOOSE_PLAYERS:
                return <PanelChoosePlayers backward={this.backward}
                                           forward={this.forward}
                                           onUpdateParams={this.updateParams}
                                           nbPowers={this.props.availableMaps[this.state.map.name].powers.length}
                                           cancel={this.props.onCancel}/>;
            case Panels.CHOOSE_POWER:
                return <PanelChoosePower backward={this.backward}
                                         forward={this.forward}
                                         onUpdateParams={this.updateParams}
                                         powers={this.props.availableMaps[this.state.map.name].powers}
                                         cancel={this.props.onCancel}/>;
            case Panels.CHOOSE_SETTINGS:
                return <PanelChooseSettings backward={this.backward}
                                            forward={this.forward}
                                            onUpdateParams={this.updateParams}
                                            username={this.props.username}
                                            params={this.state}
                                            cancel={this.props.onCancel}/>;
            default:
                return '';
        }
    }

    render() {
        return (
            <div className="game-creation-wizard">{this.renderPanel()}</div>
        );
    }
}

GameCreationWizard.propTypes = {
    onCancel: PropTypes.func.isRequired,
    onSubmit: PropTypes.func.isRequired,
    availableMaps: PropTypes.object.isRequired,
    username: PropTypes.string.isRequired
};
