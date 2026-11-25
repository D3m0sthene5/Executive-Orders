# Lind (draft v0): a method to minimise the total cost of finishing the remaining work

Named for James Lind, whose 1747 scurvy trial on HMS Salisbury compared six remedies on matched sailors and found the
cheap one that worked.

## Goal

Minimise the expected total cost to bring every remaining order to an end state:
- a verified, adopted dossier; or
- a recorded terminal blocker (no available source can settle it).

Total cost = execution cost (tokens priced by Necker, owner minutes, acquisition dollars and hours) + the cost of the
measurement used to choose how to execute. Human certification is counted separately and never traded off.
Information is bought only where it is expected to lower that total.

## Steps

1. **Fix the unit and the end state.** Every measurement ends at the adopted dossier or the terminal blocker. A unit
   cost is "dollars and owner minutes per order brought to an end state, failures included". It is never "per
   attempt", "per filed" or "per proposal".

2. **Partition all remaining orders at zero token cost** into cells. A cell is defined by:
   (route) × (binding blocker class) × (order kind) × (era).
   - Binding blocker class:
     - source-blocked: a needed source is not held;
     - rule-blocked: an owner ruling would settle it (Polya);
     - token-workable: held sources and existing rules suffice.
   - Classification uses only the tracker, Larrey gates, the dossier features and Polya. Cells are the decision units.

3. **List the options per cell, with an a-priori cost model for each:**
   - process now by the cheapest available producer (script, agent tier, human);
   - acquire the missing source first (microfilm hours, purchase, owner download);
   - ask the owner for a ruling;
   - defer;
   - declare terminal.

4. **Value of information decides what to measure.** For each cell, estimate how likely the current best option is
   wrong, and by how much it would cost if wrong:
   expected loss = P(wrong choice) × cost difference × cell size.
   Sample a cell only when expected loss exceeds the cost of sampling it. Prefer zero-token measurements (back-tests,
   feature counts, rulings) over agent runs.

5. **Measure by random sample within the cell, sequentially.**
   - Draw orders at random, never by ease, so easy pilots cannot set the rate.
   - Start at 10 orders.
   - Stop when the decision is settled (the posterior favours one option with high probability) or the next batch is
     not worth its cost.
   - Prior: the nearest measured cell, discounted.
   - Run the whole chain to the end state: producer, review, rework and adoption, with planted controls.

6. **Version every rate.** A rate is tied to the pipeline version (code hashes of the kit, the route and the triage).
   It expires when that code changes.

7. **Test cross-cutting savers as paired experiments** on the same random orders: a cheaper reviewer, a script
   producer, a triage gate, a ruling. Adopt a saver only when the paired difference is clear.

8. **Register a forecast before every batch and score it after** (Llull), with stop rules (Savigny, Whitworth). A plan
   that misses its forecast by more than its stated error is stopped and diagnosed before more is spent.

9. **Re-plan** after every batch, from the updated cells.
