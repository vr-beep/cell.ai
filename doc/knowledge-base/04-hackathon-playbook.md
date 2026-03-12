# Hackathon Playbook: Winning Strategies for the Monomer Bio Hack

> Research compiled March 11, 2026. Sources cited inline.

---

## 1. Previous Monomer Bio Hackathons

### June 2025 Hack (SF Deep Tech Week)
- Projects: chatbots, AR tools, LC optimization, digital twins, pandemic monitoring, organoid analysis
- Organizer called it "by far the most impressive one because of the confluence of tools, skills and factors"
- Participants flew in from Boston, Denver, Seattle, Houston
- Most lacked prior lab automation or MCP experience
- Tech stack: MCP servers, Cursor, Claude, Opentrons AI, Nvidia Omniverse, RAG
- Source: https://labautomation.io/t/san-francisco-mcp-build-day-june-14th-ai-x-lab-automation-hackathon-june-21st-recap-inside/6155

### October 2025 Hack
- Challenge: "How quickly can you onboard an unfamiliar cell culture by leveraging an AI Scientist?"
- Hardware: Opentrons Flex and OT-2
- No winners publicly posted
- Source: https://labautomation.io/t/24hr-ai-science-cell-culture-hack-monomer-bio-luma-sf-bay-area/6588

**Key insight:** No public record of previous winners' approaches. Judges value novelty and the "wow factor" of a closed-loop system working live.

---

## 2. iGEM Precedent: V. natriegens

**Team Marburg won the iGEM Grand Prize** by establishing *V. natriegens* as a new chassis organism. Their pitch: "7-minute doubling time enables a full cloning cycle in 12 hours."

This validates that V. natriegens optimization is a proven winning topic. The organism itself is the story.

Source: https://www.promegaconnections.com/igem-marburg-grand-prize/

---

## 3. What Judges Look For

From 5 seasoned Devpost judges:

| Judge | Key Insight |
|-------|------------|
| **Richard Moot (Square)** | "A project that really stands out is one clearly considering the judging criteria." Start building immediately to discover unknowns. |
| **Karen Bajza-Terlouw (Databricks)** | Wants code and technical depth, not polished UI with no substance. |
| **Kelvin Boateng (Google)** | Values departing from templates. Storytelling elevates submissions. |
| **Maria Yarotska (NEAR)** | Looks for "unusual and fresh approach" and "fire in their eyes." |
| **Warren Marusiak (Atlassian)** | "Is that finished product something I would want to use?" |

**Core principles:**
- Show, don't tell. Every claim must be backed by demo or data.
- Build demo script backward: start with impressive ending, work backward to minimal steps.
- Never waste demo time debugging. Have a pre-recorded backup video.
- While demoing visuals, talk about what you CANNOT see (backend logic, AI reasoning).
- Quantify: "Our optimized media achieved 2.3x the growth rate of the baseline."

Sources:
- https://angelhack.com/blog/10-tips-to-help-you-rock-your-next-hackathon-demo/
- https://info.devpost.com/blog/hackathon-judging-tips

---

## 4. Common Hackathon Mistakes

1. **Over-engineering:** Building production-ready code instead of a working demo
2. **Late demo prep:** "About half an hour before hacking ends, stop everything. Take out everything that doesn't work."
3. **Scope creep:** Mid-hackathon realization that the solution is too complicated to demo
4. **Polished UI, no substance:** Judges see through pretty wrappers with minimal code
5. **Ignoring judging criteria:** Building something cool that doesn't address the actual prompt
6. **Too much time on logos/design:** "You'd be surprised how easy it is to fall into this trap"
7. **Technical jargon overload:** "Judges zone out. Explain complexity in simple terms."
8. **No fallback plan:** If live demo crashes, having nothing to show is devastating
9. **Not practicing the pitch:** Mental rehearsal fails. Must speak it aloud.
10. **Not sleeping:** "Hackathons aren't marathons, they're relay races." The pitcher needs 2-3 hours of rest.

Sources:
- https://sigma.software/about/media/8-mistakes-definitely-help-you-screw-hackathon
- https://theinnovationmode.com/the-innovation-blog/survival-guide-for-hackathon-participants

---

## 5. Demo Format: "One Slide, Four Numbers"

One summary slide with four hero numbers (48pt+ font, one-line explanation each):

1. **Rounds completed** — "Our agent ran N closed loops with zero human intervention"
2. **Best growth rate vs. baseline** — "Our AI's best recipe outperformed initial media by X%"
3. **Growth rate improvement** — "Cell growth rate improved Y% from round 1 to round N"
4. **Conditions explored** — "The system designed, executed, and learned from Z unique media recipes"

**Why this works:**
- Judges see dozens of demos and remember concrete numbers
- Proves the system actually worked (not vaporware)
- Creates natural "before vs. after" narrative

Sources:
- https://slidemodel.com/how-to-present-key-metrics/
- https://guykawasaki.com/the-only-10-slides-you-need-in-your-pitch/

---

## 6. The "Golden Ratio" Pitch (2 minutes)

- **30 seconds:** Problem/solution
- **60 seconds:** Live demo
- **30 seconds:** Results / next steps

---

## 7. Head-to-Head Differentiation

When competing against another team on the same track:

- **Narrative framing > features:** When both teams have similar tech, the better story wins. Frame as "autonomous science" or "the AI scientist that learns from its own experiments."
- **Show what they cannot:** If they optimize better, you show biological insight. If they have better biology, you show smarter agent loop.
- **Surprise factor:** One unexpected result is worth more than five expected ones. An unexpected interaction BayBE found, a reagent that helped/hurt unexpectedly.
- **Completeness beats complexity:** A complete working loop (even simple) beats a complex broken one.
- **Show the process live:** If the other team only shows results, you show the loop running.

---

## 8. Streamlit Dashboard — What to Show

### Recommended Metrics
- **Real-time OD600 curves** per condition (line chart)
- **Growth rate (mu)** calculated from log-phase OD600 — the key target
- **BayBE suggestion vs. actual result** comparison
- **Round-over-round improvement** (bar chart, best growth rate each round)
- **Parameter space explored** (scatter/parallel coordinates of concentrations tried)
- **Current round status** (which wells are running, time remaining)
- **Leaderboard** of top 5 conditions by growth rate

### Real-Time Update Pattern
```python
@st.fragment(run_every=30)  # reruns every 30 seconds
def live_growth_chart():
    data = load_latest_od600_data()
    st.line_chart(data)
    st.metric("Current Best Growth Rate", f"{best_mu:.3f} h⁻¹")
```

Use `run_every` on `@st.fragment()` to auto-refresh only that section (not the whole page).

### Useful Libraries
- `streamlit-autorefresh` for frontend-driven auto-refresh
- `kmalci/plate-reader` (GitHub) for OD600 parsing, biomass, growth rate extraction

Sources:
- https://docs.streamlit.io/develop/tutorials/execution-flow/start-and-stop-fragment-auto-reruns
- https://github.com/kmalci/plate-reader

---

## 9. Pre-Demo Checklist

- [ ] Pitch practiced aloud 3+ times (not just mentally)
- [ ] Pre-recorded backup video of the loop running (in case live demo fails)
- [ ] "One slide, four numbers" ready with real data
- [ ] Dashboard shows live or recent data
- [ ] Clear narrative: problem → approach → loop demo → results → what surprised us
- [ ] Pitcher slept 2-3 hours minimum
- [ ] All broken/incomplete features removed from demo flow
- [ ] Technical jargon replaced with simple language for judges
