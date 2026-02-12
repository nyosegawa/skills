# Skills Vault

[日本語版 (README-ja.md)](README-ja.md)

Personal skills repository by Sakasegawa (逆瀬川): <https://x.com/gyakuse>

## Directory Overview

- `skills`: Original skills created in this repository.
- `reference_docs`: External documents and references that help when creating skills.
- `reference_skills`: Imported skill examples from external GitHub repositories.
- `scripts`: Utility scripts for fetching or generating reference assets.

## `skills`

### repo-analyzer

Analyze any GitHub or local repository using [gtc](https://github.com/nyosegawa/gemini-tree-token-counter) and Gemini 3 Pro.

- Supports GitHub URLs and local paths
- Architecture analysis, security audit, code quality review, dependency analysis, and more
- Uses gtc's token count for accurate cost estimation before each Gemini API call
- Asks for user confirmation with estimated cost before every API call
- Handles large repositories by using Gemini to plan optimal extraction commands

**Requirements:** Python 3.10+, `gtc`, `google-genai`, `GEMINI_API_KEY`

```bash
pip install gemini-tree-token-counter google-genai
export GEMINI_API_KEY="your_key_here"
```

### sakasegawa-blog-writer

Write tech blog posts in Sakasegawa's writing style. Conducts web research and generates technically accurate, readable articles.

- Outputs Markdown with Lume-compatible frontmatter to `posts/{slug}.md`
- Auto-inserts "Written by Coding Agent" notice and `<!--more-->` excerpt marker
- All URLs formatted as Markdown links (including References)
- Includes style guide, article template, and research methodology references

## `reference_docs`

`reference_docs` stores external documents useful for skill authoring.

- `reference_docs/skill-bestpractice.md` is based on Anthropic content:
  <https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf>
- Because this file is derived from Anthropic content, it is excluded via `.gitignore`.
- It can be regenerated with the script below.

### Generate `skill-bestpractice.md`

```bash
export GEMINI_API_KEY="your_actual_api_key_here"
pip install google-genai pymupdf requests
python scripts/convert_guide_to_md.py
```

Output:

- `reference_docs/skill-bestpractice.md`

Notes:

- Set `GEMINI_API_KEY` before running the script.
- Estimated generation cost is about `$0.15-$0.20` (roughly `20-30 JPY`).

### Download Gemini 3 and Nano Banana docs as `.md`

```bash
curl -L "https://ai.google.dev/gemini-api/docs/gemini-3.md.txt" \
  -o reference_docs/gemini-3-developers-guide.md
curl -L "https://ai.google.dev/gemini-api/docs/image-generation.md.txt" \
  -o reference_docs/image-generation-nanobanana.md
```

Output:

- `reference_docs/gemini-3-developers-guide.md`
- `reference_docs/image-generation-nanobanana.md`

## `reference_skills`

Rules for this directory:

- Only skills with acceptable licenses (MIT or Apache-2.0) should be added.
- Keep upstream license files (for example, `LICENSE.txt`) in each imported skill directory.
- Check for nested third-party assets/licenses inside each skill before reuse.
- Directory naming must follow:
  `{github-username}-{github-repositoryname}-{skillname}`

Example:

- `anthropics-skills-webapp-testing`
