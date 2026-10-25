/** One level run: concept → predict → play → check → aha. Run stays closed until the first choice. */

import { emit } from './events';
import { buildDetectKeys, runLevelSim, type RunOpts } from './sources';
import { saveProgress } from './progress';
import type { LevelSpec, LevelState, Phase, RunOutcome } from './types';

export interface Prediction {
  optionId: string;
  correct: boolean;
  misconceptionId?: string;
  firstTry: boolean;
}

type Listener = () => void;

export interface LevelRun {
  spec: LevelSpec;
  phase: Phase;
  params: Record<string, number | string | boolean>;
  bins: number[];
  prediction?: Prediction;
  misconceptionIds: string[];
  hintLevel: number;
  attempts: number;
  failedChecks: number;
  lastResult?: RunOutcome;
  detectKeys: string[];
  followUp?: string;
  canRun(): boolean;
  choose(optionId: string): void;
  chooseFollowUp(optionId: string): void;
  setParam(name: string, value: number | string | boolean): void;
  setBins(bins: number[]): void;
  run(): Promise<RunOutcome>;
  check(): { pass: boolean; message: string };
  answerFollowUp(text: string): { pass: boolean; message: string };
  showHint(): number;
  solutionVisible(): boolean;
  subscribe(fn: Listener): () => void;
}

function initialParams(spec: LevelSpec): Record<string, number | string | boolean> {
  const params: Record<string, number | string | boolean> = {};
  for (const control of spec.controls) {
    if (control.initial != null) params[control.name] = control.initial;
    else if (control.type === 'range') params[control.name] = control.min ?? 0;
    else if (control.type === 'toggle') params[control.name] = false;
    else if (control.options?.[0]) params[control.name] = control.options[0].value;
  }
  return params;
}

export function createLevelRun(spec: LevelSpec, opts?: { apiBase?: string; runSim?: typeof runLevelSim }): LevelRun {
  const listeners = new Set<Listener>();
  const notify = () => {
    for (const fn of listeners) fn();
  };
  const run: LevelRun = {
    spec,
    phase: 'concept',
    params: initialParams(spec),
    bins: [],
    misconceptionIds: [],
    hintLevel: 0,
    attempts: 0,
    failedChecks: 0,
    detectKeys: [],
    canRun() {
      return Boolean(run.prediction);
    },
    choose(optionId: string) {
      if (run.prediction) {
        notify();
        return;
      }
      const option = spec.predict.options.find((item) => item.id === optionId);
      if (!option) return;
      const prediction: Prediction = { optionId, correct: option.correct, firstTry: true };
      if (option.misconception) {
        prediction.misconceptionId = option.misconception;
        run.misconceptionIds = [option.misconception];
      }
      run.prediction = prediction;
      run.phase = 'play';
      emit('prediction', {
        levelId: spec.id,
        optionId,
        correct: option.correct,
        ...(option.misconception ? { misconceptionId: option.misconception } : {}),
        firstTry: true,
      });
      notify();
    },
    chooseFollowUp(optionId: string) {
      run.followUp = optionId;
      const option = spec.predictFollowUp?.options.find((item) => item.id === optionId);
      if (option?.misconception && !run.misconceptionIds.includes(option.misconception)) {
        run.misconceptionIds = [...run.misconceptionIds, option.misconception];
      }
      notify();
    },
    setParam(name, value) {
      run.params = { ...run.params, [name]: value };
      if (name === 'build') run.detectKeys = buildDetectKeys(String(value));
      notify();
    },
    setBins(bins) {
      run.bins = bins.slice();
      notify();
    },
    async run() {
      if (!run.canRun()) throw new Error('Choose a prediction before running.');
      const state: LevelState = {
        params: run.params,
        detectKeys: run.detectKeys,
        bins: run.bins,
        tree: undefined,
      };
      const runSim = opts?.runSim ?? runLevelSim;
      const simOpts: RunOpts = {};
      if (opts && Object.prototype.hasOwnProperty.call(opts, 'apiBase')) simOpts.deps = { apiBase: opts.apiBase };
      const outcome = await runSim(spec, state, simOpts);
      run.lastResult = outcome;
      run.phase = 'play';
      emit('sim', { levelId: spec.id, source: outcome.source, params: run.params, summary: outcome.result.summary ?? '' });
      notify();
      return outcome;
    },
    check() {
      const result = run.lastResult?.result ?? {};
      const state: LevelState = {
        params: run.params,
        detectKeys: run.detectKeys,
        records: result.records,
        snr: typeof result.snr === 'number' ? result.snr : undefined,
        cost: typeof result.cost === 'number' ? result.cost : undefined,
        snrSquare: typeof result.snrSquare === 'number' ? result.snrSquare : undefined,
        costSquare: typeof result.costSquare === 'number' ? result.costSquare : undefined,
        tradeoff: result.tradeoff,
        bins: run.bins,
      };
      const verdict = spec.check.fn(result, state);
      run.attempts += 1;
      emit('check', { levelId: spec.id, pass: verdict.pass, attempt: run.attempts, message: verdict.message });
      if (verdict.pass) {
        emit('pass', { levelId: spec.id, attempts: run.attempts, predictionCorrect: Boolean(run.prediction?.correct) });
        saveProgress(spec.id, {
          passed: true,
          predictionCorrect: Boolean(run.prediction?.correct),
          attempts: run.attempts,
          ts: Date.now(),
        });
        run.phase = 'aha';
      } else {
        run.failedChecks += 1;
        run.phase = 'check';
      }
      notify();
      return verdict;
    },
    answerFollowUp(text: string) {
      const fn = spec.checkFollowUp?.fn;
      if (!fn) return { pass: false, message: 'This level has no follow-up.' };
      return fn(text);
    },
    showHint() {
      if (run.hintLevel < 4) run.hintLevel += 1;
      emit('hint', { levelId: spec.id, hintLevel: run.hintLevel });
      notify();
      return run.hintLevel;
    },
    solutionVisible() {
      return run.failedChecks >= 2;
    },
    subscribe(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    },
  };
  return run;
}
