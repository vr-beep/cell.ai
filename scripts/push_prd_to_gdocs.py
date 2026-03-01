#!/usr/bin/env python3
"""Push PRD to Google Docs with full formatting."""

import os
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(SCRIPT_DIR, "token.json")
CREDENTIALS_FILE = os.path.expanduser(
    "~/Desktop/client_secret_455874745738-60g5fm1f3gtamg7uco3j9fbls2ugg103.apps.googleusercontent.com.json"
)


def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def insert_text(index, text):
    return {"insertText": {"location": {"index": index}, "text": text}}


def heading_style(start, end, level):
    style_map = {
        1: "HEADING_1",
        2: "HEADING_2",
        3: "HEADING_3",
    }
    return {
        "updateParagraphStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "paragraphStyle": {"namedStyleType": style_map.get(level, "HEADING_3")},
            "fields": "namedStyleType",
        }
    }


def bold_style(start, end):
    return {
        "updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"bold": True},
            "fields": "bold",
        }
    }


def italic_style(start, end):
    return {
        "updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"italic": True},
            "fields": "italic",
        }
    }


def bold_italic_style(start, end):
    return {
        "updateTextStyle": {
            "range": {"startIndex": start, "endIndex": end},
            "textStyle": {"bold": True, "italic": True},
            "fields": "bold,italic",
        }
    }


def divider_request(index):
    return {"insertSectionBreak": {"location": {"index": index}, "sectionType": "CONTINUOUS"}}


