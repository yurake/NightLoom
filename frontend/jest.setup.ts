import "@testing-library/jest-dom";

// Polyfill for fetch API in Jest environment
global.fetch = jest.fn();
