/** Learner shell: one loop for every level, scoped under .academy. */

import { bind, getLevelState, nextLevel, runSim, setParam, showHint } from '../controller';
import { createLevelRun, type LevelRun } from '../engine';
import { on } from '../events';
import { coherentDecay, dftMagnitude, ONE_MHZ } from '../formulas';
import { levelById, LEVELS } from '../levels';
import { logLinear } from '../levels/metrics';
import { gridFrom } from '../levels/L5';
import { snrAt } from '../levels/L7';
import { logRun, runRow } from '../logRun';
import { fitPulse } from '../l8score';
import { getLearnerId } from '../progress';
import { getPreset } from '../presets';
import { mountClaimCredential } from '../../chain/claim';
import { bridgeFromController } from '../../tutor/bridge';
import { mountTutor } from '../../tutor';
import type { LevelId, LevelState, RunOutcome } from '../types';
import { mountAha } from './ahaCard';
import { setRichText } from './richText';
import { mountCheckBanner } from './checkBanner';
import { mountCode } from './codeToggle';
import { mountConcept } from './conceptCard';
import { mountControls, mountRunButton } from './controls';
import { mountHistogram } from './histogram';
import { mountHints } from './hintLadder';
import { mountParity } from './parityMeter';
import { plot } from './plot';
import { mountRadios } from './predictPanel';
import { mountProgress } from './progressMap';
import { mountBadge } from './sourceBadge';
import { ACADEMY_CSS } from './styles';
import { paintWigner } from './wignerCanvas';

function radios(host: HTMLElement, question: string, options: { id: string; text: string; correct: boolean; feedback: string }[], onChoose: (id: string) => void) {
  return mountRadios(host, question, options, onChoose);
}

export interface AcademyHandle {
  navigate(levelId: LevelId): void;
  dispose(): void;
}

function ensureStyle(): void {
  let node = document.getElementById('academy-style');
  if (!node) {
    node = document.createElement('style');
    node.id = 'academy-style';
    document.head.append(node);
  }
  if (node.textContent !== ACADEMY_CSS) node.textContent = ACADEMY_CSS;
}

function runLabel(id: LevelId): string {
  return id === 'L8' ? 'Score' : 'Run';
}

function engineWords(engine: string): string {
  if (engine === 'ts') return 'in-browser';
  if (engine === 'records') return 'stored records';
  if (engine === 'server-expr' || engine === 'server-two-mode') return 'API or stored preset';
  return engine;
}

function idleNote(id: LevelId, engine: string, hasApi: boolean): string {
  if (id === 'L8') return 'Not scored yet. If the in-browser model loads, the badge says in-browser. If it does not, the badge says MOCK.';
  if (engine === 'ts') return 'Not run yet. A finished run is computed in this browser and is not badged MOCK.';
  if (id === 'L6') {
    return hasApi
      ? 'Not run yet. If the API answers, the badge names that server result. If it fails, the badge says MOCK. Vultr is not deployed for this demo.'
      : 'Not run yet. No API is configured, so Run shows a stored build and the badge says MOCK. Vultr is not deployed for this demo.';
  }
  if (engine === 'records') return 'Not run yet. No live record bundle is loaded, so Run shows the stored snapshot and the badge says MOCK.';
  return 'Not run yet.';
}

function prefersStill(): boolean {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
}

