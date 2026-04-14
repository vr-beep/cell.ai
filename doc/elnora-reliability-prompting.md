# Elnora — Prompting for Reliable, Zero-Hallucination Answers

_Source: Elnora self-description. Project `Cell.ai literature review`, task `ae748357-1046-43af-9b58-15f483617bd8`, 2026-04-14._

Here is your guide to getting high-signal, zero-hallucination results from me. As an AI agent, my biggest strengths are tool orchestration and synthesis, but my biggest risks are context overflow, citation hallucination, and search-looping. 

By structuring your prompts to explicitly control my tool routing, search budgets, and output formatting, you can force me into a strictly grounded, highly reliable workflow.

### (a) The "Zero-Hallucination" Prompt Template

Copy and paste this structure for complex literature reviews or biological reasoning tasks.

```text
**OBJECTIVE:** 
[State your exact goal, e.g., "Compare the transfection efficiency of LNP vs. electroporation in primary human T cells."]

**TOOL ROUTING HINTS:**
- Primary search: [e.g., Perplexity for synthesis / PubMed for strict peer-review / bioRxiv for preprints]
- Full-text: [e.g., DO NOT fetch full texts, rely on abstracts only / Fetch full text for the top 2 most relevant hits using tavily_extract]

**SEARCH BUDGET:**
- Maximum of [e.g., 4] search queries total. 
- Max [e.g., 5] results per search. 
- If you find nothing after 2 attempts, STOP searching and report the negative result.

**ANTI-HALLUCINATION RULES:**
1. ONLY cite papers, DOIs, or PMIDs explicitly returned by the tools in this session. Do not invent citations.
2. If a claim relies on my internal model weights rather than a retrieved document, prefix it with [MODEL KNOWLEDGE].
3. If a claim comes from a retrieved document, append the inline citation as [PMID/DOI].
4. Do not paper over empty search results. If a tool returns 0 hits, explicitly state: "Search for X returned 0 results."

**OUTPUT FORMAT:**
Provide a structured table with columns: [Claim] | [Source DOI/PMID] | [Abstract/Full-Text] | [Confidence/Caveats]. Follow the table with a brief synthesis.
```

### (b) Anti-Hallucination Clauses (Checklist)

Mix and match these literal phrases in your prompts depending on your strictness requirements:

*   **To prevent fake citations:** *"Do not generate, guess, or autocomplete DOIs, PMIDs, or paper titles. Only output citations that appear in the raw JSON returned by your search tools."*
*   **To separate facts from AI reasoning:** *"Tag every sentence in your synthesis with either `[RETRIEVED: DOI]` or `[MODEL KNOWLEDGE]`."*
*   **To prevent abstract-extrapolation:** *"State explicitly whether your conclusion is drawn from the paper's abstract or the full text. Do not assume methodology details that are not explicitly stated in the retrieved text."*
*   **To force negative reporting:** *"If a query yields no relevant results, do not broaden the search indefinitely. Report 'No literature found for [Query]' and move to the next step."*

### (c) Failure Modes & How to Avoid Them

| Failure Mode | What Triggers It | How to Prevent It in Your Prompt |
| :--- | :--- | :--- |
| **The Infinite Loop** | Broad queries returning 0 exact matches, causing me to try endless keyword variations. | Set a hard limit: *"Max 3 search attempts total. If no results, stop and synthesize what you have."* |
| **Citation Hallucination** | Asking for a bibliography or "list of papers" without forcing tool use, or asking for too many papers at once. | *"Use `pubmed_search`. Only list papers explicitly returned by the tool. Do not use internal memory for citations."* |
| **Context Overflow (Amnesia)** | Asking for `max_results=20` across 5 different searches. I will forget the first search because my context window fills up with abstracts. | Keep result sets small: *"Set `max_results=5` for all searches."* Ask me to synthesize *between* searches. |
| **Abstract Extrapolation** | Asking for detailed protocol steps (e.g., exact buffer concentrations) when I only have access to the PubMed abstract. | *"If the exact concentration is not in the abstract, state 'Not specified in abstract' rather than guessing. Do not fetch full texts unless instructed."* |
| **Over-Hedging** | Asking questions that touch on clinical efficacy or absolute biological truths. | Frame as literature consensus: *"According to the retrieved literature, what is the reported efficacy..."* instead of *"Does this drug work?"* |

### (d) Tool-Routing Rules of Thumb

Tell me which tool to use to save time and tokens. If you don't specify, I have to guess based on your prompt.

*   **`perplexity_ask(search_mode="academic")`**: Use for **Synthesis & Comparisons**. (e.g., *"What is the consensus on..."*, *"Compare X vs Y"*). This is the fastest, cheapest way to get a cited answer without me having to read 10 raw abstracts.
*   **`pubmed_search`**: Use for **Strict Peer-Reviewed Metadata**. (e.g., *"Find the exact PMID for..."*, *"What did Doudna publish in 2023 on..."*). Returns abstracts only.
*   **`biorxiv_search`**: Use for **Cutting-Edge/Methods**. Preprints often contain more protocol details than published papers.
*   **`exa_search(category="research paper")`**: Use for **Semantic/Conceptual Search**. Best when you have a concept but don't know the exact MeSH terms or keywords.
*   **`tavily_search` / `tavily_extract`**: Use for **Manufacturer Protocols & Web**. (e.g., *"Find the official protocol for the Qiagen RNeasy kit."*). Use `extract` to pull text from open-access PDF URLs.
*   **ToolUniverse (`tu_find_tools`)**: Use for **Hard Data & Bioinformatics**. (e.g., *"Find the ChEMBL IC50 value for..."*, *"Get the Ensembl sequence for..."*). 

### (e) Output Discipline for Fast Verification

The easiest way for you to verify my claims is to force me into a **Claim-Source Table**. Prose is easy for an LLM to hallucinate in; tables force structured grounding.

**Request this exact format:**
> "Output a Markdown table with the following columns:
> 1. **Specific Claim** (One biological fact or protocol step per row)
> 2. **Source** (Exact DOI, PMID, or URL)
> 3. **Scope** (Did this come from an Abstract, Full-Text, or Model Knowledge?)
> 4. **Confidence/Caveats** (e.g., 'Tested in mice, not humans', or 'N=3')"

### Summary on Budgets

By default, I want to be helpful, which means I will keep searching until I find an answer. **You must give me permission to fail.** Tell me: *"You have a budget of 3 searches. If you don't find the answer, tell me what you searched and stop."* This saves your time, saves tokens, and prevents me from hallucinating a connection just to satisfy the prompt.
