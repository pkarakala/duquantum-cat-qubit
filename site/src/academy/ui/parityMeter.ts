export function mountParity(host: HTMLElement): { update: (values: ArrayLike<number> | undefined) => void } {
  host.replaceChildren();
  const wrap = document.createElement('div');
  wrap.className = 'parity';
  const meter = document.createElement('div');
  meter.className = 'parity-track';
  meter.setAttribute('role', 'meter');
  meter.setAttribute('aria-valuemin', '-1');
  meter.setAttribute('aria-valuemax', '1');
  const fill = document.createElement('div');
  fill.className = 'parity-fill';
  meter.append(fill);
  const text = document.createElement('p');
  wrap.append(meter, text);
  host.append(wrap);
  return {
    update(values) {
      if (!values || !values.length) {
        text.textContent = 'Parity has not been computed yet.';
        meter.setAttribute('aria-valuenow', '0');
        return;
      }
      const last = Number(values[values.length - 1]);
      let lo = Infinity;
      let hi = -Infinity;
      for (let i = 0; i < values.length; i++) {
        const v = Number(values[i]);
        if (v < lo) lo = v;
        if (v > hi) hi = v;
      }
      const frozen = hi - lo < 1e-3;
      const pos = ((last + 1) / 2) * 100;
      fill.style.width = `${Math.min(100, Math.max(0, pos))}%`;
      meter.setAttribute('aria-valuenow', last.toFixed(3));
      meter.setAttribute('aria-valuetext', `parity ${last.toFixed(3)}${frozen ? ', frozen' : ''}`);
      text.textContent = frozen
        ? `Parity ${last.toFixed(3)} and it is not moving. Even stays even.`
        : `Parity ${last.toFixed(3)}. It started at ${Number(values[0]).toFixed(3)}.`;
    },
  };
}
