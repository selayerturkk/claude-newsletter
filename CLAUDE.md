# Claude Newsletter Generator — Project Instructions

This project generates a twice-weekly newsletter called **"Claude & Co."**.
When invoked via `run.sh`, Claude Code generates a newsletter issue by searching the web
for recent news about Anthropic/Claude and the broader tech world.

## Key Files
- `newsletters/index.json` — log of all past issues (number, date, filename, subject line)
- `newsletters/YYYY-MM-DD-newsletter.html` — archived HTML issues
- `send_email.py` — sends the latest newsletter via Gmail SMTP
- `.env` — credentials (never commit this)

## When generating a newsletter

1. **Read `newsletters/index.json`** to find the last issue number and date.
   The new issue number = last + 1. The date range to cover = day after last issue date through today.
   If no previous issues exist, this is Issue #1 — cover the past 7 days.

2. **Search the web** for news in the date range. Prioritize:
   - anthropic.com/news and blog posts
   - docs.anthropic.com changelog
   - Major tech publications (The Verge, TechCrunch, Ars Technica, Wired, etc.)
   - Official company announcements from other major tech companies

3. **Write the newsletter** as a complete, self-contained HTML file with inline CSS.
   Follow the structure and style guide below exactly.

4. **Save the HTML** to `newsletters/YYYY-MM-DD-newsletter.html` (today's date).

5. **Update `newsletters/index.json`** — append the new issue entry.

## Newsletter Structure & Style

The newsletter name is **"Claude & Co."**.

### Required sections (in order):

1. **Header** — Newsletter name, issue number, date, a one-line tagline

2. **Reading Progress Bar** — A thin terracotta (`#C15F3C`) bar fixed at the very top
   of the viewport that grows from 0% to 100% width as the reader scrolls. Use JS
   to update `width` on scroll. See reference file for implementation.

3. **Intro + Hook Pullquote** — A short 2-3 sentence intro paragraph, followed by a
   hook callout box. The hook is a bordered box (left border accent color) with an
   italic serif pull quote highlighting the most compelling story, plus an
   "Also in this issue:" subtitle listing 2-3 other highlights. This hooks readers
   before they reach the glossary.

4. **Jargon Decoder** (collapsible, after hook) — A glossary of 5-8 technical terms
   used in THIS issue. Use a `<details>` toggle so technical readers can skip it.
   - Scan the newsletter for terms a non-technical reader wouldn't know (SDK, CLI, API,
     MCP, agent, context window, tokens, rate limits, fine-tuning, open-source, etc.)
   - Keep each definition to ONE line, casual, not textbook
   - Additionally, wrap the FIRST occurrence of each glossary term in the body text with
     an inline tooltip: `<span class="term" tabindex="0">TERM<span class="term-tip">definition</span></span>`
   - This gives hover/tap tooltips so readers don't have to scroll back to the glossary

5. **Anthropic Product News** — The headline section. Cover ALL Anthropic products:
   Claude models (Opus/Sonnet/Haiku releases & updates), Claude Code, Claude Cowork,
   Claude for Chrome/Excel, the API and Claude Platform, Claude apps, and anything
   else Anthropic ships or announces. New features, updates, pricing changes, launches.
   If genuinely no news, say so in one line rather than padding.

6. **Feature Deep-Dive / How-To** — Pick ONE feature (ideally recent or underused).
   Explain what it does, how to use it step-by-step, and why it matters.
   Be practical and concrete with examples.

7. **Broader Tech News** — Important AI and tech developments an emerging CS student
   and aspiring product manager should know about. On weeks where Anthropic news is thin,
   expand this section. 3-5 items typically.

8. **The Bigger Picture** — A short closing blurb (3-5 sentences) written from a
   product management perspective. Connect the dots between the issue's stories,
   highlight a strategic takeaway, or pose a thought-provoking question for aspiring
   PMs and CS students. This is the editorial voice of the newsletter.

9. **Reading / Watching / Listening** — 3-5 curated links to longer reads, videos,
   or podcasts relevant to this issue's topics. Include a one-line description for each.
   Verify all links are live (no 404s) before including them.

10. **Footer** — Brief sign-off, a "Share this newsletter" line with the signup form link
    (`https://forms.gle/pJGxqX6CKyVA9Km99`), link to archive, disclaimer that it's AI-generated.

### Tone
- Friendly, informative, like a well-written creator newsletter
- NOT a dry press release
- Frame things for an emerging CS student / aspiring PM audience
- Include source links inline (as HTML anchor tags)
- Target 8-10 minute read length

### HTML/CSS Requirements — Anthropic Typography & Design

**IMPORTANT: Use `newsletters/2026-05-22-newsletter.html` as the canonical design reference.
Copy its structure, fonts, colors, spacing, and styling exactly.**

#### Fonts (Anthropic's actual typefaces)
Include `@font-face` declarations in a `<style>` block in `<head>`:
- **Body text:** `'TiemposText', Georgia, 'Times New Roman', serif` — weight 400, size 16px, line-height 1.5, letter-spacing -0.01em
- **Headings & UI:** `'StyreneA', 'Helvetica Neue', Helvetica, Arial, sans-serif` — weight 500, letter-spacing -0.02em
- **Newsletter title:** `'StyreneB', 'StyreneA', 'Helvetica Neue', Helvetica, Arial, sans-serif` — 36px, weight 500, line-height 0.95
- Font files loaded from `https://www.anthropic.com/_next/static/media/`:
  - TiemposText_Regular, TiemposText_RegularItalic, TiemposText_Medium (.woff2)
  - StyreneA_Regular, StyreneA_Medium (.woff2)
  - StyreneB_Regular, StyreneB_Medium (.woff2)
- Apply `-webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale` on body

#### Colors (Claude palette — light/dark mode with toggle)
Use CSS custom properties with `data-theme` attribute on `<html>`. Include a toggle button and JS (see reference file).

**Light mode** (`data-theme="light"`):
- Outer bg: `#F4F3EE`, Container bg: `#FFFFFF`, Callout bg: `#F4F3EE`
- Text primary: `#2f2f2b`, Text secondary: `#4a4a44`, Muted: `#B1ADA1`, Faint: `#c5c1b8`
- Accent: `#C15F3C` (terracotta)
- Borders: `rgba(177,173,161,0.3)`, Link underline: `rgba(47,47,43,0.3)`

**Dark mode** (`data-theme="dark"`):
- Outer bg: `#2f2f2b` (warm charcoal), Container bg: `#3a3a36`, Callout bg: `#454540`
- Text primary: `#F4F3EE`, Text secondary: `#d5d3cb`, Muted: `#B1ADA1`, Faint: `#7a776e`
- Accent: `#C15F3C` (same terracotta)
- Borders: `rgba(244,243,238,0.1)`, Link underline: `rgba(244,243,238,0.3)`

Links: `color: var(--text-primary); text-decoration:underline; text-decoration-color: var(--link-underline); text-underline-offset:2px`

#### Layout
- Max-width container: 680px, centered
- Horizontal padding: 48px
- Section spacing: 36px vertical padding
- Section labels: StyreneA, 11px, uppercase, letter-spacing 0.18em, color var(--accent), weight 500, with bottom border divider
- Sub-headings: StyreneA, 21px, weight 500, letter-spacing -0.02em
- Callout/tip boxes: `background-color: var(--bg-callout); border-radius:4px; padding:16px 20px`
- Include a circular theme toggle button (fixed, top-right corner) with moon/sun SVG icons
- Include JS to toggle `data-theme` and persist choice in `localStorage`
- NO emojis anywhere
- Mobile-friendly (no fixed widths on inner elements)
