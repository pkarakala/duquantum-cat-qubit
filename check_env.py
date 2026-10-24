"""Run this first: python check_env.py
Confirms dynamiqs + JAX work and shows which devices are available."""
import time
import jax
import jax.numpy as jnp
import dynamiqs as dq

print("JAX devices:", jax.devices())
print("dynamiqs version:", getattr(dq, "__version__", "unknown"))

n = 15
a = dq.destroy(n)
t = jnp.linspace(0, 3, 50)
L2 = jnp.sqrt(1.0) * (a @ a - 4.0 * dq.eye(n))
start = time.time()
res = dq.mesolve(dq.zeros(n), [L2], dq.fock(n, 0), t, exp_ops=[a.dag() @ a])
print(f"mesolve OK in {time.time() - start:.2f}s, final <n> = {float(res.expects[0, -1].real):.3f} (expect ~4)")
