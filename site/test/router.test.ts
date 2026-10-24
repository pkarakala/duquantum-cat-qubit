// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../src/components/plot", () => ({ plot: vi.fn(async () => {}) }));

import { buildMock } from "../scripts/make_mock.mjs";
import { plot } from "../src/components/plot";
import { loadBundle } from "../src/data/index";
import { DATA_NAMES, type DataName } from "../src/data/types";
import { renderRoute } from "../src/main";

const mockData = buildMock() as Record<DataName, unknown>;
const asMods = (dir: string, names: readonly DataName[] = DATA_NAMES) =>
  Object.fromEntries(names.map((n) => [`./${dir}/${n}.json`, structuredClone(mockData[n])]));
const mockMods = asMods("mock");

const PAGES: [string, string, boolean][] = [
  ["#/inflate", "Inflate", true],
  ["#/errors", "Error budget", true],
  ["#/readout", "Readout designer", true],
  ["#/verify", "Verification", false],
  ["#/about", "About", false],
];

function setupDom(): HTMLElement {
  document.body.innerHTML = `
    <nav aria-label="Pages"><a href="#/inflate">Inflate</a><a href="#/errors">Error budget</a>
      <a href="#/readout">Readout designer</a><a href="#/verify">Verification</a><a href="#/about">About</a></nav>
    <div id="banner" role="status" hidden></div>
    <main id="app"></main>
    <dialog id="card"></dialog>`;
  return document.getElementById("app")!;
}

function accessibleName(el: Element): string {
  const aria = el.getAttribute("aria-label")?.trim();
  if (aria) return aria;
  const by = el.getAttribute("aria-labelledby");
  if (by) {
    const text = by
      .split(/\s+/)
      .map((id) => document.getElementById(id)?.textContent?.trim() ?? "")
      .join(" ")
      .trim();
    if (text) return text;
  }
  const labels = (el as HTMLInputElement).labels;
  if (labels && labels.length) return [...labels].map((l) => l.textContent?.trim() ?? "").join(" ").trim();
  return "";
}

beforeEach(() => {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  }));
  vi.mocked(plot).mockClear();
});

describe("hash router", () => {
  for (const [hash, title, plots] of PAGES) {
    it(`${hash} renders "${title}"`, () => {
      const root = setupDom();
      expect(() => renderRoute(hash, root, loadBundle())).not.toThrow();
      expect(root.querySelector("h1")?.textContent).toContain(title);
      if (plots) expect(vi.mocked(plot).mock.calls.length).toBeGreaterThan(0);
    });
  }

  it("'' and unknown hashes render Inflate", () => {
    for (const hash of ["", "#/nope"]) {
      const root = setupDom();
      renderRoute(hash, root, loadBundle({}, mockMods));
      expect(root.querySelector("h1")?.textContent).toContain("Inflate");
    }
  });

  it("marks the active nav link", () => {
    const root = setupDom();
    renderRoute("#/errors", root, loadBundle({}, mockMods));
    const active = document.querySelector('nav a[aria-current="page"]');
    expect(active?.getAttribute("href")).toBe("#/errors");
  });
});

describe("mock banner", () => {
  it("names every mock file when nothing is live", () => {
    const root = setupDom();
    const b = loadBundle({}, mockMods);
    renderRoute("#/inflate", root, b);
    const banner = document.getElementById("banner")!;
    expect(banner.getAttribute("role")).toBe("status");
    expect(banner.hidden).toBe(false);
    expect(banner.textContent).toContain("MOCK DATA");
    for (const n of DATA_NAMES) expect(banner.textContent).toContain(`${n}.json`);
  });

  it("is empty and hidden when all five files are live and valid", () => {
    const root = setupDom();
    const b = loadBundle(asMods("live"), mockMods);
    for (const n of DATA_NAMES) expect(b.sources[n]).toBe("live");
    renderRoute("#/inflate", root, b);
    const banner = document.getElementById("banner")!;
    expect(banner.hidden).toBe(true);
    expect(banner.textContent).toBe("");
  });

  it("falls back to mock for an invalid live file and names it", () => {
    const root = setupDom();
    const live = asMods("live");
    (live["./live/errors.json"] as { gamma_x: { one_mode: { value: unknown }[] } }).gamma_x.one_mode[0].value = "x";
    const b = loadBundle(live, mockMods);
    expect(b.sources.errors).toBe("mock");
    expect(b.sources.records).toBe("live");
    renderRoute("#/inflate", root, b);
    const banner = document.getElementById("banner")!;
    expect(banner.hidden).toBe(false);
    expect(banner.textContent).toContain("errors.json");
    expect(banner.textContent).not.toContain("readout.json");
  });

  it("partial live data: a missing live file falls back to mock", () => {
    const b = loadBundle(asMods("live", ["records", "verify"]), mockMods);
    expect(b.sources).toEqual({ records: "live", inflation: "mock", errors: "mock", readout: "mock", verify: "live" });
  });
});

describe("accessibility", () => {
  for (const [hash] of PAGES) {
    it(`every control on ${hash} has an accessible name`, () => {
      const root = setupDom();
      renderRoute(hash, root, loadBundle({}, mockMods));
      const controls = [...root.querySelectorAll("input, select, button")];
      for (const el of controls) expect(accessibleName(el), el.outerHTML.slice(0, 120)).not.toBe("");
    });
  }
});
