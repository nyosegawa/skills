---
name: repo-analyzer
description: Analyze any GitHub or local repository using gtc and Gemini 3 Pro. Use when user asks to "analyze this repo", "explain this codebase", "repository analysis", "architecture review", "security audit", "code review", "リポジトリ分析", or "コードベース解析".
compatibility: Requires Python 3.10+, gtc (pip install gemini-tree-token-counter), google-genai (pip install google-genai), and GEMINI_API_KEY environment variable. Claude Code only.
metadata:
  author: nyosegawa
  version: 1.0.0
---

# Repository Analyzer

Analyze any GitHub or local repository using **gtc** (Gemini Tree Token Counter) and **Gemini 3 Pro**.

## Prerequisites

Before starting any analysis, verify all dependencies. If any are missing, install them or ask the user to configure them.

1. **gtc**: `gtc --version` — if missing: `pip install gemini-tree-token-counter`
2. **google-genai**: `python3 -c "from google import genai; print('OK')"` — if missing: `pip install google-genai`
3. **GEMINI_API_KEY**: `echo $GEMINI_API_KEY` — if not set, ask the user to provide it

## Gemini 3 Pro Pricing Reference

Use this table with the **exact token count from gtc output** to calculate costs.

| Context Size | Input | Output |
|---|---|---|
| ≤ 200k tokens | $2.00 / 1M tokens | $12.00 / 1M tokens |
| > 200k tokens | $4.00 / 1M tokens | $18.00 / 1M tokens |

**Cost calculation:**
- Use the **actual token count of the file being sent** (see "Understanding gtc Token Counts" below)
- For ≤200k input tokens: cost ≈ (tokens × $0.000002) + (65536 × $0.000012) = input + ~$0.79
- For >200k input tokens: cost ≈ (tokens × $0.000004) + (65536 × $0.000018) = input + ~$1.18

## Understanding gtc Token Counts

**`Grand Total Tokens` from gtc is the estimated CONTENT token count** — i.e., how many tokens the file contents would be if extracted with `-c`. The tree.txt file itself is much smaller (typically 1-5% of this number).

Example: If `Grand Total Tokens: 5,000,000`, it means the full repo content is ~5M tokens, but tree.txt itself might only be ~50-100k tokens.

**When calculating Gemini API costs, always use the actual file size being sent, not `Grand Total Tokens`.**

To measure the actual token count of a file:
```bash
wc -w $TMPDIR/tree.txt | awk '{printf "%.0f\n", $1 * 1.3}'  # rough estimate: words × 1.3
```

## CRITICAL: User Confirmation Before Every Gemini API Call

**You MUST confirm with the user before EVERY Gemini 3 Pro API call.** Always:

1. Determine the actual token count of the file(s) being sent (use `wc -w` × 1.3 as rough estimate)
2. Calculate cost using the pricing table above
3. Present purpose, token count, and estimated cost
4. Wait for explicit user approval

Format:

```
Gemini 3 Pro API call:
- Purpose: [what will be analyzed]
- Input: ~[N] tokens (estimated from file size)
- Estimated cost: ~$X.XX (input: $X.XX + max output: $X.XX)
Proceed?
```

**Do NOT proceed without explicit user approval.**

## CRITICAL: Do NOT Analyze the Repository Yourself

**Gemini 3 Pro has a 1M token context window — let it do the analysis, not you.**

- Do NOT read tree.txt with sed/grep/cat to understand the repository structure
- Do NOT manually browse the tree output to find relevant directories
- Do NOT make multiple targeted gtc calls to explore the codebase
- Do NOT use grep, GitHub API, or other tools to read individual files from the repository
- Your job is ONLY: run gtc → check `Grand Total Tokens` → send to Gemini → present results
- Gemini is the analyzer. You are the orchestrator.

**Common mistake to avoid:** When `Grand Total Tokens` > 800k, do NOT try to manually read the tree to find relevant paths. Instead, send tree.txt to Gemini for planning — tree.txt is small (typically <100k tokens) and cheap to process. The `Grand Total Tokens` number represents the full repo content size, NOT the cost of the planning step.

## Workflow

### Step 1: Create Temp Directory

```bash
TMPDIR=$(mktemp -d /tmp/repo-analyzer.XXXXXX)
```

### Step 2: Extract Repository Tree and Check Size

Run gtc to get the token count (without file contents):

```bash
gtc <target> > $TMPDIR/tree.txt 2>&1
grep "Grand Total Tokens:" $TMPDIR/tree.txt
```

Where `<target>` is a GitHub URL or local path. Optional flags:
- `-b <branch>`, `-d <dir>`, `-e <pattern>`, `--commit <hash>`, `--date <YYYY-MM-DD>`

