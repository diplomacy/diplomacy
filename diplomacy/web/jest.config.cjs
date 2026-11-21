module.exports = {
    testEnvironment: 'jsdom',
    roots: ['<rootDir>/src'],
    transform: {'^.+\\.[jt]sx?$': 'babel-jest'},
    moduleNameMapper: {
        '\\.(css|svg)$': '<rootDir>/test/assetMock.cjs'
    }
};
