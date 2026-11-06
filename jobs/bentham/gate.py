"""Bentham gate: after each batch of an agent production wave, say CONTINUE, STOP or PILOT.

Method (consistent with Llull's Raiffa ranking, which also uses a Beta prior centred on a measured base rate):
  1. The yield of the wave (dossiers filed per order attempted) gets a Beta prior whose mean is the measured
     base rate and whose weight equals `prior_strength` pretend attempts (default 20).
  2. Each batch updates it: alpha += filed, beta += attempted - filed.
  3. The wave's value per dollar is yield / cost_per_attempt. The gate computes the probability that this
     exceeds the value per dollar of the next-best action (which the caller takes from Bentham's ranking).
  4. STOP when that probability falls below `stop_below`; STOP at once if any planted control was missed;
     PILOT while fewer than `min_attempts` orders have been attempted (too little data to judge either way).

What the numbers mean: the probability is a statement about the wave's long-run yield under the model, not a
forecast of the next batch. What it does not mean: it ignores fecundity (later dossiers an action unlocks) and
batch-to-batch drift unless you pass `window` (use only the last N batches), which reacts faster to a collapse
that follows a good start. Dollars come from the caller (measured tokens at assumed list prices).

Batch file: JSON list (or {"batches": [...]}) or CSV with columns batch, attempted, submitted, filed,
controls_missed, usd. Missing numeric cells count as 0.
"""
import argparse
import csv
import json
import math
import random
import sys


def posterior(prior_rate, prior_strength, filed, attempted):
    """Beta(alpha, beta) after `filed` successes in `attempted` tries from a prior centred on prior_rate."""
    if not 0 < prior_rate < 1:
        raise ValueError("prior_rate must be strictly between 0 and 1")
    if prior_strength <= 0:
        raise ValueError("prior_strength must be positive")
    if attempted < 0 or filed < 0 or filed > attempted:
        raise ValueError("need 0 <= filed <= attempted")
    return (prior_rate * prior_strength + filed,
            (1 - prior_rate) * prior_strength + attempted - filed)


def _betacf(a, b, x):
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 500):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d; d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c; c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d; d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c; c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-14:
            break
    return h


def beta_cdf(x, a, b):
    """Regularised incomplete beta function I_x(a, b) = P(Beta(a, b) <= x)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    ln_front = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                + a * math.log(x) + b * math.log1p(-x))
    front = math.exp(ln_front)
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1 - front * _betacf(b, a, 1 - x) / b


def beta_quantile(p, a, b):
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if beta_cdf(mid, a, b) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def prob_better(alpha, beta, cost_per_attempt, threshold_value_per_usd, samples=20000, seed=0, method="exact"):
    """P(yield / cost_per_attempt > threshold), yield ~ Beta(alpha, beta).

    method "exact" uses the Beta CDF; "mc" draws `samples` seeded random.betavariate values.
    """
    if cost_per_attempt <= 0:
        raise ValueError("cost_per_attempt must be positive")
    t = threshold_value_per_usd * cost_per_attempt  # break-even yield
    if method == "exact":
        return 1.0 - beta_cdf(t, alpha, beta)
    if method == "mc":
        rng = random.Random(seed)
        return sum(rng.betavariate(alpha, beta) > t for _ in range(samples)) / samples
    raise ValueError("method must be exact or mc")


def decide(batches, prior_rate, prior_strength, cost_per_attempt, next_best_value_per_usd,
           stop_below=0.2, min_attempts=30, window=None, method="exact", samples=20000, seed=0):
    """Return the gate verdict for the batches seen so far (oldest first)."""
    used = list(batches)[-window:] if window else list(batches)
    attempted = sum(int(b.get("attempted") or 0) for b in used)
    filed = sum(int(b.get("filed") or 0) for b in used)
    spent = sum(float(b.get("usd") or 0) for b in used)
    missed = [b.get("batch") for b in used if int(b.get("controls_missed") or 0) > 0]
    a, b = posterior(prior_rate, prior_strength, filed, attempted)
    pb = prob_better(a, b, cost_per_attempt, next_best_value_per_usd, samples, seed, method)
    out = {"posterior_mean": a / (a + b),
           "interval80": [beta_quantile(0.1, a, b), beta_quantile(0.9, a, b)],
           "prob_better": pb, "attempted": attempted, "filed": filed, "spent_usd": spent,
           "breakeven_yield": next_best_value_per_usd * cost_per_attempt}
    if missed:
        d, why = "STOP", f"planted control missed in batch {', '.join(map(str, missed))}; quality failure outranks economics"
    elif attempted < min_attempts:
        d, why = "PILOT", f"only {attempted} of {min_attempts} attempts; too few to judge yield"
    elif pb < stop_below:
        d, why = "STOP", (f"probability the wave beats the next-best action is {pb:.2f}, below {stop_below}")
    else:
        d, why = "CONTINUE", (f"probability the wave beats the next-best action is {pb:.2f}, at least {stop_below}")
    out.update(decision=d, reason=why)
    return out


def load_batches(path):
    with open(path, newline="") as f:
        if str(path).lower().endswith(".csv"):
            rows = list(csv.DictReader(f))
        else:
            rows = json.load(f)
            if isinstance(rows, dict):
                rows = rows["batches"]
    return rows


def verdict_text(r):
    lo, hi = r["interval80"]
    return (f"{r['decision']}: {r['reason']}. Across {r['attempted']} attempts the wave filed {r['filed']} "
            f"(${r['spent_usd']:.2f} spent). The posterior yield is {r['posterior_mean']:.1%} with an 80% interval "
            f"of {lo:.1%} to {hi:.1%}, against a break-even yield of {r['breakeven_yield']:.1%}; the probability "
            f"that the wave beats the next-best action is {r['prob_better']:.2f}.")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--batches", required=True)
    p.add_argument("--prior-rate", type=float, required=True)
    p.add_argument("--prior-strength", type=float, default=20)
    p.add_argument("--cost-per-attempt", type=float, required=True)
    p.add_argument("--next-best", type=float, required=True, help="next-best action's dossiers per USD")
    p.add_argument("--stop-below", type=float, default=0.2)
    p.add_argument("--min-attempts", type=int, default=30)
    p.add_argument("--window", type=int, default=None, help="use only the last N batches")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    r = decide(load_batches(a.batches), a.prior_rate, a.prior_strength, a.cost_per_attempt, a.next_best,
               a.stop_below, a.min_attempts, a.window)
    print(json.dumps(r, indent=2) if a.json else verdict_text(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
