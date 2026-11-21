import {UTILS} from './utils';

describe('UTILS.javascript tree helpers', () => {
    test('supports null-prototype objects', () => {
        const tree = Object.create(null);
        UTILS.javascript.extendTreeValue(tree, ['a', 'b'], 1, false);
        expect(UTILS.javascript.getTreeValue(tree, ['a', 'b'])).toEqual([1]);
    });

    test('ignores shadowed hasOwnProperty and inherited keys', () => {
        const tree = Object.create({inherited: 7});
        tree.hasOwnProperty = 'shadowed';
        tree.own = {hasOwnProperty: null, value: 3};
        expect(UTILS.javascript.getTreeValue(tree, ['own', 'value'])).toBe(3);
        expect(UTILS.javascript.getTreeValue(tree, ['inherited'])).toBe(null);
    });
});