export function mountAcademy(root: HTMLElement, opts?: { levelId?: LevelId; apiBase?: string }): AcademyHandle {
  function apiBase(): string {
    const fromOpts = opts?.apiBase ?? import.meta.env.VITE_API_BASE ?? '';
    return fromOpts.replace(/\/$/, '');
  }

  ensureStyle();
  getLearnerId();
  let disposed = false;
  let current = opts?.levelId ?? 'L1';
  let cleanup: (() => void)[] = [];
  let seq = 0;
  let timer = 0;
  let armed = false;
  let frameTimer = 0;

  const api: AcademyHandle = {
    navigate(levelId) {
      if (disposed || levelId === current) return;
      const next = `#/learn/${levelId}`;
      if (location.hash !== next && location.hash !== `#${levelId}`) location.hash = next;
      render(levelId);
    },
    dispose() {
      disposed = true;
      for (const fn of cleanup) fn();
      cleanup = [];
      window.clearTimeout(timer);
      window.clearInterval(frameTimer);
      root.replaceChildren();
    },
  };

  function render(levelId: LevelId) {
    for (const fn of cleanup) fn();
    cleanup = [];
    window.clearTimeout(timer);
    window.clearInterval(frameTimer);
    armed = false;
    seq += 1;
    current = levelId;
    const spec = levelById(levelId) ?? LEVELS[0]!;
    const run = createLevelRun(spec, opts && 'apiBase' in (opts ?? {}) ? { apiBase: opts?.apiBase } : undefined);
    if (spec.id === 'L8') {
      const square = (getPreset('L8')?.result.squareBins as number[] | undefined) ?? Array.from({ length: 20 }, () => 1);
      run.setBins(square);
    }
    bind(run, (id) => api.navigate(id));

    root.classList.add('academy');
    root.dataset.level = spec.id;
    root.replaceChildren();

    const header = document.createElement('header');
    const eyebrow = document.createElement('p');
    eyebrow.className = 'eyebrow';
    eyebrow.textContent = `Learn · ${spec.minutes} min · ${engineWords(spec.sim.engine)}`;
    const title = document.createElement('h1');
    title.textContent = `${spec.id} · ${spec.title}`;
    const mapHost = document.createElement('div');
    header.append(eyebrow, title, mapHost);
    mountProgress(mapHost, spec, (id) => api.navigate(id));

    const badgeHost = document.createElement('div');
    const badge = mountBadge(badgeHost);
    badge.set('Not run yet', idleNote(spec.id, spec.sim.engine, Boolean(apiBase())));
    const conceptHost = document.createElement('div');
    mountConcept(conceptHost, spec);

    const layout = document.createElement('div');
    layout.className = 'layout';
    const side = document.createElement('div');
    const main = document.createElement('div');
    layout.append(side, main);

    const predictHost = document.createElement('section');
    predictHost.className = 'card predict-gate';
    predictHost.dataset.locked = 'true';
    const verb = runLabel(spec.id);
    const step = document.createElement('p');
    step.className = 'step';
    step.textContent = 'Predict first';
    const gateStatus = document.createElement('p');
    gateStatus.className = 'gate-status';
    gateStatus.textContent = `Choose an answer. ${verb} stays off until you do.`;
    predictHost.append(step, gateStatus);
    const feedback = document.createElement('p');
    feedback.className = 'feedback';
    radios(predictHost, spec.predict.question, spec.predict.options, (id) => {
      const option = spec.predict.options.find((item) => item.id === id);
      run.choose(id);
      setRichText(feedback, option?.feedback ?? '');
    });
    predictHost.append(feedback);
    if (spec.predictFollowUp) {
      radios(predictHost, spec.predictFollowUp.question, spec.predictFollowUp.options, (id) => run.chooseFollowUp(id));
    }

    const controlHost = document.createElement('div');
    const offControls = mountControls(controlHost, run, () => {
      paintLocal(run);
      if (!armed || !run.canRun()) return;
      window.clearTimeout(timer);
      timer = window.setTimeout(() => void launch(run), 100);
    });
    cleanup.push(offControls);

    const actions = document.createElement('div');
    actions.className = 'actions';
    const runButton = mountRunButton(actions, run, runLabel(spec.id), () => void launch(run));
    let finishedRun = false;
    const syncGate = () => {
      const open = run.canRun();
      predictHost.dataset.locked = open ? 'false' : 'true';
      gateStatus.textContent = open
        ? `Prediction saved. ${verb} is the next step.`
        : `Choose an answer. ${verb} stays off until you do.`;
      runButton.classList.toggle('is-primary', open && !finishedRun);
    };
    syncGate();
    cleanup.push(run.subscribe(syncGate));

    const views = document.createElement('div');
    views.className = 'views';
    const histHost = document.createElement('div');
    const wignerHost = document.createElement('div');
    const plotHost = document.createElement('div');
    plotHost.className = 'plot';
    const parityHost = document.createElement('div');
    const extra = document.createElement('div');
    extra.className = 'extra';
    views.append(histHost, wignerHost, plotHost, parityHost, extra);
    const histogram = mountHistogram(histHost);
    const parity = mountParity(parityHost);
    if (!spec.views.some((view) => view.kind === 'histogram')) histHost.hidden = true;
    if (!spec.views.some((view) => view.kind === 'wigner')) wignerHost.hidden = true;
    if (!spec.views.some((view) => view.kind === 'parity')) parityHost.hidden = true;
    if (!spec.views.some((view) => view.kind === 'n_t' || view.kind === 'rates_log' || view.kind === 'b_iq' || view.kind === 'pulse')) plotHost.hidden = true;
    if (!wignerHost.hidden) {
      const canvas = document.createElement('canvas');
      paintWigner(canvas, new Float64Array([0]), 1, 1, [0], [0]);
      wignerHost.append(canvas);
    }

    const pulseHost = document.createElement('div');
    const pulseExtras = mountPulse(pulseHost, run, () => void launch(run));
    mountWell(extra, spec.id);
    if (spec.id === 'L6') {
      const blocksNote = document.createElement('p');
      blocksNote.className = 'blocks-note';
      blocksNote.append(document.createTextNode('This lesson runs four stored builds. Without a live API the badge says MOCK. Vultr is not hosting this demo. '));
      const sandbox = document.createElement('a');
      sandbox.href = '#/sandbox';
      sandbox.textContent = 'Open the block editor';
      blocksNote.append(sandbox, document.createTextNode('.'));
      controlHost.append(blocksNote);
    }

    side.append(predictHost, controlHost, pulseHost, actions);
    main.append(views);

    const checkHost = document.createElement('section');
    checkHost.className = 'card';
    const goal = document.createElement('p');
    goal.textContent = spec.check.goal;
    const checkButton = document.createElement('button');
    checkButton.type = 'button';
    checkButton.className = 'check';
    checkButton.textContent = 'Check';
    checkButton.disabled = true;
    const banner = mountCheckBanner(checkHost);
    checkButton.addEventListener('click', () => {
      const verdict = run.check();
      banner.set(verdict.message, verdict.pass);
      if (verdict.pass) {
        aha.show(spec.aha);
        if (spec.id === 'L8') showCredential();
        mountProgress(mapHost, spec, (id) => api.navigate(id));
      }
      hints.refresh();
    });
    checkHost.prepend(goal, checkButton);

    if (spec.checkFollowUp) {
      const follow = document.createElement('div');
      radios(follow, spec.checkFollowUp.question, spec.checkFollowUp.options, (id) => {
        const option = spec.checkFollowUp?.options.find((item) => item.id === id);
        const verdict = run.answerFollowUp(option?.text ?? id);
        banner.set(verdict.message, verdict.pass);
      });
      checkHost.append(follow);
    }

    const hintHost = document.createElement('section');
    hintHost.className = 'card';
    const hints = mountHints(hintHost, run);
    const ahaHost = document.createElement('div');
    const aha = mountAha(ahaHost);
    const codeHost = document.createElement('div');
    mountCode(codeHost, spec, () => stateOf(run));

    const tutor = document.createElement('div');
    tutor.dataset.slot = 'tutor';
    tutor.setAttribute('aria-label', 'Tutor');
    const tutorBase = apiBase();
    if (tutorBase) {
      const bridge = bridgeFromController(
        {
          getLevelState: () => getLevelState() as Record<string, unknown>,
          setParam: (name, value) => setParam(name, value),
          runSim: async () => {
            const outcome = (await runSim()) as { result?: { summary?: string }; source?: string } | null;
            return { summary: outcome?.result?.summary ?? '', source: outcome?.source ?? 'academy' };
          },
          showHint: (level) => {
            showHint(level);
          },
          nextLevel: () => nextLevel(),
        },
        { on },
      );
      mountTutor(tutor, bridge, { apiBase: tutorBase, askTutor: true, learnerId: getLearnerId() });
    }
    const credential = document.createElement('div');
    credential.dataset.slot = 'credential';
    credential.hidden = true;

    function showCredential() {
      credential.hidden = false;
      credential.replaceChildren();
      const base = apiBase();
      if (!base) {
        const note = document.createElement('p');
        note.textContent = 'Demo mode: no Solana key, so this credential was not broadcast.';
        const link = document.createElement('a');
        link.href = '#/research';
        link.textContent = 'Unlock Real Research';
        credential.append(note, link);
        return;
      }
      mountClaimCredential(credential, {
        apiBase: base,
        learnerId: getLearnerId(),
        alias: 'learner',
        levelsPassed: ['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8'],
      });
      const link = document.createElement('a');
      link.href = '#/research';
      link.textContent = 'Unlock Real Research';
      credential.append(link);
    }

    const board = document.createElement('form');
    if (spec.id === 'L8') {
      board.className = 'card';
      const alias = document.createElement('input');
      alias.type = 'text';
      alias.setAttribute('aria-label', 'Alias');
      alias.placeholder = 'alias';
      const submit = document.createElement('button');
      submit.type = 'submit';
      submit.textContent = 'Submit score';
      const status = document.createElement('p');
      status.textContent = 'Local score (unverified).';
      board.append(alias, submit, status);
      board.addEventListener('submit', (ev) => {
        ev.preventDefault();
        const base = opts?.apiBase || import.meta.env.VITE_API_BASE;
        if (!base) {
          status.textContent = 'Local score (unverified).';
          return;
        }
        const body = {
          challenge: 'readout_pulse',
          learner_id: getLearnerId(),
          alias: alias.value || 'anon',
          score: Number(run.lastResult?.result.snr ?? 0),
          payload: { eps_bins: run.bins, T_us: 1, n_bins: 20 },
        };
        const ctrl = new AbortController();
        const kill = window.setTimeout(() => ctrl.abort(), 3000);
        fetch(`${base.replace(/\/$/, '')}/api/leaderboard`, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify(body),
          signal: ctrl.signal,
        })
          .then(async (res) => {
            window.clearTimeout(kill);
            if (!res.ok) throw new Error('leaderboard');
            const data = (await res.json()) as { rank?: number };
            status.textContent = `Rank ${data.rank ?? '?'}`;
          })
          .catch(() => {
            status.textContent = 'Local score (unverified).';
          });
      });
    }

    // Two-column lesson: left = concept, predict, controls, check, hints, aha; right = badge, views, tutor.
    side.prepend(conceptHost);
    side.append(checkHost, hintHost, ahaHost, codeHost);
    main.prepend(badgeHost);
    main.append(tutor);
    side.classList.add('lesson-main');
    main.classList.add('lesson-aside');
    root.append(header, layout, credential, board);
    paintLocal(run);

    async function launch(active: LevelRun) {
      if (!active.canRun()) return;
      const id = ++seq;
      armed = true;
      root.classList.add('is-busy');
      root.setAttribute('aria-busy', 'true');
      try {
        const outcome = await active.run();
        if (id !== seq) return;
        badge.set(outcome.badge, outcome.banner);
        paintResult(active, outcome);
        finishedRun = true;
        runButton.classList.remove('is-primary');
        checkButton.classList.add('is-primary');
        checkButton.disabled = false;
        const base = apiBase();
        if (base) {
          void logRun(base, runRow(spec.id, getLearnerId(), outcome.source, active.params, outcome.result.summary));
        }
      } catch (error) {
        if (id !== seq) return;
        badge.set('MOCK', error instanceof Error ? error.message : 'Run failed');
      } finally {
        if (id === seq) {
          root.classList.remove('is-busy');
          root.setAttribute('aria-busy', 'false');
        }
      }
    }

    function paintLocal(active: LevelRun) {
      if (spec.id === 'L1') {
        const kind = active.params.state === 'fock' ? 'fock' : 'poisson';
        histogram.update({ kind, alpha: Number(active.params.alpha ?? 0), n: Number(active.params.n ?? 0) });
      }
      if (spec.id === 'L8') pulseExtras.sync(active.bins);
    }

    function paintResult(active: LevelRun, outcome: RunOutcome) {
      const result = outcome.result;
      paintLocal(active);
      const wigner = result.wigner;
      const frame = active.params.mixture === true && result.mixtureW && wigner
        ? { w: result.mixtureW, x: wigner.x, y: wigner.y }
        : wigner?.frames?.[wigner.frames.length - 1]
          ? { w: wigner.frames[wigner.frames.length - 1]!.w, x: wigner.x, y: wigner.y }
          : null;
      if (frame) {
        wignerHost.replaceChildren();
        const canvas = document.createElement('canvas');
        const nx = frame.x.length || Math.round(Math.sqrt(frame.w.length));
        const ny = frame.y.length || nx;
        paintWigner(canvas, frame.w, nx, ny, frame.x, frame.y);
        const axes = document.createElement('p');
        axes.className = 'axis';
        axes.textContent = 'Re α →    Im α ↑';
        wignerHost.append(canvas, axes);
        if (wigner && wigner.frames.length > 1 && active.params.mixture !== true) animate(canvas, wigner.x, wigner.y, wigner.frames);
      } else if (!wignerHost.hidden) {
        const canvas = document.createElement('canvas');
        paintWigner(canvas, [0], 1, 1, [0], [0]);
        wignerHost.replaceChildren(canvas);
      }
      if (spec.id === 'L3' && result.n && result.tUs) {
        histogram.update({ kind: 'pair', t: result.tUs, values: result.n });
      }
      if (result.parity) parity.update(result.parity);
      void drawPlots(plotHost, active, outcome);
      extra.querySelector('[data-part="truncation"]')?.remove();
      if (spec.id === 'L6') extra.append(truncationCard(result));
      if (spec.id === 'L5') extra.append(rateChips(active, outcome));
      if (spec.id === 'L7') extra.append(snrCard(active, outcome));
    }
  }

  render(current);
  return api;
}

