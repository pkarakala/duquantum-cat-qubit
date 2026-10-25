import { describe, expect, it } from 'vitest';
import md from '../../../../docs/product/LEVELS.md?raw';
import { LEVELS } from '../levels';
import { allPresets, getPreset } from '../presets';

function sections(source: string): { id: string; body: string }[] {
  const chunks = source.split(/\n## (L\d) · /).slice(1);
  const out: { id: string; body: string }[] = [];
  for (let i = 0; i < chunks.length; i += 2) out.push({ id: chunks[i] ?? '', body: chunks[i + 1] ?? '' });
  return out;
}

function cleanOption(line: string): { id: string; text: string; correct: boolean; misconception?: string } {
  const match = line.match(/\s+- (?:\*\*)?([A-D])\)\s*(.+)/);
  if (!match) throw new Error(line);
  let rest = match[2] ?? '';
  const feedbackAt = rest.indexOf('Feedback:');
  if (feedbackAt >= 0) rest = rest.slice(0, feedbackAt);
  const mis = rest.match(/\(M(\d)\)/);
  rest = rest.replace(/\s*\(M\d\)/g, '');
  const correct = rest.includes('(correct)');
  rest = rest.replace(/\s*\(correct\)/g, '');
  rest = rest.replace(/\*\*/g, '');
  rest = rest.replace(/\s+/g, ' ').trim();
  rest = rest.replace(/\s+(This is|That breaks)\b.*/g, '');
  rest = rest.trim().replace(/\.$/, '');
  return { id: match[1] ?? '', text: rest, correct, ...(mis ? { misconception: `M${mis[1]}` } : {}) };
}

function parse(body: string) {
  const title = body.match(/^(.+?) \(\d+ min\)/)?.[1] ?? '';
  const question = body.match(/\*\*Predict:\*\* "([^"]+)"/)?.[1] ?? '';
  const options: ReturnType<typeof cleanOption>[] = [];
  let inPredict = false;
  for (const line of body.split('\n')) {
    if (line.includes('**Predict:**')) {
      inPredict = true;
      continue;
    }
    if (inPredict && line.startsWith('- **')) break;
    if (inPredict && /^\s+- (?:\*\*)?[A-D]\)/.test(line)) options.push(cleanOption(line));
  }
  const goal = (body.match(/\*\*Check(?:, part 1)?:\*\* "([^"]+)"/)?.[1] ?? '').replace(/\*\*/g, '');
  const hints = [...body.matchAll(/\n\s+\d\. "([^"]+)"/g)].map((m) => m[1] ?? '');
  const ahaBlock = body.match(/- \*\*Aha:\*\*\s*([\s\S]+?)(?=\n- \*\*Show code)/)?.[1] ?? '';
  const aha = [...ahaBlock.split(/\n-\s+\*\*On completion:\*\*/)[0]!.matchAll(/"([^"]*)"/g)].map((m) => m[1]).join('\n');
  const allowedLine = body.match(/\*\*Allowed constants:\*\* (.+)/)?.[1] ?? '';
  const allowed = [...allowedLine.matchAll(/\d+(?:\.\d+)?/g)].map((m) => Number(m[0]));
  const preset = body.match(/\*\*Preset:\*\* `([^`]+)`/)?.[1] ?? '';
  const sourcesLine = (body.match(/\*\*Sources:\*\* (.+)/)?.[1] ?? '').trim().replace(/\.$/, '');
  const sources = sourcesLine.split(',').map((part) => part.trim().replace(/`/g, '').replace(/\.$/, '')).filter(Boolean);
  const follow = body.match(/Follow-up question: "([^"]+)".*?The answer is "([^"]+)"/);
  return { title, question, options, goal, hints, aha, allowed, preset, sources, follow };
}

describe('level content matches LEVELS.md', () => {
  const parsed = new Map(sections(md).map((section) => [section.id, parse(section.body)]));

  it('matches every level verbatim and stays inside the structure rules', () => {
    expect(LEVELS.map((level) => level.id)).toEqual(['L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8']);
    for (const spec of LEVELS) {
      const fromDoc = parsed.get(spec.id);
      expect(fromDoc, spec.id).toBeTruthy();
      expect(spec.title).toBe(fromDoc?.title);
      expect(spec.predict.question).toBe(fromDoc?.question);
      expect(spec.predict.options.map((option) => option.text)).toEqual(fromDoc?.options.map((option) => option.text));
      expect(spec.predict.options.map((option) => option.misconception ?? null)).toEqual(
        fromDoc?.options.map((option) => option.misconception ?? null),
      );
      expect(spec.check.goal).toBe(fromDoc?.goal);
      expect([...spec.hints]).toEqual(fromDoc?.hints);
      expect(spec.aha).toBe(fromDoc?.aha);
      expect(new Set(spec.allowedConstants)).toEqual(new Set(fromDoc?.allowed));
      expect(spec.preset).toBe(fromDoc?.preset);
      expect(spec.sources).toEqual(fromDoc?.sources);
      expect(spec.predict.options.filter((option) => option.correct)).toHaveLength(1);
      expect(spec.controls.filter((control) => !control.revealAtHint).length).toBeLessThanOrEqual(3);
      expect(spec.controls.length).toBeLessThanOrEqual(3);
      for (const option of [...spec.predict.options, ...(spec.predictFollowUp?.options ?? []), ...(spec.checkFollowUp?.options ?? [])]) {
        if (option.misconception) expect(option.misconception).toMatch(/^M[1-7]$/);
      }
      if (fromDoc?.follow) {
        expect(spec.predictFollowUp?.question).toBe(fromDoc.follow[1]);
        expect(spec.predictFollowUp?.options.some((option) => option.correct && option.text === fromDoc.follow?.[2])).toBe(true);
      }
      expect(getPreset(spec.preset)).toBeTruthy();
    }
  });

  it('keeps the preset bundle under 2 MB', () => {
    const raw = import.meta.glob('../presets/*.json', { eager: true, query: '?raw', import: 'default' }) as Record<string, string>;
    const bytes = Object.values(raw).reduce((sum, file) => sum + new TextEncoder().encode(file).length, 0);
    expect(Object.keys(raw).length).toBeGreaterThan(0);
    expect(bytes).toBeLessThan(2_000_000);
    expect(allPresets().length).toBeGreaterThanOrEqual(8);
  });
});
