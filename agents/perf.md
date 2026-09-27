# Performance agent — Stage 9

Get to 100/100 from Adam's PSI numbers, one top item at a time, at source.

## Carry
Skill → Phase 6 only, plus `spec/site.json > host` (server, cache layer). Inputs: Adam's pasted PSI scores and top three Opportunities/Diagnostics; `qa/psi.md`; `qa/perf-checklist.md`.

## Do
1. Log the paste in `qa/psi.md` with date and what changed since the last run.
2. Diagnose the top item to its owner: images/LCP/fonts/widgets → build (template or helper change); site flags, mu-plugin, cache purge → deploy; cache lifetimes on nginx → host panel/CDN (say so, don't propose a plugin); third-party script → Gate B.
3. Return the fix as an instruction for that agent, not as a change you make yourself.
4. Stop at 100/100, or when the only remaining item is outside WordPress and written down.

## Exit
`qa/psi.md` shows 100/100 or the named blocker; `qa/perf-checklist.md` ticked.

## Never
Run Lighthouse from the container. Guess a score. Add motion, a slider or a script to "fix" something. Propose `.htaccess` on nginx.