function stateOf(run: LevelRun): LevelState {
  return { params: run.params, bins: run.bins, python: run.spec.showCode({ params: run.params, bins: run.bins }) };
}

function animate(canvas: HTMLCanvasElement, x: ArrayLike<number>, y: ArrayLike<number>, frames: { tUs: number; w: ArrayLike<number> }[]) {
  if (prefersStill() || frames.length < 2) return;
  let i = 0;
  const nx = x.length || Math.round(Math.sqrt(frames[0]!.w.length));
  const ny = y.length || nx;
  const timer = window.setInterval(() => {
    const frame = frames[i % frames.length]!;
    paintWigner(canvas, frame.w, nx, ny, x, y);
    i += 1;
  }, 1000 / 30);
  canvas.addEventListener('remove', () => window.clearInterval(timer));
}

async function drawPlots(host: HTMLElement, run: LevelRun, outcome: RunOutcome) {
  const result = outcome.result;
  host.replaceChildren();
  if (run.spec.id === 'L2' && result.tUs && result.n) {
    const kappa = Number(run.params.kappa ?? 0);
    const guide = Array.from(result.tUs, (t) => coherentDecay(4, kappa, Number(t)));
    await plot(host, [
      { x: result.tUs, y: result.n, name: '⟨n⟩' },
      { x: result.tUs, y: guide, name: '4e^{−κt}', dash: 'dash' },
    ], { xlabel: 't (µs)', ylabel: '⟨n⟩' });
  } else if ((run.spec.id === 'L3' || run.spec.id === 'L4') && result.tUs && result.n) {
    const series = [{ x: result.tUs, y: result.n, name: '⟨n⟩' }];
    if (result.parity) series.push({ x: result.tUs, y: result.parity, name: 'parity' });
    await plot(host, series, { xlabel: 't (µs)', ylabel: 'value' });
  } else if (run.spec.id === 'L5') {
    const grid = gridFrom(result, { params: run.params });
    if (!grid) return;
    const xs = grid.gammaX.map((p) => p.alpha2);
    await plot(host, [
      { x: xs, y: grid.gammaX.map((p) => 1 / p.gamma), name: 'T_X (µs)' },
      { x: grid.gammaZ.map((p) => p.alpha2), y: grid.gammaZ.map((p) => 1 / p.gamma), name: 'T_Z (µs)' },
    ], { xlabel: 'α²', ylabel: 'lifetime (µs)', ylog: true });
  } else if (run.spec.id === 'L6' && result.tUs && (result.na || result.n)) {
    const series = [{ x: result.tUs, y: (result.na ?? result.n)!, name: '⟨n_a⟩' }];
    if (result.nb) series.push({ x: result.tUs, y: result.nb, name: '⟨n_b⟩' });
    await plot(host, series, { xlabel: 't (µs)', ylabel: 'population' });
  } else if (run.spec.id === 'L7' && result.signals) {
    const s = result.signals;
    await plot(host, [
      { x: s.tUs, y: s.bPlusRe, name: 'Re ⟨b⟩ valley 0' },
      { x: s.tUs, y: s.bPlusIm, name: 'Im ⟨b⟩ valley 0', dash: 'dash' },
      { x: s.tUs, y: s.bMinusRe, name: 'Re ⟨b⟩ valley 1' },
      { x: s.tUs, y: s.bMinusIm, name: 'Im ⟨b⟩ valley 1', dash: 'dash' },
    ], { xlabel: 't (µs)', ylabel: '⟨b⟩' });
  } else if (run.spec.id === 'L8') {
    const bins = run.bins;
    const mags = dftMagnitude(bins);
    const freq = bins.map((_, k) => k * (1 / 1));
    await plot(host, [{ x: freq.slice(0, 10), y: mags.slice(0, 10), name: 'spectrum' }], {
      xlabel: 'frequency (MHz)',
      ylabel: 'amplitude',
      guides: [{ x: 3.14, name: '3.14 MHz' }],
    });
  }
}

