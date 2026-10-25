# Cat qubits: bit flips, phase flips and a better readout

**DuQuantum 2026 · Alice & Bob challenge · Standard track**
Team: Pranav Reddy, Harshit Aggarwal, Halo Kwok, Xuanyu Zhu

<p align="center"><img src="figures/task_1_1_wigner.gif" width="360" alt="Cat qubit forming in the two-mode model"></p>

## The challenge

| | Write-up |
|---|---|
| **Task 1**: stabilize a cat qubit, check convergence, prepare a logical state | [docs/task_1.md](docs/task_1.md) |
| **Task 2**: bit flips, phase flips, buffer readout, a better readout | [notebooks 06–09](notebooks/) · [docs/TECHNICAL.md](docs/TECHNICAL.md) |

## Run it

```bash
pip install -r requirements.txt
./run_all.sh      # every number is also saved as JSON in results/
```

## How we used AI and tools

- **Claude Code** did most of the implementation and drafted the write ups, under our direction.
- **Codex** helped with Section 1 validation, convergence analysis, figures and the brute force Task 2.1/2.2 simulations.
- **Gemini** checked the physics in the code and validated the plots (`tools/ai_review.py`; log in [`reviews/`](reviews/)).
- **Vultr** ran our large simulation batches in the cloud for about 5 USD in total ([tools log](docs/tools-log.md)).
- **Cursor** and a **Groq**-powered bot are used for the product layer.

We checked every result against a hand prediction or a second method.
