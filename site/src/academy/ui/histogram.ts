import { poisson } from '../formulas';
import { oddEvenPopulations } from '../levels/metrics';

export function mountHistogram(host: HTMLElement): { update: (spec: { kind: 'poisson' | 'fock' | 'pair'; alpha?: number; n?: number; t?: ArrayLike<number>; values?: ArrayLike<number> }) => void } {
  host.replaceChildren();
  const figure = document.createElement('figure');
  figure.className = 'hist';
  const caption = document.createElement('figcaption');
  const bars = document.createElement('div');
  bars.className = 'bars';
  figure.append(bars, caption);
  host.append(figure);

  return {
    update(spec) {
      bars.replaceChildren();
      let pairs: { label: string; p: number }[] = [];
      if (spec.kind === 'fock') {
        pairs = [{ label: `n=${spec.n ?? 0}`, p: 1 }];
        caption.textContent = 'Fock state: one bar, one count.';
      } else if (spec.kind === 'pair' && spec.values && spec.t) {
        const pops = oddEvenPopulations(spec.t, spec.values);
        if (!pops) {
          caption.textContent = 'Still settling. The last 10% of ⟨n⟩ has not flattened, so the |0⟩/|1⟩ split is not shown yet.';
          return;
        }
        pairs = [
          { label: '|0⟩', p: Math.max(0, pops.p0) },
          { label: '|1⟩', p: Math.max(0, pops.p1) },
        ];
        caption.textContent = 'Only |0⟩ and |1⟩ survive pair loss. P(1) = ⟨n⟩∞ when the trace has settled. Populations are not exported by the solver yet.';
      } else {
        const mu = (spec.alpha ?? 0) ** 2;
        for (let n = 0; n <= 12; n++) pairs.push({ label: String(n), p: poisson(n, mu) });
        caption.textContent = `Poisson histogram for ⟨n⟩ = ${mu.toFixed(2)}. The height is the chance of that count.`;
      }
      const max = Math.max(0.01, ...pairs.map((p) => p.p));
      for (const pair of pairs) {
        const col = document.createElement('div');
        col.className = 'bar-col';
        const bar = document.createElement('div');
        bar.className = 'bar';
        bar.style.height = `${(pair.p / max) * 100}%`;
        bar.title = `${pair.label}: ${pair.p.toFixed(3)}`;
        const lab = document.createElement('span');
        lab.textContent = pair.label;
        col.append(bar, lab);
        bars.append(col);
      }
    },
  };
}