### Step 3: Extract Content (Based on Token Count)

**If Grand Total Tokens ≤ 800,000:**
- Extract everything with no filtering:
  ```bash
  gtc <target> -c > $TMPDIR/content.txt 2>&1
  ```
- Proceed directly to Step 4.

**If Grand Total Tokens > 800,000:**
- The repository is too large to send in full. Use Gemini to plan extraction.
- **[USER CONFIRMATION REQUIRED]** Measure tree.txt's actual size with `wc -w $TMPDIR/tree.txt | awk '{printf "%.0f\n", $1 * 1.3}'` and present this as the input token count (NOT Grand Total Tokens — that's the content estimate, tree.txt is much smaller).
- Write a planning prompt to `$TMPDIR/plan_prompt.txt`:

```
Based on the following repository tree structure and the user's analysis goal,
suggest the most effective gtc command(s) to extract relevant source code.

User's goal: [user's analysis request]

Rules:
- Use -d flags to focus on the most relevant directories
- Use -e flags to exclude noise (tests, vendor, generated code, lock files, etc.)
- Aim for total content under 800k tokens
- Prioritize core source code over configuration and documentation
- Output ONLY the gtc command(s), one per line, using <TARGET> as a placeholder
```

- Run:
  ```bash
  python3 <SKILL_DIR>/scripts/gemini_query.py \
    --prompt-file $TMPDIR/plan_prompt.txt \
    --file $TMPDIR/tree.txt \
    --output $TMPDIR/plan.txt \
    --max-tokens 4096
  ```
- Execute the suggested gtc commands:
  ```bash
  gtc <target> -c [flags from plan] > $TMPDIR/content.txt 2>&1
  ```
- If the result still exceeds 900,000 tokens, add more `-e` flags and retry.

### Step 4: Analyze with Gemini

**[USER CONFIRMATION REQUIRED]** Parse `Grand Total Tokens` from content.txt (this time it IS the actual content being sent), calculate cost, and confirm.

Write the analysis prompt to `$TMPDIR/analysis_prompt.txt` (see templates below). Then run:

```bash
python3 <SKILL_DIR>/scripts/gemini_query.py \
  --prompt-file $TMPDIR/analysis_prompt.txt \
  --file $TMPDIR/content.txt \
  --output $TMPDIR/result.md
```

Read and present `$TMPDIR/result.md` to the user.

### Step 5: Cleanup

```bash
rm -rf $TMPDIR
```

## Analysis Prompt Templates

Adapt these based on the user's request. Combine or modify as needed.

### Architecture Analysis

```
Analyze the architecture of this codebase:
1. Overall design pattern (monolith, microservices, layered, hexagonal, etc.)
2. Key modules/components and their responsibilities
3. Dependency graph between components
4. Entry points and data flow paths
5. Technology stack and frameworks
6. Strengths and potential architectural concerns
Provide a structured summary. Use ASCII diagrams where helpful.
```

### Security Audit

```
Perform a security review of this codebase:
1. Injection vulnerabilities (SQL, command, XSS, path traversal)
2. Authentication and authorization issues
3. Sensitive data exposure (hardcoded secrets, logging PII)
4. Insecure dependencies or configurations
5. Input validation gaps
Rate each finding: Critical / High / Medium / Low. Include file paths and line references.
```

### Code Quality Review

```
Review the code quality:
1. Code organization and modularity
2. Error handling patterns and consistency
3. Test coverage indicators
4. Documentation completeness
5. Adherence to language/framework conventions
6. DRY violations and code duplication
Provide specific, actionable recommendations with file references.
```

### Dependency / API Surface Analysis

```
Analyze the dependency structure and API surface:
1. External dependencies and their purposes
2. Internal module dependency graph
3. Public API surface (exported functions, classes, endpoints)
4. Potential circular dependencies
5. Dependency freshness and maintenance status
```

## Troubleshooting

### gtc fails on GitHub URL
- Ensure the repository is public, or git credentials are configured
- For private repos, clone locally first and pass the local path
- If rate-limited by GitHub, wait and retry

### Gemini API errors
- Verify `GEMINI_API_KEY` is set and valid
- If content exceeds the 1M token context window, narrow scope with `-d` and `-e`
- For timeout errors, split the analysis into smaller targeted chunks

### Content too large for Gemini
- Use `-d` to focus on specific directories
- Use `-e` to exclude common noise: `"*.test.*"`, `"*_test.*"`, `"vendor/*"`, `"node_modules/*"`, `"*.lock"`, `"*.min.js"`, `"dist/*"`, `"build/*"`, `"*.generated.*"`
- If still too large, run multiple targeted analyses on different subsystems