def build_prd_content():
    """Build the PRD as a list of (text, type, level) blocks.
    Types: 'heading', 'para', 'bold_para', 'quote', 'bullet', 'divider', 'table'
    """
    blocks = []

    # Metadata block
    blocks.append(("Project: 24hr AI Science Cell Culture Hack @ Monomer Bio — Track A\nDate: October 25-26, 2025\nAuthor: Cell.ai team\nStatus: Draft\n", "meta", [
        ("Project:", True, False),
        ("Date:", True, False),
        ("Author:", True, False),
        ("Status:", True, False),
    ]))

    blocks.append(("---", "divider", None))

    # Section 1
    blocks.append(("1. Description: What is it?", "heading", 1))
    blocks.append(("An autonomous AI agent that optimizes cell culture media composition in a closed loop on Monomer Bio's robotic work cell during a 24-hour hackathon. The agent uses an LLM to generate an initial media \"recipe\" from scientific literature for an unknown cell line (revealed morning-of), then uses Bayesian optimization to iteratively suggest new compositions. Each round, the robot mixes the media, applies it to cells in a 96-well plate, incubates, and reads outcomes via a plate reader. The results feed back into the optimization algorithm, which proposes the next set of compositions — repeating for 2-3 loops until the agent converges on the highest-yield formulation.", "para", None))
    blocks.append(("Hackathon brief: \"Build an autonomous workflow that iteratively varies media components, runs cell culture, measures outcomes, and updates the next experiment end-to-end. All on REAL cells.\"", "quote", None))

    blocks.append(("---", "divider", None))

    # Section 2
    blocks.append(("2. Problem: What problem is this solving?", "heading", 1))
    blocks.append(("2a. What is the problem this project addresses?", "heading", 2))
    blocks.append(("Cell culture scientists spend days of manual labor testing media formulations one-at-a-time — mixing, pouring, monitoring, and compiling results by hand — because no tool exists that can autonomously design, execute, measure, and iterate on media compositions in a closed loop on robotic hardware.", "bullet", None))
    blocks.append(("\"It's more like the manual labor piece that's like the problem for all these iterative like hands-on stuff. It's not like reading results or comparing data isn't the issue — it's really like the amount of time it takes to set up so many different conditions.\" — Nikki, [37:17]", "quote", None))

    blocks.append(("2b. What is your hypothesis for why this problem is happening?", "heading", 2))
    blocks.append(("Today's media optimization is a brute-force matrix exercise. A scientist testing 2 media types across 4 components manually prepares ~30 individual plates, pours media into each, monitors them over time, and compiles data into Excel. This is repeated across multiple rounds. The tools exist in pieces — Bayesian optimization libraries (BayBE, BoTorch), robotic liquid handlers (Opentrons), plate readers — but nobody has wired them into a single autonomous loop where the AI both designs and learns from each round.", "bullet", None))
    blocks.append(("\"I might have to have like 30 different samples which are each like a plate that has my cells and my media with like the different condition, but then I also manually have to make those individual media conditions and like pour them in every plate and like monitor all those plates... it's like a matrix, like you have to make huge matrices manually in person with a bunch of different media.\" — Nikki, [37:37]", "quote", None))

    blocks.append(("2c. What problems are you NOT solving?", "heading", 2))
    blocks.append(("Contamination detection/remediation. The team explicitly scoped this out. Contamination takes days to manifest, far beyond the 24-hour hackathon window, and would require different instrumentation.", "bullet_bold_start", "Contamination detection/remediation."))
    blocks.append(("\"The contamination I don't think we can do much about... I don't think it's like within 24 hours and is really hard.\" — Team member, [05:48]", "quote", None))
    blocks.append(("Passaging / cell expansion workflows. Passaging requires dislodging cells, which adds mechanical complexity outside the scope of this demo.", "bullet_bold_start", "Passaging / cell expansion workflows."))
    blocks.append(("\"Is the experiment just from seeding till confluence, or do we also have a passaging aspect? Passaging is harder because now you need to dislodge the cells.\" — Nikki, [06:24]", "quote", None))
    blocks.append(("Cell potency or functional characterization. The team will focus on simple health metrics (viability, growth) rather than complex functional readouts like potency or phenotype.", "bullet_bold_start", "Cell potency or functional characterization."))
    blocks.append(("\"The health ones are probably a lot easier, right? Like if they're alive, if they're growing, it's just simpler. The other ones get a little complicated.\" — Nikki, [28:06]", "quote", None))

    blocks.append(("---", "divider", None))

    # Section 3
    blocks.append(("3. Why: How do we know this is a real problem and worth solving?", "heading", 1))
    blocks.append(("Business Impact:", "heading", 2))
    blocks.append(("TetraScience's Media Formulation Assistant claims to reduce wet lab experiments by up to 88% — validating that AI-driven media optimization has massive efficiency gains. Synthace has 94% ARR growth serving this same need at enterprise scale. The market demand is proven; the startup-accessible product doesn't exist yet.", "bullet", None))
    blocks.append(("BayBE-based approaches have been published in Nature Communications (2025), achieving results using 3-30x fewer experiments than standard DoE methods, and in cellular agriculture research achieving 181% more cells than commercial media variants while using 38% fewer experiments.", "bullet", None))
    blocks.append(("The hackathon itself is evidence: Monomer Bio, Opentrons, and multiple AI partners have organized a sold-out 50-builder event specifically around this problem space, signaling industry urgency.", "bullet", None))
    blocks.append(("Hackathon page: \"Rethink cell development. Onboarding a new cell line is notoriously difficult and lab automation is traditionally too intimidating to program and inflexible. We want to change that.\"", "quote", None))

    blocks.append(("Customer Impact:", "heading", 2))
    blocks.append(("Scientists currently spend hours to days on what is fundamentally manual labor — mixing, pouring, monitoring plates — rather than on scientific thinking. The bottleneck is not analysis, it's physical setup.", "bullet", None))
    blocks.append(("\"A person could test like 50 conditions in like three hours, but like if this can spit it back faster and then do the iterative part — I think even like three times would be impressive because if I was in a lab it would take a lot longer than that.\" — Nikki, [36:09]", "quote", None))
    blocks.append(("Media formulation is a multi-variable optimization problem with real trade-offs (e.g., growth vs. potency) that scientists currently navigate by intuition and literature review, not systematic experimentation.", "bullet", None))
    blocks.append(("\"The same mechanism that stimulates them exhausts them. So if you want something to grow rapidly, it's always like a pro-con situation.\" — Nikki, [26:33]", "quote", None))
    blocks.append(("The quality of optimization is limited by what the scientist can manually test. Garbage-in-garbage-out is the primary risk — if the initial guess is bad, all downstream conditions suffer.", "bullet", None))
    blocks.append(("\"It's as good as the inputs. If for some reason what we thought wasn't correct or the best approach, then you have a bunch of options but none of them are good.\" — Nikki, [40:43]", "quote", None))

    blocks.append(("---", "divider", None))

    # Section 4
    blocks.append(("4. Success: How do we know if we've solved this problem?", "heading", 1))
    blocks.append(("Given the 24-hour hackathon constraint, success is defined as:", "para", None))
    blocks.append(("Complete at least 2-3 closed-loop optimization rounds end-to-end (AI suggests composition -> robot mixes -> incubate -> plate read -> AI learns -> next round) with zero human intervention during each loop.", "bullet_bold_start", "Complete at least 2-3 closed-loop optimization rounds"))
    blocks.append(("Demonstrate measurable improvement in the target metric (likely optical density as a proxy for cell growth/viability) from round 1 to round 2-3, showing the AI agent learned from prior results.", "bullet_bold_start", "Demonstrate measurable improvement"))
    blocks.append(("Deliver a working demo at Sunday 4pm showcase: the agent receives a mystery cell line, autonomously generates an initial media recipe from literature, executes iterative optimization on the robotic work cell, and presents a final \"best recipe\" with supporting data.", "bullet_bold_start", "Deliver a working demo"))
    blocks.append(("Stretch goal: The AI agent converges on a formulation that outperforms a naive/literature-only baseline — demonstrating that closed-loop optimization adds value beyond a single LLM literature lookup.", "bullet_bold_start", "Stretch goal:"))
    blocks.append(("\"I think even like three times would be impressive because if I was in a lab it would take a lot longer than that.\" — Nikki, [36:36]", "quote", None))

    blocks.append(("---", "divider", None))

    # Section 5
    blocks.append(("5. Audience: Who are we building for?", "heading", 1))
    blocks.append(("Primary: Hackathon judges and demo audience — scientists, engineers, and builders at the Monomer Bio event who will evaluate whether the agent demonstrates a credible, end-to-end autonomous workflow on real cells.", "para", None))
    blocks.append(("Secondary: Cell culture scientists (the long-term Cell.ai user) — researchers who currently optimize media manually, want to test more conditions faster, and need a system that handles the tedious matrix of mix-pour-monitor-compile. As described in the meeting:", "para", None))
    blocks.append(("\"I have these cells, I want to see this much growth — what cocktail would be good for that? Or how much quantity I should use of the individual components... like a recipe.\" — Nikki, [31:32]", "quote", None))
    blocks.append(("They need a system constrained by what's actually available in their lab:", "para", None))
    blocks.append(("\"You basically have some something and something you don't have, so you want to limit the answer by what components you have right now.\" — Team member, [32:37]", "quote", None))

    blocks.append(("---", "divider", None))

    # Section 6
    blocks.append(("6. What: Roughly, what does this look like in the product?", "heading", 1))
    blocks.append(("[Architecture diagram — see local file: doc/assets/architecture-proposed.png]", "para", None))
    blocks.append(("The system has six components wired into an autonomous feedback loop:", "para", None))

    blocks.append(("A. Input: Cell Type + Available Media Components", "heading", 2))
    blocks.append(("The mystery cell line is revealed morning-of. The scientist (or agent) specifies cell type and which media components are physically available on the robotic work cell.", "bullet", None))

    blocks.append(("B. LLM Layer — Literature-Informed Priors", "heading", 2))
    blocks.append(("Standard Bayesian optimization starts with random guesses. Instead, an LLM agent reads scientific protocols and papers to set informed priors — generating a starting recipe grounded in published data for the given cell type.", "bullet", None))
    blocks.append(("This dramatically reduces the number of wet-lab rounds needed by starting from a plausible region of the search space rather than random.", "bullet", None))
    blocks.append(("\"We will put LLM who will go in literature for this cell type and will suggest something. So we need initial, we need this first one.\" — Team member, [23:45]", "quote", None))

    blocks.append(("C. Bayesian Optimization Engine", "heading", 2))
    blocks.append(("Takes the LLM-generated starting recipe and generates a batch of ~8-12 variant compositions (one per row of a 96-well plate, with replicates across columns).", "bullet", None))
    blocks.append(("After each round's results come back, the algorithm learns which compositions performed best and proposes the next batch.", "bullet", None))
    blocks.append(("\"There is an algorithm which can optimize parameters... for example 12 different combinations. We create these combinations, we exchange media, we incubate, we measure something and put these results back in the algorithm, which now learns from our previous composition — which one worked, which did not — and now it gives us another set of assumptions.\" — Team member, [24:14]", "quote", None))

    blocks.append(("D. World Model (Digital Twin / Simulator)", "heading", 2))
    blocks.append(("Before committing real reagents, the optimizer can \"dream\" — simulating thousands of candidate media recipes in silico to prune bad ideas before they reach the robot.", "bullet", None))
    blocks.append(("Requires historical data or a learned model from prior rounds to be effective. In round 1 this layer is thin; by round 2-3 the agent has enough real data to build a predictive model that filters candidates.", "bullet", None))
    blocks.append(("This is the key differentiator from a naive closed loop: the agent doesn't just try the next best guess, it pre-screens candidates computationally to maximize the value of each expensive wet-lab round.", "bullet", None))

    blocks.append(("E. Automated Experiment via MCP", "heading", 2))
    blocks.append(("Only the simulator-vetted recipes reach the robot. The agent sends commands to Monomer's robotic work cell through MCP (Model Context Protocol):", "bullet", None))
    blocks.append(("Create media mixture — robot mixes the specified composition", "sub_bullet", None))
    blocks.append(("Media change — robot applies the new media to wells", "sub_bullet", None))
    blocks.append(("Incubate — robot moves plate to incubator for the required time (~4 hours per round)", "sub_bullet", None))
    blocks.append(("Plate read — robot reads optical density or other signal as the outcome metric", "sub_bullet", None))
    blocks.append(("Hackathon brief: \"Robotic workcell actions are made available via MCP: Incubate, Create media mixture, Media change, Plateread.\"", "quote", None))

    blocks.append(("F. Data Parser + Agent Learning", "heading", 2))
    blocks.append(("Raw plate reader output is parsed into structured results.", "bullet", None))
    blocks.append(("The agent compares predicted outcomes (from the world model) against actual measurements, updates its internal model, and feeds everything back into the Bayesian optimizer for the next round.", "bullet", None))
    blocks.append(("The feedback loop closes: Input -> LLM Priors -> BayesOpt -> Simulator -> Robot -> Parse -> Learn -> BayesOpt -> ...", "bullet", None))
    blocks.append(("Output: the optimized recipe with the best measured outcome across all rounds.", "bullet", None))
    blocks.append(("\"We have a feedback loop. We were like cooking and then we see a result, and the result is coming back in the way we can determine what part of the recipe was wrong.\" — Team member, [35:15]", "quote", None))

    blocks.append(("Plate layout strategy:", "heading", 3))
    blocks.append(("96-well plate: each row = a different media composition, columns = biological replicates.", "bullet", None))
    blocks.append(("Fresh plate for each optimization round to avoid carryover effects confounding the results.", "bullet", None))
    blocks.append(("\"If we will be reusing the same plate for a second loop, there is no actually valuable data because it can be affected by previous [conditions]. Yeah, there's no control if you put it on the same group of cells.\" — Team member & Nikki, [21:23]", "quote", None))

    blocks.append(("Measurement approach:", "heading", 3))
    blocks.append(("Primary: optical density via plate reader (available, automated, quantitative).", "bullet", None))
    blocks.append(("The specific readout depends on cell type (adherent vs. suspension) and plate reader capabilities — to be confirmed with organizers.", "bullet", None))
    blocks.append(("\"How about optical density — is it giving any valuable information? Yeah, I mean we have a plate reader. So that makes sense.\" — Team discussion, [11:32]", "quote", None))

    blocks.append(("---", "divider", None))

    # Section 7
    blocks.append(("7. How: What is the experiment plan?", "heading", 1))

    blocks.append(("Phase 1: Pre-hack preparation (before Oct 25)", "heading", 2))
    blocks.append(("Build the optimization pipeline: LLM literature agent + BayBE/BoTorch Bayesian optimizer + MCP client for robotic commands.", "bullet", None))
    blocks.append(("Prepare a cell-type-agnostic framework: when the mystery cell line is revealed, the LLM generates the initial recipe and the optimizer adapts automatically.", "bullet", None))
    blocks.append(("Confirm with organizers (via Jimmy): what cell type, what plate reader capabilities, what media components are available.", "bullet", None))
    blocks.append(("\"The biggest unknown is actually what components are available, what can we change, what agents do we have to play with — and then the equipment.\" — Team member, [25:28]", "quote", None))

    blocks.append(("Phase 2: Hack day execution (Oct 25, 10am - Oct 26, 3pm)", "heading", 2))
    blocks.append(("Hour 0-1: Cell line revealed. LLM generates initial recipe from literature. Team configures available components and concentration ranges.", "bullet_bold_start", "Hour 0-1:"))
    blocks.append(("Hour 1-2: Algorithm generates first batch of ~8-12 compositions. Robot mixes and plates.", "bullet_bold_start", "Hour 1-2:"))
    blocks.append(("Hour 2-6: Incubation round 1 (~4 hours based on expected doubling time). Team monitors.", "bullet_bold_start", "Hour 2-6:"))
    blocks.append(("Hour 6-7: Plate read round 1. Results feed into optimizer. Algorithm proposes round 2 compositions.", "bullet_bold_start", "Hour 6-7:"))
    blocks.append(("Hour 7-11: Round 2: mix, plate, incubate, read.", "bullet_bold_start", "Hour 7-11:"))
    blocks.append(("Hour 11-15: Round 3 (if time permits): mix, plate, incubate, read.", "bullet_bold_start", "Hour 11-15:"))
    blocks.append(("Hour 15-18: Compile results, prepare demo narrative and dashboard.", "bullet_bold_start", "Hour 15-18:"))

    blocks.append(("\"The cells... they grow in four hours and we can do several loops.\" — Team member, [01:04]", "quote", None))
    blocks.append(("\"Two loops, three maximum. I don't know if somebody would like to stay overnight there.\" — Team member, [20:09]", "quote", None))

    blocks.append(("Phase 3: Demo (Oct 26, 4-5pm)", "heading", 2))
    blocks.append(("Present the full closed-loop story: mystery cell line -> LLM-generated initial recipe -> iterative optimization -> final best formulation, with data showing improvement across rounds.", "bullet", None))

    blocks.append(("---", "divider", None))

    # Section 8
    blocks.append(("8. When: When does it ship and what are the milestones?", "heading", 1))

    # Table: milestones
    blocks.append(("milestones_table", "table", [
        ["Milestone", "Date", "Risks", "Mitigations"],
        ["Confirm cell type, plate reader specs, and available media components with organizers", "ASAP (before hack)", "Organizers may not respond in time; mystery cell line may not be revealed until morning-of", "Reach out to Jimmy via email/LinkedIn now. Build cell-type-agnostic framework so the system works regardless."],
        ["Optimization pipeline built and tested (LLM + BayBE + MCP client)", "Oct 24 (day before hack)", "MCP interface may not be documented until event; BayBE integration may have edge cases", "Use mock MCP endpoints for pre-testing. Have fallback to manual MCP commands if API integration fails."],
        ["Round 1 complete (first plate read results in)", "Oct 25, ~4pm", "Incubation takes longer than expected; plate reader output format unknown", "Plan for 4-hour incubation windows. Have parsing scripts ready for common plate reader output formats."],
        ["Round 2 complete (demonstrable learning)", "Oct 25, ~10pm", "Cells may not show measurable differences between compositions in one round", "Choose a metric (OD) with enough sensitivity. Ensure enough replicates per condition for statistical signal."],
        ["Round 3 complete (stretch goal)", "Oct 26, ~6am", "Requires overnight presence; cell viability may degrade", "Optional milestone. Even 2 rounds with clear learning is a strong demo."],
        ["Demo-ready", "Oct 26, 3pm (submission deadline)", "Dashboard not polished; narrative unclear", "Reserve last 3 hours exclusively for demo prep. Prioritize the \"story\" over the \"polish.\""],
    ]))

    blocks.append(("Hackathon agenda: \"Saturday 12:00p Hack + build. Sunday 3p Final submission. 4-5p Demos + Pitching.\"", "quote", None))

    blocks.append(("---", "divider", None))

    # Open Questions
    blocks.append(("Open Questions", "heading", 1))
    blocks.append(("These were explicitly identified during the team meeting as blockers requiring information from the organizers:", "para", None))

    blocks.append(("1. What cell type? The experiment design (adherent vs. suspension, doubling time, known media requirements) depends entirely on this.", "para", None))
    blocks.append(("\"Did you guys say you know what cell type it is?\" / \"I don't know what it is.\" / \"This is probably something that we need to reach out to them about.\" — Team discussion, [04:49]", "quote", None))

    blocks.append(("2. What media components are available? The optimization search space is constrained by what Monomer physically has on-site.", "para", None))
    blocks.append(("\"What is the biggest unknown is actually what components are available, what can we change.\" — Team member, [25:40]", "quote", None))

    blocks.append(("3. What does the plate reader measure? Optical density, impedance, fluorescence — the measurement capability determines what the agent optimizes for.", "para", None))
    blocks.append(("\"I just don't know like what the plate reader is doing is the other problem. If you know what it can do then it's probably easy for us to come up with something simple to look at.\" — Nikki, [30:23]", "quote", None))

    blocks.append(("4. Fresh plate per round or reuse? Team leaning toward fresh plates to avoid carryover confounds, but this depends on cell/plate availability.", "para", None))
    blocks.append(("\"If we will be reusing the same plate for a second loop, there is no actually valuable data because it can be affected by previous [conditions].\" — Team member, [21:23]", "quote", None))

    blocks.append(("---", "divider", None))

    # Key Design Decisions
    blocks.append(("Key Design Decisions from Meeting", "heading", 1))

    blocks.append(("decisions_table", "table", [
        ["Decision", "Resolution", "Rationale"],
        ["Contamination track", "Out of scope", "Takes days to manifest; can't demo in 24 hours"],
        ["Passaging", "Out of scope", "Adds mechanical complexity; focus on seeding-to-growth"],
        ["Optimization target", "Cell growth / viability (not potency)", "Simpler to measure; potency requires functional assays"],
        ["Measurement method", "Plate reader (optical density)", "Available via MCP; quantitative; automated"],
        ["Initial media recipe", "LLM literature search", "No starting media provided; AI generates first guess"],
        ["Plate strategy", "Fresh plate per round (preferred)", "Avoids carryover confounding results"],
        ["Number of loops", "2-3 in 24 hours", "~4 hour incubation per round; overnight stay optional"],
    ]))

    return blocks


