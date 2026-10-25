/** ExprTree builders for the sim requests. Evaluation lives in P1, not here. */

export const num = (value: number) => ({ op: 'num' as const, value });
export const sym = (name: string) => ({ op: 'sym' as const, name });
export const mul = (...args: unknown[]) => ({ op: 'mul' as const, args });
export const pow = (base: unknown, exp: number) => ({ op: 'pow' as const, base, exp });
export const sqrt = (arg: unknown) => ({ op: 'sqrt' as const, arg });
