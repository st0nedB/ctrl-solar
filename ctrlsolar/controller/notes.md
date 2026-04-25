# Controller
Objective : plan the whole day based on current forecast
split the day into two phases

## Proposal for Phases
  - Phase 1 produces as much as possible, while maximizing storage 
    - P_min = const.
      - when plant produces more, the phase activates
      - when less, the phase deactivates
    - P_max = legal limit
    - P_target = Expected energy production for upcoming hour / 1h
    - start: when Prod > P_min
    - stop: when Prod < P_min
  - Phase 2 is characterized by a constant power
    - Power = const.
    - Power is determined by available battery energy when phase starts

## Phase 1: Solar-powered Phase
### Goal:
  Maximize solar energy for self-consumption.
  -> Satisfy phase standby demand
  -> Ensure enough excess energy for Phase 2 is stored
  -> Provide any surplus to public grid
### Constraints:
  - Maximum Power: The legal upper limit 
    Guideline: The legal upper limit your microinverter may supply.
  - Target Power: The target for power production.
    Guideline: What you can supply while still charging full.
  - Minimum Power: A minimum power requirement. 
    Guideline: Switches off the plant and just charges battery. Useful in winter.
### Thoughts:
  - Predict power production and battery charge state 
  - Goal: Maximize battery charge state, given target power production
  - How do we do that?
      -> Set the minimum target power, such that the batteries are fully charged by the end of the phase! (Phase 2 maximization!)
      -> If this power target < minimum power: 
          - charge only batteries
      -> If this power target > maximum power:
          - set to maximum power 
  
### Proposal
At each full hour:
   1. Assume you keep Max_Limit from now until Phase 1 end.
   2. Compute whether the battery still ends above the required threshold.
      2.1 If yes, use Max_Limit this hour.
      2.2 If no, compute the smallest target reduction that makes the remaining plan feasible. See below for details
   3. Apply and wait for next update.

#### Proposal for smalles target reduction:
- How much energy will be missing from the batteries at the end of phase 1? -> Missing_Energy
- How many hours are remaining? -> Remaining_Hours
- Target_Power = Max_power - (Missing_Energy / Remaining_Hours) 

## Phase 2: Storage-powered Phase
### Goal: 
Provide a constant power level during solar inavailability
Contraints: 
    Minimum Power: A minimum power. If None, 100W.
        Guideline: Lower limit of standby production.
        Maximum Power: A maximum power. If None, 800W.
        Guideline: Upper limit of standby production.
  Future Improvements:
      - Constraints can be measured and calibrated automatically.