def create_doc_with_prd():
    creds = authenticate()
    docs_service = build("docs", "v1", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    title = "PRD: AI-Driven Cell Culture Media Optimization Agent"

    # Create blank doc
    file_metadata = {
        "name": title,
        "mimeType": "application/vnd.google-apps.document",
    }
    file = drive_service.files().create(body=file_metadata, fields="id").execute()
    doc_id = file["id"]
    print(f"Created doc: https://docs.google.com/document/d/{doc_id}/edit")

    blocks = build_prd_content()

    # Build plain text and track positions for formatting
    full_text = ""
    format_ops = []  # (start, end, type, extra)
    table_insertions = []  # (insert_after_char_index, table_data)

    for block in blocks:
        text, btype, extra = block
        if btype == "divider":
            # We'll use a horizontal line (Unicode) as a visual separator
            start = len(full_text)
            full_text += "━" * 50 + "\n\n"
            format_ops.append((start, start + 50, "divider", None))
        elif btype == "heading":
            start = len(full_text)
            full_text += text + "\n"
            end = len(full_text)
            format_ops.append((start, end, "heading", extra))
        elif btype == "para":
            start = len(full_text)
            full_text += text + "\n\n"
        elif btype == "meta":
            start = len(full_text)
            full_text += text + "\n"
            # Bold the label parts
            for label, is_bold, is_italic in extra:
                idx = full_text.find(label, start)
                if idx >= 0:
                    format_ops.append((idx, idx + len(label), "bold", None))
        elif btype == "bullet":
            start = len(full_text)
            full_text += "• " + text + "\n\n"
        elif btype == "sub_bullet":
            start = len(full_text)
            full_text += "    ◦ " + text + "\n"
        elif btype == "bullet_bold_start":
            start = len(full_text)
            full_text += "• " + text + "\n\n"
            # Bold the prefix
            bold_text = extra
            bold_start = start + 2  # after "• "
            bold_end = bold_start + len(bold_text)
            format_ops.append((bold_start, bold_end, "bold", None))
        elif btype == "quote":
            start = len(full_text)
            full_text += "    " + text + "\n\n"
            format_ops.append((start, start + len(text) + 4, "italic", None))
        elif btype == "table":
            # Mark position for table insertion
            table_insertions.append((len(full_text), extra))
            full_text += "\n"  # placeholder
        else:
            start = len(full_text)
            full_text += text + "\n\n"

    # Step 1: Insert all text
    requests = [insert_text(1, full_text)]

    # Step 2: Apply formatting (headings, bold, italic)
    for start, end, ftype, extra in format_ops:
        # Offset by 1 for doc body index
        s = start + 1
        e = end + 1
        if ftype == "heading":
            requests.append(heading_style(s, e, extra))
        elif ftype == "bold":
            requests.append(bold_style(s, e))
        elif ftype == "italic":
            requests.append(italic_style(s, e))
        elif ftype == "divider":
            # Style the divider line as gray
            requests.append({
                "updateTextStyle": {
                    "range": {"startIndex": s, "endIndex": e},
                    "textStyle": {
                        "foregroundColor": {
                            "color": {
                                "rgbColor": {"red": 0.7, "green": 0.7, "blue": 0.7}
                            }
                        },
                        "fontSize": {"magnitude": 6, "unit": "PT"},
                    },
                    "fields": "foregroundColor,fontSize",
                }
            })

    # Execute text + formatting
    docs_service.documents().batchUpdate(
        documentId=doc_id, body={"requests": requests}
    ).execute()
    print("Text and formatting applied.")

    # Step 3: Insert tables
    # We need to re-read the doc to get current end index for table insertion
    for table_pos, table_data in reversed(table_insertions):
        doc = docs_service.documents().get(documentId=doc_id).execute()
        body_content = doc["body"]["content"]
        # Find insertion point near our placeholder
        doc_end = body_content[-1]["endIndex"] - 1

        rows = len(table_data)
        cols = len(table_data[0])

        # Insert table at end
        table_requests = [
            {
                "insertTable": {
                    "rows": rows,
                    "columns": cols,
                    "endOfSegmentLocation": {"segmentId": ""},
                }
            }
        ]
        docs_service.documents().batchUpdate(
            documentId=doc_id, body={"requests": table_requests}
        ).execute()

        # Re-read to get table cell indices
        doc = docs_service.documents().get(documentId=doc_id).execute()
        body_content = doc["body"]["content"]

        # Find the last table in the doc
        table_element = None
        for element in reversed(body_content):
            if "table" in element:
                table_element = element["table"]
                break

        if table_element:
            # Fill cells in reverse order to keep indices stable
            cell_requests = []
            for row_idx in range(rows - 1, -1, -1):
                row = table_element["tableRows"][row_idx]
                for col_idx in range(cols - 1, -1, -1):
                    cell = row["tableCells"][col_idx]
                    cell_start = cell["content"][0]["startIndex"]
                    cell_text = table_data[row_idx][col_idx]
                    cell_requests.append(insert_text(cell_start, cell_text))

            docs_service.documents().batchUpdate(
                documentId=doc_id, body={"requests": cell_requests}
            ).execute()

            # Bold header row
            doc = docs_service.documents().get(documentId=doc_id).execute()
            for element in doc["body"]["content"]:
                if "table" in element:
                    # Check if this is the right table by checking first cell
                    first_table = element["table"]
                    header_row = first_table["tableRows"][0]
                    bold_requests = []
                    for cell in header_row["tableCells"]:
                        cs = cell["content"][0]["startIndex"]
                        ce = cell["content"][-1]["endIndex"] - 1
                        if ce > cs:
                            bold_requests.append(bold_style(cs, ce))
                    if bold_requests:
                        docs_service.documents().batchUpdate(
                            documentId=doc_id, body={"requests": bold_requests}
                        ).execute()

        print(f"Table inserted ({rows}x{cols})")

    print(f"\nDone! View your doc at:")
    print(f"https://docs.google.com/document/d/{doc_id}/edit")
    return doc_id


if __name__ == "__main__":
    create_doc_with_prd()
