---
title: Trajectory
toc: false
---

# The project's trajectory

Verified work held, in work-hours, one point per day (Tsiolkovsky's end-of-day series). No human certification is
credited; this is a measure of machine and source work, not of certified dossiers.

```js
const traj = await FileAttachment("data/TRAJECTORY.csv").csv({typed: true});
const points = await FileAttachment("data/GENERATION_POINTS.csv").csv({typed: true});
const mission = await FileAttachment("data/MISSION.csv").csv({typed: true});
const last = traj.at(-1);
const fmt = d3.format(",.0f");
```

<style>.big{font-size:1.6rem;font-weight:700}</style>

<div class="grid grid-cols-4">
  <div class="card"><h2>Work held</h2><span class="big">${fmt(last.W_hours)} h</span></div>
  <div class="card"><h2>Share of mission</h2><span class="big">${d3.format(".1%")(last.p)}</span></div>
  <div class="card"><h2>Phase</h2><span class="big">${last.phase}</span></div>
  <div class="card"><h2>Ready for human review</h2><span class="big">${fmt(last.ready)}</span></div>
</div>

## Work held, with the sensitivity band

```js
const showBand = view(Inputs.toggle({label: "Show the low-high band", value: true}));
```

```js
display(resize((width) => Plot.plot({
  width,
  height: 300,
  y: {grid: true, label: "work-hours", domain: [0, d3.max(traj, (d) => d.W_high_hours) * 1.05]},
  x: {label: null},
  marks: [
    showBand ? Plot.areaY(traj, {x: "date", y1: "W_low_hours", y2: "W_high_hours", fillOpacity: 0.25}) : null,
    Plot.lineY(traj, {x: "date", y: "W_hours", strokeWidth: 2}),
    Plot.dot(traj, {x: "date", y: "W_hours", tip: true})
  ]
})));
```

## Where the work sits, by step

```js
const stepColumns = [
  ["W_census_hours", "census"],
  ["W_provisional_status_hours", "provisional status"],
  ["W_original_text_hours", "original text"],
  ["W_clause_inventory_hours", "clause inventory"],
  ["W_ending_or_current_basis_hours", "ending or current basis"],
  ["W_savings_residuals_hours", "savings and residuals"],
  ["W_counterevidence_hours", "counterevidence"],
  ["W_shared_sources_hours", "shared sources"],
  ["W_opus_media_hours", "opus media"]
];
const byStep = traj.flatMap((d) => stepColumns.map(([col, step]) => ({date: d.date, step, hours: d[col]})));
```

```js
display(resize((width) => Plot.plot({
  width,
  height: 320,
  color: {legend: true, scheme: "tableau10"},
  y: {grid: true, label: "work-hours"},
  x: {label: null},
  marks: [Plot.areaY(byStep, {x: "date", y: "hours", fill: "step", tip: true}), Plot.ruleY([0])]
})));
```

## Dossiers ready, and claims filed

```js
display(resize((width) => Plot.plot({
  width,
  height: 260,
  color: {legend: true, domain: ["ready", "claims"]},
  y: {grid: true, label: "orders"},
  x: {label: null},
  marks: [
    Plot.lineY(traj, {x: "date", y: "claims", stroke: Plot.valueof(traj, () => "claims")}),
    Plot.lineY(traj, {x: "date", y: "ready", stroke: Plot.valueof(traj, () => "ready")}),
    Plot.tip(traj, Plot.pointerX({x: "date", y: "ready"}))
  ]
})));
```

## Velocity: work-hours gained per day

```js
display(resize((width) => Plot.plot({
  width,
  height: 240,
  y: {grid: true, label: "hours per day"},
  x: {label: null},
  marks: [Plot.rectY(traj, {x: "date", interval: "day", y: "v_hours_per_day", tip: true}), Plot.ruleY([0])]
})));
```

## Every tracker generation

Each dot is one published readiness-tracker generation, placed by when it landed on main (${points.length} readings).

```js
display(resize((width) => Plot.plot({
  width,
  height: 260,
  y: {grid: true, label: "work-hours"},
  x: {label: null},
  marks: [Plot.dot(points, {x: "landed_utc", y: "W_hours", r: 3, tip: true})]
})));
```

## Mission milestones

The rocket dashboard's milestones, placed on the same scale.

```js
display(Inputs.table(mission, {
  columns: ["event", "met_hours", "p", "W_hours", "phase_after"],
  header: {event: "Event", met_hours: "Mission hours", p: "Share", W_hours: "Work-hours", phase_after: "Phase after"},
  format: {p: d3.format(".1%"), W_hours: fmt, met_hours: d3.format(".1f")}
}));
```
