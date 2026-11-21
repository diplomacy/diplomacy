/* eslint-env jest */
import React from 'react';
import HotKey from './components/hot_key';
import ReactDOM from 'react-dom';
import {act} from 'react-dom/test-utils';
import {ContentGame} from './pages/content_game';
import {PowerOrderCreationForm} from './forms/power_order_creation_form';
import {SelectViaForm} from './forms/select_via_form';
import {Power} from '../diplomacy/engine/power';
import {STRINGS} from '../diplomacy/utils/strings';

let container;

function pressKey(key, keyCode, target = document.body) {
    act(() => {
        for (const type of ['keydown', 'keypress', 'keyup'])
            target.dispatchEvent(new KeyboardEvent(type, {key, keyCode, which: keyCode, bubbles: true}));
    });
}

beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
});

afterEach(() => {
    act(() => {
        ReactDOM.unmountComponentAtNode(container);
    });
    container.remove();
});

it.each(['renderTabResults', 'renderTabMessages'])('%s handles history navigation keys only while displayed', method => {
    const engine = {phase: 'F1901M', order_history: {contains: () => false}, result_history: {contains: () => false}};
    const view = {
        state: {historyShowOrders: false},
        __get_engine_to_display: () => ({engine, pastPhases: ['S1901M', 'F1901M', 'S1902M'], phaseIndex: 1}),
        __form_phases: () => <select key="phases" id="select-past-phase" defaultValue="1">
            {[0, 1, 2].map(index => <option key={index} value={index}>{index}</option>)}
        </select>,
        renderMapForResults: () => null,
        renderMapForMessages: () => null,
        renderCurrentMessages: () => null,
        renderPastMessages: () => null,
        __change_past_phase: jest.fn()
    };
    for (const name of ['onChangePastPhaseIndex', 'onDecrementPastPhase', 'onIncrementPastPhase',
        'displayFirstPastPhase', 'displayLastPastPhase'])
        view[name] = ContentGame.prototype[name].bind(view);
    const render = displayed => act(() => {
        ReactDOM.render(ContentGame.prototype[method].call(view, displayed, engine), container);
    });

    render(true);
    pressKey('ArrowRight', 39);
    expect(view.__change_past_phase).toHaveBeenLastCalledWith(2, 0);
    pressKey('ArrowLeft', 37);
    expect(view.__change_past_phase).toHaveBeenLastCalledWith(1, 1);
    pressKey('Home', 36);
    expect(view.__change_past_phase).toHaveBeenLastCalledWith(0, 0);
    pressKey('End', 35);
    expect(view.__change_past_phase).toHaveBeenLastCalledWith(-1, 1);

    // Shortcuts must not navigate while the user is typing in a field.
    const input = document.createElement('input');
    container.appendChild(input);
    view.__change_past_phase.mockClear();
    pressKey('ArrowLeft', 37, input);
    expect(view.__change_past_phase).not.toHaveBeenCalled();
    input.remove();

    render(false);
    pressKey('ArrowLeft', 37);
    expect(view.__change_past_phase).not.toHaveBeenCalled();
});

it('selects an order type with a letter and resets it with Escape', () => {
    const onChange = jest.fn();
    const power = new Power('FRANCE', STRINGS.OMNISCIENT_TYPE, {isRealTime: () => false});
    act(() => {
        ReactDOM.render(<PowerOrderCreationForm power={power} role={STRINGS.OMNISCIENT_TYPE}
            orderType="H" orderTypes={['H', 'M']} onChange={onChange}/>, container);
    });

    pressKey('m', 109);
    expect(onChange).toHaveBeenLastCalledWith({order_type: 'M'});
    pressKey('Escape', 27);
    expect(onChange).toHaveBeenLastCalledWith({order_type: 'H'});
});

