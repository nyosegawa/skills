# Skills Vault

[日本語版 (README-ja.md)](README-ja.md)

Personal skills repository by Sakasegawa (逆瀬川): <https://x.com/gyakuse>

## Directory Overview

- `skills`: Original skills created in this repository.
- `private_skills`: Personal skills with environment-specific configurations (e.g., local paths).
- `reference_docs`: External documents and references that help when creating skills.
- `reference_skills`: Imported skill examples from external GitHub repositories.
- `scripts`: Utility scripts for fetching or generating reference assets.

## Private Skills

### sakasegawa-blog-writer

Proofread given text and publish it to the blog.

- Outputs Markdown with Lume-compatible frontmatter to `posts/{slug}.md`
- Target repository: `nyosegawa.github.io`
- Includes a publishing flow with user confirmation before `git push`

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

## `reference_skills`

Rules for this directory:

- Only skills with acceptable licenses (MIT or Apache-2.0) should be added.
- Keep upstream license files (for example, `LICENSE.txt`) in each imported skill directory.
- Check for nested third-party assets/licenses inside each skill before reuse.
- Directory naming must follow:
  `{github-username}-{github-repositoryname}-{skillname}`

Example:

- `anthropics-skills-webapp-testing`
