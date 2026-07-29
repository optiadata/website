# Optia Website Build — Claude Code Prompt

Paste this whole file to Claude Code as your opening instruction (or save it as `CLAUDE.md` in the project root so it stays in context). Three assets referenced below still need to land in the project folder before Claude Code can execute fully — see **OPEN ITEMS** at the bottom. Everything else is ready to build from.

---

## 0. Skills to load before starting

Before any design or build work, check your available skills for these two and read them in full — they take precedence over the general guidance in this document where they're more specific:

- **`frontend-dev`** — covers Design DNA, the anti-generic-AI-look pattern catalogue, SEO-complete build practices, and framework-specific code quality guidance. (Being added to this project folder — if it's not yet present, check again before finalising the design plan in §1.)
- **`ui-ux-pro-max`** (folder: `C:\Users\helen\.claude\skills\ui-ux-pro-max`) — apply its guidance alongside `frontend-dev`, not instead of it. If you can't find a skill by this name, say so explicitly rather than silently skipping it, and proceed on `frontend-dev` plus the rest of this brief.

If both skills give overlapping advice, follow the more specific/opinionated instruction rather than the generic one. If they conflict, flag the conflict rather than picking silently.

## 1. Role and standard

Act as a Senior Design Director with 20 years in editorial, luxury and technology branding — the kind of eye behind studios like Bureau Borsche, Instrument, Pentagram's digital arm, or Zero Density. You are not a template assembler. Before writing code, think like a designer: form a point of view, defend it, then build it with engineering precision.

Non-negotiables:
- No emoji, anywhere, in copy, comments, commits or UI.
- Nothing that reads as AI-generated. That means: no generic Inter/system-ui fallback moments, no soft-shadow rounded-corner card grids, no gradient blobs, no stock "diverse team high-fiving" photography, no tick-mark bullet lists, no cliché SaaS hero with a laptop mockup, no centred-everything layout with a big rounded CTA button.
- Specifically avoid the three patterns AI design tools default to: (1) warm cream background with high-contrast serif and a terracotta accent, (2) near-black background with a single neon-green or vermilion accent, (3) broadsheet hairline-rule newspaper layout used as a crutch rather than a choice. If Optia's palette or the Zodiak serif happens to overlap one of these by coincidence, that's fine — just don't default into it lazily.
- Editorial, minimal, elegant, with one funky/artistic risk per major section rather than noise everywhere. Restraint is the discipline; the signature moment is where you spend the boldness.

Work in two passes, out loud, before touching final code:
1. **Design plan** — a compact token system: colour (named hex values and their exact usage rule), type (roles and weights for Switzer and Zodiak), layout concept per section (one-sentence description + ASCII wireframe), and the signature element each page will be remembered by.
2. **Self-critique** — check the plan against the brief. If any part of it is the generic answer you'd give any consultancy site, revise it and say what changed. Only then build.

Take screenshots as you go and critique your own work before calling anything done.

---

## 2. Who this is for and what it needs to do

Optia is a five-person UK data and AI consultancy delivering Nielsen/Circana/Kantar analytics and Power BI dashboards to CPG, financial services, engineering, education and health clients. The homepage speaks to commercial, category and insight leaders — not technical buyers. The Core page speaks to data and IT people specifically; it's the one place a more technical tone is correct.

Positioning in one line: Optia is a practical intelligence company for consumer brands. It brings fragmented market, retailer, innovation and internal data together, makes it reliable, and puts a named analyst behind every number. Not an AI company. Not a software company.

Launch target: 1 August 2026 (Optia's two-year anniversary as an independent company).

---

## 3. Tech stack (assumption — adjust if you already have a scaffold in this folder)

- **Next.js 14+, App Router, TypeScript.**
- **Tailwind CSS** for utility scaffolding only — all actual design tokens (colour, type scale, spacing) defined as CSS variables / a `theme` extension, never left as Tailwind defaults.
- **GSAP + ScrollTrigger** for the orchestrated scroll and load animations; **Lenis** for smooth scroll.
- **next/font/local** to self-host Switzer and Zodiak as variable fonts (see §5). No Google Fonts, no CDN font-loading flash.
- Static export or standard Vercel/Netlify deployment — confirm hosting target before wiring up build config (memory shows a prior Netlify deployment issue was left unresolved; check that before assuming Netlify again).
- Accessibility floor: visible keyboard focus on every interactive element, `prefers-reduced-motion` respected (all GSAP timelines get a reduced-motion fallback that cuts to instant/opacity-only), semantic HTML landmarks, alt text on every image.

---

## 4. Colour system

**[PENDING — see Open Items. Do not invent a palette; wait for the exact hex values.]**

Once supplied, apply this rule without exception, because it's the client's explicit instruction:

> Every text/background pairing must pass a hard light-dark contrast check. White or near-white type on any dark or saturated background. Ink/near-black type on any light background. Never place a mid-tone colour behind mid-tone text just because both are "on brand" — brand colours are for bold full-bleed fields and accents, not for producing a washed-out pairing.

Be bold with colour blocking: full-bleed saturated sections, confident colour transitions between sections, not pastel tints or 10%-opacity accent washes. Use accent colours the way an editorial magazine uses a spot colour — deliberately and sparingly against a disciplined base.

Build the palette into Tailwind as named CSS variables (e.g. `--optia-ink`, `--optia-paper`, `--optia-accent-1`) so every component references the token, never a raw hex.

---

## 5. Typography

Only two typefaces are permitted. Both are Fontshare variable fonts — self-host them, don't link Fontshare's CDN in production.

**Switzer** — neo-grotesque sans, variable weight axis 100 (Thin) to 900 (Black), 9 weights plus italics. This is the workhorse: navigation, body copy, UI labels, captions, buttons, forms. Use its variable axis properly — interpolate weight for hover/active states and micro-interactions rather than swapping static files.

**Zodiak** — high-contrast display serif with slab-like bracketed serifs, 6 weights (Thin to Black) plus italics, also variable. This is the editorial voice: hero statements, section openers, pull quotes, the one or two big declarative lines per page that should feel considered rather than functional. Use it with restraint — it's the character actor, not the lead in every scene.

Pairing logic: Switzer's neutrality is the stage; Zodiak's character is what stands on it. Don't let both compete in the same line of text — establish a clear rule (e.g. Zodiak only for headline-level type above a certain size, Switzer for everything functional) and hold it consistently.

**Dynamic hero typography — best-effort spec, confirm against the source deck once uploaded (see Open Items):**
The hero headline is:

> Intelligence.
> Practically applied, moving you forward with confidence

Treat "Intelligence." as the typographic hero moment: set it in Zodiak at large display scale, and animate its variable weight axis on load or scroll (e.g. interpolating from a light weight to Black, or oscillating gently) so the word itself performs the idea of something coming into focus. The second line sits underneath in Switzer at a calmer, smaller scale, as the grounded, practical counterpoint to the first line's drama. This word-level variable-font animation is the "fonts change dynamically" behaviour referenced in the brief — build it as a reusable component, since it may need to reappear at smaller scale elsewhere (e.g. section openers on Approach).

---

## 6. Opening interaction — circle / wordmark intro

Reference: neuemontreal.com (Pangram Pangram's PP Neue Montréal site). Note for whoever is running Claude Code: this reference is a heavily animated Framer site; a text fetch of it cannot capture the exact motion, so treat the following as the genre to build in this spirit, not a pixel-accurate spec — confirm the precise choreography with Helena if she has a screen recording or more specific reference.

Build a load-in sequence: a circle (containing or forming the word "Optia," set in Switzer or Zodiak — designer's call, test both) that the visitor sees first, before the page reveals itself. The circle should feel like a considered threshold, not a generic "spinner" — think an aperture opening, a circle that scales and resolves into the wordmark, then dissolves or expands outward to reveal the hero underneath. Keep it fast (sub-2-second budget) and skippable/interruptible on scroll or click so it never becomes an obstacle for a returning visitor. Respect `prefers-reduced-motion` by skipping straight to the resolved state.

---

## 7. Logo

**[PENDING — see Open Items.]** File referenced: `Optia__Logo_RGB_white-01.svg` — a white lockup, intended for dark backgrounds. Once supplied:
- Check whether the SVG uses a single fill colour (in which case it can be recoloured via CSS `currentColor` for flexible placement) or is multi-colour/locked (in which case treat it as a fixed asset and request an ink/dark variant for light backgrounds rather than trying to invert it programmatically).
- Standard lockup rules: consistent clear space around the mark equal to the height of the "O", never stretched, never placed on a background that fails the contrast rule in §4.

---

## 8. Site map and page-by-page content

Use the exact copy below verbatim — this is signed-off client content, not a starting draft. Do not paraphrase, embellish, or "improve" it. Where the source has bracketed placeholders (`[Case study...]`, `[Name]`, `[email]` etc.) or open editorial questions (marked in the source with things like "(fresh?)" or italic asides), leave them as clearly marked TODO placeholders in the code — comment them as `{/* TODO: awaiting client sign-off */}` — rather than inventing content to fill the gap.

Site map: **Hero → Solutions (3 pillars + Capabilities) → Customers (all verticals) → Approach (core mechanism + AI approach, combined) → Core (technical backbone) → Contact (button).** Homepage audience: commercial/category/insight leaders. Core page audience: data/IT.

### Home — Hero

> **Intelligence.**
> **Practically applied, moving you forward with confidence**

You know AI is changing the way we work. Knowing what to do about it is harder.

Optia builds the right foundations, bringing together fragmented data, fixing manual processes and developing numbers you can trust; we then help your people turn them into intelligence they can act on.

**Trusted data. Practical intelligence. Confident decisions.**

### Solutions

Three things, built on top of each other. Most clients start where their data is today and move up as it earns their trust.

**Foundation: get the data right** — We bring syndicated market data and your internal numbers into one governed, audited place (in cloud, on prem, or their private cloud), reconciled and reliable, with a clear trail of where every figure came from. The result: numbers that match, and reporting that runs itself. This is the step most people skip, and it's why their AI gives confident, wrong answers.

**Context: teach the data your business** — Data on its own doesn't know your categories, your definitions, your hierarchies or your quirks. We capture that meaning and hold it as a managed layer: the business rules, definitions and relationships that let your people and any AI read your data correctly instead of guessing. This is what we mean by speaking your data's language.

**Intelligence: turn data into decisions** — Dashboards, plain English answers and enhanced assisted analysis, every output signed off by a named analyst before it reaches you. Each insight carries what it's worth and what we'd do about it, and every recommendation is scored against what actually happened. The result: decisions made with confidence.

CTA: Not sure which of these fits where you are today? **[Start a conversation]**

Capabilities (for visitors who want the substance):
- **Data and Analytics engineering** — Ingestion, harmonisation and reconciliation of syndicated and internal data, with full lineage, delivered into a governed, audited environment, or into your own tenant or Power BI where you prefer. Cloud infrastructure, data lakes, warehouses, bespoke tech stacks.
- **AI and practical intelligence** — Context layers, plain English querying and AI-assisted analysis over data we have made reliable, always with a named analyst accountable for the output.
- **Verticals** — Consumer goods is our focus today, where we know the market data inside out. Working in another sector with fragmented data? Talk to us. The engineering travels well.

### Customers

Section header: **Customers**

**Consumer**
- Samworth Brothers — [Case study: the challenge, what we built, the result. Awaiting sign-off.]
- Stemilt — [Case study: the challenge, what we built, the result. Awaiting sign-off.]
- CTA: Want to see what this looks like on your data? **[Start a conversation]**
- Logos/names to display: Starbucks, Arla, International Beverage, Bacardi, Campari, Golden Acre Foods, Samyang Foods, Henkel, VitHit

**Financial Services** — MUFG, Clear One Advantage

**Engineering** — QTS Data Centres, Saulsbury Industries

**Education** — Inspired Learning Group, VentureEd

**Health** — Rethink First, Oracare

Note: two additional use cases are still to be added — leave a clearly marked slot for them.

### Approach

Section header: **Approach — Practical Intelligence starts with trust**

Almost every organisation knows Artificial Intelligence matters. Far fewer know where to begin. Most advice starts with choosing a model, buying a platform or deploying a chatbot. Our experience has been different. The hardest part isn't choosing the right AI. It's giving AI information it can trust. Ask the most sophisticated model a question over fragmented, contradictory or poorly governed data and you'll receive a confident answer. It just may not be the correct one. That's why we don't begin with AI. We begin with trust.

**We build confidence before intelligence** — Every engagement follows the same principle. First, we understand how your business makes decisions. Then we bring together syndicated market data, retailer data and your internal systems into one governed, auditable foundation. Next, we capture the business rules, hierarchies and commercial context that give your data meaning. Only then do we apply AI. The result isn't simply better reporting. It's intelligence your teams can act on with confidence.

**AI interprets the question. Your governed data calculates the answer.** — This simple distinction sits at the heart of everything we do. Large language models are excellent at understanding what people are asking. They are not systems of record. Every answer comes from governed, auditable data through business rules and transformations that can be explained. AI becomes the interface. Your data remains the source of truth.

**Technology supports people. It doesn't replace them.** — The goal isn't to automate judgement. It's to automate repetitive work so experts can spend more time making better decisions. Whether we're delivering dashboards, automated reporting, decision briefings or AI-assisted analysis, every important output is reviewed by a named analyst who understands both the data and the commercial context. Technology accelerates the work. People remain accountable.

**Practical AI, not AI for its own sake** — Some organisations need predictive modelling. Others need workflow automation. Some simply need reporting they can finally trust. Our role isn't to sell AI. It's to recommend the right combination of data engineering, analytics, automation and Practical Intelligence for your business today, while creating foundations that allow you to adopt more advanced AI when the time is right. Sometimes AI is the answer. Sometimes it isn't. We'll tell you the difference.

**Confidence isn't claimed. It's earned.** — Trust comes from transparency. Every recommendation can be traced back to the data behind it. Every important output has a person accountable for it. Every engagement is designed to leave your organisation with cleaner data, smarter processes and greater confidence in every commercial decision. That's what we mean by Practical Intelligence.

### Core

Section header: **Core — For the people who have to trust this too**

If you own data or IT, you're the one who has to be comfortable with how this works. Here's the straight version.

**Governed, not guessed.** Every figure comes from your governed data through versioned, auditable transformations, not a model's best guess. AI asks the question; your governed data gives the answer.

**A full trail.** We hold every inbound source with complete lineage, so which data, which version and how it was derived always has an answer. Our environment is ISO 27001 aligned, with per-client isolation.

**Why this matters more in the AI era.** A statistical model gives a plausible answer; commercial decisions need a precise one. You get precise answers from AI by giving it a foundation it can trust and rules it must follow. That is the work we do.

**Coexists with what you have.** Where you mandate Power BI or your own tenant, we deliver clean, governed data into it with our lineage intact. We don't ask you to rip anything out.

Stat line (treat as a large-scale editorial number moment, not a generic stat-card grid): **400 processes, 400 dynamic tables, 8 billion rows, eight products.**

CTA: **[Talk to our technical team]**

### About

**Who we are** — We're a specialist consumer goods data team. We've spent years in the detail of syndicated datasets, doing the unglamorous work that makes commercial numbers reliable, for brands like [named clients]. We're small on purpose: work with us and you deal directly with the people doing the work.

**Our story** — Two years as Optia, marked on 1 August 2026, built on around 20 years of data heritage: building and maintaining data platforms and software, and understanding the needs of our customers, who, in every single case, wanted a solution, not more tech to have to figure out how to use.

**Why a name matters** — Every output we send has a person behind it: a named analyst who has checked the number and will stand behind it. In a market rushing to automate the human away, we think the human is the point. Trust is earned, not claimed.

**The team** — Leadership team and analyst team, with names, photos and one honest line each. [TODO: awaiting names/photos/lines.] Footprint spans the UK, Spain, India and the UAE — show this on a small map.

### Contact

**Let's talk** — No pitch and no jargon. Tell us what's slowing your commercial decisions down and we'll show you how we'd approach it, including a real briefing on real data so you can see exactly what you'd get.

Form fields: Name / Company / Email / What's on your mind? / **[Start a conversation]**

Direct: [email] · [phone] · [LinkedIn]

---

## 9. Voice and copy guardrails

The copy above is final and must be used as-is. For any microcopy Claude Code has to originate itself (button hover states, form validation messages, 404 page, meta descriptions, image alt text), write it to this voice:

- British English throughout (organisation, optimise, analysed).
- Plain, concrete, Year 9–11 reading level. Short sentences, one idea per paragraph.
- Never oversell: avoid "always," "never," "guaranteed," "perfect." Prefer "usually," "often," "designed to," "helps."
- Banned words unless truly unavoidable: leverage, synergy, cutting-edge, best-in-class, revolutionary, world-class, game changer, paradigm, seamless, holistic, state-of-the-art, disruptive, utilise, empower, "enable organisations to," digital transformation, AI-powered, next generation, solutioning, framework (unless it's a literal framework).
- Never use the AI-cliché false-contrast structure ("it isn't X, it's Y"; "not this, not that, but this"; "X is dead"; "here's the thing"; "let that sink in").
- Never describe client data as untrustworthy or bad — it's fragmented and misaligned, not wrong.
- Never position Optia as an AI company or a software company. Avoid "solutions" as a noun and "human oversight" as a standalone claim.
- No em dashes anywhere in copy or code comments.

---

## 10. Build process for Claude Code

1. Confirm the three pending assets are in the repo (§12). If not all are present, proceed with the sections that don't depend on them (content structure, Switzer/Zodiak type system, layout, Solutions/Approach/Core/About/Contact pages) and stub the hero and colour system clearly rather than guessing.
2. Load and apply the `frontend-dev` and `ui-ux-pro-max` skills per §0. Produce the two-pass design plan from §1 and show it before writing page code. Get it reviewed.
3. Build the design token layer first (CSS variables for colour and type), then layout primitives, then page by page: Home → Solutions → Customers → Approach → Core → About → Contact.
4. Build the hero circle-intro and the dynamic Zodiak weight-animation as isolated, reusable components early, since they're the highest-risk custom animation work.
5. After each page, take a screenshot and self-critique against the "no AI-look" list in §1 before moving on.
6. Final pass: responsive check at mobile/tablet/desktop, keyboard-navigation check, reduced-motion check, and a read-through of every page against §9's voice rules.

---

## 11. Production checklist (from the signed-off content doc — carry these through as literal TODOs in the code, not silent gaps)

- [ ] Client logos and names cleared for Home, Work and About.
- [ ] Team photos and confirmed titles; offices map for the UK, Spain, India and the UAE.
- [ ] Anonymised sample decision briefing built, used anywhere a live figure would otherwise appear, so no unvalidated number is ever shown.
- [ ] Technical wording on ISO 27001 and lineage confirmed by Pankaj; core mechanism line checked.
- [ ] Confirm "practical intelligence" carries no brand clash before launch.

---

## 12. OPEN ITEMS — needed before this can be fully executed

Only the copy document made it through in full. Three referenced assets weren't attached and need to be added to the project folder (or re-sent) before Claude Code can build against them precisely:

1. **Colour palette** (`colour code.png`) — exact hex values and which are backgrounds vs accents vs text. Until this lands, §4 is a placeholder and Claude Code should not invent brand colours.
2. **Hero reference deck** (`Presentation1.pptx`) — the actual layout/animation the hero should match, including how the "fonts change dynamically" behaviour is meant to look. §5's hero spec is a reasonable best guess from the brief text alone, not a substitute for seeing the deck.
3. **Logo file** (`Optia__Logo_RGB_white-01.svg`) — needed for §7 and for the header/footer/favicon build.

Once those are in the repo, tell Claude Code to re-read §4, §5, §6 and §7 and finalise them against the real assets rather than the placeholder guidance.
