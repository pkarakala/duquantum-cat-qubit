// Blockly reads CSS.supports while injecting. Node and some jsdom builds omit it.
if (typeof globalThis.CSS === 'undefined') {
  (globalThis as unknown as { CSS: { supports: () => boolean } }).CSS = {
    supports: () => false,
  };
}
