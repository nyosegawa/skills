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

**Cost calculation using gtc token count:**
- gtc outputs `Grand Total Tokens: XXXXX` — use this as the input token count
- For ≤200k input tokens: cost ≈ (tokens × $0.000002) + (65536 × $0.000012) = input + ~$0.79
- For >200k input tokens: cost ≈ (tokens × $0.000004) + (65536 × $0.000018) = input + ~$1.18

## CRITICAL: User Confirmation Before Every Gemini API Call

**You MUST confirm with the user before EVERY Gemini 3 Pro API call.** Always:

1. Parse `Grand Total Tokens: XXXXX` from the gtc output
2. Calculate cost using the pricing table above
3. Present purpose, token count, and estimated cost
4. Wait for explicit user approval

Format:

```
Gemini 3 Pro API call:
- Purpose: [what will be analyzed]
- Input: [N] tokens (from gtc)
- Estimated cost: ~$X.XX (input: $X.XX + max output: $X.XX)
Proceed?
```

**Do NOT proceed without explicit user approval.**

## Workflow

### Step 1: Create Temp Directory

```bash
TMPDIR=$(mktemp -d /tmp/repo-analyzer.XXXXXX)
```

Store the path for use in subsequent commands.

### Step 2: Extract Repository Tree

Run gtc to get the repository structure (without file contents):

```bash
gtc <target> > $TMPDIR/tree.txt 2>&1
```

Where `<target>` is a GitHub URL or local path.

Optional gtc flags:
- `-b <branch>` — specific branch
- `-d <dir>` — focus on a subdirectory (can be used multiple times)
- `-e <pattern>` — exclude glob patterns (can be used multiple times)
- `--commit <hash>` — specific commit
- `--date <YYYY-MM-DD>` — state at a specific date

After running, extract the token count and line count:

```bash
grep "Grand Total Tokens:" $TMPDIR/tree.txt
wc -l < $TMPDIR/tree.txt
```

### Step 3: Plan Content Extraction Commands

**If tree ≤ 500 lines:**
- Read `$TMPDIR/tree.txt` directly
- Based on the user's request, decide which directories/files are relevant
- Construct the `gtc -c` command with appropriate `-d` and `-e` flags

**If tree > 500 lines:**
- The tree is too large to read in Claude's context
- **[USER CONFIRMATION REQUIRED]** Use Gemini to analyze the tree and suggest optimal `gtc` commands
- Write a planning prompt to `$TMPDIR/plan_prompt.txt`:

```
Based on the following repository tree structure and the user's analysis goal,
suggest the most effective gtc command(s) to extract relevant source code.

User's goal: [user's analysis request]

Rules:
- Use -d flags to focus on the most relevant directories
- Use -e flags to exclude noise (tests, vendor, generated code, lock files, etc.)
- Keep total content under 500k tokens if possible
- Prioritize core source code over configuration and documentation
- Output ONLY the gtc command(s), one per line, using <TARGET> as a placeholder for the repo path/URL
```

- Calculate cost from `Grand Total Tokens` in tree.txt, present to user for confirmation
- If approved, run:
  ```bash
  python3 <SKILL_DIR>/scripts/gemini_query.py \
    --prompt-file $TMPDIR/plan_prompt.txt \
    --file $TMPDIR/tree.txt \
    --output $TMPDIR/plan.txt \
    --max-tokens 4096
  ```
- Read `$TMPDIR/plan.txt` and use the suggested commands

### Step 4: Extract Content

Run the planned `gtc -c` command to get file contents:

```bash
gtc <target> -c [planned flags] > $TMPDIR/content.txt 2>&1
```

**IMPORTANT:** The `-c` flag includes full file contents — always redirect to a file.

Extract the token count:

```bash
grep "Grand Total Tokens:" $TMPDIR/content.txt
```

If tokens exceed 900,000, narrow scope with more `-d` / `-e` flags before proceeding.

### Step 5: Analyze with Gemini

**[USER CONFIRMATION REQUIRED]** Use the token count from Step 4 to calculate cost and confirm with the user.

Write the analysis prompt to `$TMPDIR/analysis_prompt.txt`, tailored to the user's request (see templates below). Then run:

```bash
python3 <SKILL_DIR>/scripts/gemini_query.py \
  --prompt-file $TMPDIR/analysis_prompt.txt \
  --file $TMPDIR/content.txt \
  --output $TMPDIR/result.md
```

Read and present `$TMPDIR/result.md` to the user.

### Step 6: Cleanup

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
