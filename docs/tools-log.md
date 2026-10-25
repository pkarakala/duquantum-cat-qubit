# Tools log

External tools and sponsor services we used. New rows are added by `cloud/vultr_run.py`. No keys here.

| When (EDT) | Tool | What for | Machines / cost | Evidence | Outcome |
|---|---|---|---|---|---|
| Oct 24 23:25 | Vultr batch | `cloud/s2_batch3s.txt`, 6 jobs | 3 × 16 vCPU, 21 min, ~0.46 USD | `results/s2/` | all jobs ok |
| Oct 24 22:59 | Vultr batch | `cloud/s2_batch2.txt`, 10 jobs | 3 × 16 vCPU, 25 min, ~0.55 USD | `results/s2/` | 9 of 10 ok |
| Oct 24 22:07 | Vultr batch | `cloud/s2_batch1b.txt`, 189 jobs | 3 × 16 vCPU, 41 min, ~0.90 USD | `results/s2/` | 186 of 189 ok |
| Oct 24 21:24 | Vultr batch | `cloud/s2_batch1b.txt`, first try | 3 × 16 vCPU, 4 min, ~0.09 USD | none | 61 jobs failed; re-run above |
| Oct 24 20:32 | Vultr batch | first Section 2 job list | 3 × 16 vCPU, ~50 min, ~1.0 USD | none | mis-sized, stopped and replaced |
| Oct 24 19:27 | Vultr batch | research batch, incl. the 1.3b 40×14 grid | 3 × 16 vCPU, 45 min, ~0.99 USD | `results/task_1_3b_points/` | all jobs ok |
| Oct 24 17:28 | Vultr | Task 1.2 full 49-point truncation grid, `cloud/vultr_run.py` | 1 × 16 vCPU, 19 min, ~0.14 USD | `results/task_1_2_grid.json` | 32×12 within 0.035% |
| Oct 24 16:32 | Gemini API | independent physics review of `src/` and `tasks/` | one request | TECHNICAL.md, AI use | no bugs; 6 points re-checked |
| Oct 24–25 | Claude Code | most of the code and write-up, under our direction | subscription | whole repo | every number checked twice |