it('updates order shortcuts when the same form changes phase', () => {
    const onChange = jest.fn();
    const power = new Power('FRANCE', STRINGS.OMNISCIENT_TYPE, {isRealTime: () => false});
    const render = orderTypes => act(() => {
        ReactDOM.render(<PowerOrderCreationForm power={power} role={STRINGS.OMNISCIENT_TYPE}
            orderType={orderTypes[0]} orderTypes={orderTypes} onChange={onChange}/>, container);
    });
    render(['H', 'M']);
    render(['A', 'F']);
    pressKey('a', 97);
    expect(onChange).toHaveBeenLastCalledWith({order_type: 'A'});
    pressKey('f', 102);
    expect(onChange).toHaveBeenLastCalledWith({order_type: 'F'});
    onChange.mockClear();
    pressKey('h', 104);
    pressKey('m', 109);
    expect(onChange).not.toHaveBeenCalled();
});

it('lets a dialog own move keys and restores the underlying form on close', () => {
    const onChange = jest.fn();
    const onSelect = jest.fn();
    const power = new Power('FRANCE', STRINGS.OMNISCIENT_TYPE, {isRealTime: () => false});
    const render = dialog => act(() => {
        ReactDOM.render(<div>
            <PowerOrderCreationForm power={power} role={STRINGS.OMNISCIENT_TYPE}
                orderType="H" orderTypes={['H', 'M']} onChange={onChange}/>
            {dialog && <SelectViaForm path={['A', 'LON', '-', 'BEL']} onSelect={onSelect} onClose={() => {}}/>}
        </div>, container);
    });
    render(false);
    render(true);
    render(true); // An ordinary form rerender must not reclaim the dialog's keys.
    pressKey('m', 109);
    pressKey('v', 118);
    expect(onSelect.mock.calls).toEqual([['M'], ['V']]);
    expect(onChange).not.toHaveBeenCalled();
    render(false);
    pressKey('m', 109);
    expect(onChange).toHaveBeenLastCalledWith({order_type: 'M'});
    expect(onSelect).toHaveBeenCalledTimes(2);
});

it('updates bindings and callbacks without losing ownership during rerenders or non-top cleanup', () => {
    const first = jest.fn();
    const updated = jest.fn();
    const top = jest.fn();
    const render = (keys, callback, showFirst = true, showTop = true) => act(() => {
        ReactDOM.render(<div>
            {showFirst && <HotKey key="first" keys={keys} onKeysPressed={callback}/>}
            {showTop && <HotKey key="top" keys={['m']} onKeysPressed={top}/>}
        </div>, container);
    });
    render(['m'], first);
    render(['m'], updated);
    pressKey('m', 109);
    expect(top).toHaveBeenCalledTimes(1);
    expect(first).not.toHaveBeenCalled();
    expect(updated).not.toHaveBeenCalled();
    render(['m'], updated, false);
    pressKey('m', 109);
    expect(top).toHaveBeenCalledTimes(2);
    render(['a'], first, true, false);
    render(['f'], updated, true, false);
    pressKey('a', 97);
    expect(first).not.toHaveBeenCalled();
    pressKey('f', 102);
    expect(updated).toHaveBeenCalledTimes(1);
    render(['f'], first, true, false);
    pressKey('f', 102);
    expect(first).toHaveBeenCalledTimes(1);
    expect(updated).toHaveBeenCalledTimes(1);
});

it('ignores editable fields and does not prevent defaults even when a callback returns false', () => {
    const onKeysPressed = jest.fn(() => false);
    act(() => {
        ReactDOM.render(<div><HotKey keys={['m']} onKeysPressed={onKeysPressed}/></div>, container);
    });
    for (const tag of ['input', 'select', 'textarea']) {
        const field = document.createElement(tag);
        container.appendChild(field);
        pressKey('m', 109, field);
    }
    expect(onKeysPressed).not.toHaveBeenCalled();
    const event = new KeyboardEvent('keypress', {key: 'm', keyCode: 109, which: 109,
        bubbles: true, cancelable: true});
    act(() => { document.body.dispatchEvent(event) });
    expect(onKeysPressed).toHaveBeenCalledTimes(1);
    expect(event.defaultPrevented).toBe(false);
});

it('selects regular or convoyed moves from keyboard events', () => {
    const onSelect = jest.fn();
    act(() => {
        ReactDOM.render(<SelectViaForm path={['A', 'LON', '-', 'BEL']} onSelect={onSelect}
            onClose={() => {}}/>, container);
    });

    pressKey('m', 109);
    pressKey('v', 118);
    expect(onSelect.mock.calls).toEqual([['M'], ['V']]);
});