function truncationCard(result: RunOutcome['result']): HTMLElement {
  const card = document.createElement('div');
  card.dataset.part = 'truncation';
  card.className = 'card';
  const meta = result.meta ?? {};
  const topA = Number(meta.top2_a ?? NaN);
  const topB = Number(meta.top_b ?? NaN);
  const line = document.createElement('p');
  const aFlag = Number.isFinite(topA) && topA > 1e-4 ? 'above' : 'under';
  const bFlag = Number.isFinite(topB) && topB > 1e-4 ? 'above' : 'under';
  line.textContent = `Truncation: top two memory levels ${fmt(topA)} (${aFlag} 1e-4), top buffer level ${fmt(topB)} (${bFlag} 1e-4). Live 16×5 peak ${fmt(meta.peak_16x5)} versus the 32×12 reference 6.89 and the 24×6 starter 6.11. The 6.89 number is the documented converged peak, quoted only from that reference.`;
  card.append(line);
  return card;
}

function rateChips(run: LevelRun, outcome: RunOutcome): HTMLElement {
  const wrap = document.createElement('div');
  wrap.className = 'chips';
  const grid = gridFrom(outcome.result, { params: run.params });
  const alpha2 = Number(run.params.alpha2 ?? 0);
  const tx = grid ? logLinear(grid.gammaX, alpha2) : null;
  const tz = grid ? logLinear(grid.gammaZ, alpha2) : null;
  const bias = document.createElement('p');
  bias.textContent = tx && tz ? `Bias T_X/T_Z = ${(tz / tx).toExponential(2)} at α² = ${alpha2.toFixed(2)}.` : 'Bias needs both curves inside the record range.';
  wrap.append(bias);
  for (const point of grid?.gammaX ?? []) {
    if (!point.id || Math.abs(point.alpha2 - alpha2) > 0.75) continue;
    const chip = document.createElement('span');
    chip.textContent = point.id;
    wrap.append(chip);
  }
  return wrap;
}

