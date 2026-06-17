---
type: reference
title: Multi-Sided Marketplace & Product Discovery
description: Reference guide for multi-sided marketplace discovery and cold-start tactics.
version: "1.0.1"
---

# Multi-Sided Marketplace & Product Discovery


This reference describes the discovery, validation, and cold-start strategies for multi-sided products (e.g., marketplaces, networks). Use this during concept framing (`1b`) to grill both sides of the network and design the initial liquidity loop.

---

## 1. Both-Sides Discovery & Acquisition
A multi-sided product must discover the pains, motivations, and entry points for **each distinct side** (typically Demand/Buyers and Supply/Sellers).
- Grilling must address both sides independently.
- The RAT (Riskiest Assumption Test) must validate both sides (e.g., 10 DMs to supply actors AND 10 DMs to demand actors).
- **Per-side Opportunity Scoring:** Must be conducted in `1a` (Research) using the evidence standards. `1b` flags both sides but does not assign speculative opportunity numbers without evidence.

---

## 2. The 7 Cold-Start Tactics
To overcome the "chicken-and-egg" problem, select and apply at least one of these cold-start tactics:

1. **Single-Player Mode First:** Create immediate value for one side of the market without requiring the other side to be present (e.g., tool-utility first, network second).
2. **Start Absurdly Narrow:** Constrain the launch to an extremely small niche (e.g., one city, one campus, one specific team) to quickly reach critical mass.
3. **Hold Network Behind a Threshold:** Do not open the network until a certain number of users sign up (e.g., "unlock when 50 coworkers join").
4. **Seed the Hard Side by Hand:** Manually recruit and curate the initial supply or demand to ensure high quality and initial activity.
5. **Seed Supply Honestly (Never Fake Demand):** Aggregate or manually input high-quality supply listings yourself, but never simulate fake demand (which destroys trust when suppliers realize it).
6. **Minimum Liquidity Threshold:** Define the exact numbers required to make the room feel alive (e.g., "10 active listings in Seattle before opening Seattle demand").
7. **Pick Which Side First:** Identify which side is harder to acquire (usually supply) and focus initial acquisition efforts there.

---

## 3. The Empty-Room Failure Note
The biggest risk for a multi-sided product is the **Empty Room**. If a user signs up and finds no listings, no activity, or no matches, they leave and never return. 
- You must identify the **Minimum Liquidity Threshold** and hold back demand until that threshold is crossed.
- Design a single, cheap loop metric to measure liquidity.

---

## 4. Single Cheap Loop Metric
Focus on a single, actionable metric that measures network health:
- **Primary Liquidity Metric:** The percentage of new users who experience a successful interaction or transaction within their first week (or the share of new users that came from an existing user's activity).