function snrCard(run: LevelRun, outcome: RunOutcome): HTMLElement {
  const card = document.createElement('p');
  const snr = snrAt(outcome.result, { params: run.params });
  const row = (outcome.result.tradeoff ?? []).find((item) => Math.abs(item.eps - Number(run.params.eps)) < 1e-6);
  card.textContent = `SNR in 1 µs: ${snr == null ? '—' : snr.toFixed(3)}. Relative bit-flip cost: ${row?.gammaXRel?.toFixed(3) ?? '—'}. Harder driving reads faster and disturbs the cat more.`;
  return card;
}

function mountWell(host: HTMLElement, id: LevelId) {
  if (id !== 'L5') return;
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 240 80');
  svg.setAttribute('class', 'well');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', 'Double well: two valleys separated by a barrier. A bit flip hops between them.');
  svg.innerHTML = '<path d="M10 20 C 40 20, 50 70, 80 70 C 110 70, 120 15, 150 70 C 180 70, 190 20, 230 20" fill="none" stroke="#0072b2" stroke-width="3"/><text x="70" y="78" font-size="10">valley 0</text><text x="145" y="78" font-size="10">valley 1</text>';
  host.append(svg);
}

function mountPulse(host: HTMLElement, run: LevelRun, onScore: () => void): { sync: (bins: number[]) => void } {
  if (run.spec.id !== 'L8') return { sync() {} };
  const editor = document.createElement('div');
  editor.className = 'pulse-editor';
  editor.setAttribute('role', 'group');
  editor.setAttribute('aria-label', 'Pulse bars');
  const inputs: HTMLInputElement[] = [];
  const square = (getPreset('L8')?.result.squareBins as number[] | undefined) ?? run.bins;
  const max = Math.max(1, ...square) * 3;
  for (let i = 0; i < 20; i++) {
    const input = document.createElement('input');
    input.type = 'range';
    input.min = '0';
    input.max = String(max);
    input.step = '0.01';
    input.value = String(run.bins[i] ?? square[i] ?? 0);
    input.setAttribute('aria-label', `Pulse bar ${i + 1} of 20`);
    input.addEventListener('input', () => {
      run.setBins(inputs.map((node) => Number(node.value)));
    });
    editor.append(input);
    inputs.push(input);
  }
  const shape = document.createElement('button');
  shape.type = 'button';
  shape.textContent = 'Shape near 3.14 MHz';
  shape.addEventListener('click', () => {
    const TAU = ONE_MHZ;
    const next = square.map((amp, i) => amp * (0.7 + 0.3 * Math.sin((TAU * 3.14 * i) / 20)));
    const fitted = fitPulse(next, square, Number(getPreset('L8')?.result.squareSnr ?? 0.95));
    inputs.forEach((input, i) => { input.value = String(fitted[i] ?? 0); });
    run.setBins(fitted);
  });
  const fit = document.createElement('button');
  fit.type = 'button';
  fit.textContent = 'Fit to budget';
  fit.addEventListener('click', () => {
    const fitted = fitPulse(run.bins, square, Number(getPreset('L8')?.result.squareSnr ?? 0.95));
    inputs.forEach((input, i) => { input.value = String(fitted[i] ?? 0); });
    run.setBins(fitted);
  });
  const note = document.createElement('p');
  note.textContent = 'Score after you predict. If linresp is absent, the badge says MOCK and a flat pulse uses the square prototype. Fit to budget only rescales the bars.';
  host.append(editor, shape, fit, note);
  void onScore;
  return {
    sync(bins) {
      inputs.forEach((input, i) => {
        if (document.activeElement !== input) input.value = String(bins[i] ?? input.value);
      });
    },
  };
}

function fmt(value: unknown): string {
  const n = Number(value);
  return Number.isFinite(n) ? n.toExponential(2) : '—';
}
