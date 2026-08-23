---
description: The CC license families in plain language: what each requires and when to use which.
---

# License briefs (plain language, not legal advice)

| License | Credit? | Commercial? | Modifications? | When to pick |
|---|---|---|---|---|
| CC0 | not required (nice) | yes | yes | Blog heroes, product surfaces, "just let me use it" |
| PDM (Public Domain Mark) | not required | yes | yes | Same as CC0; work already public domain |
| CC BY | REQUIRED | yes | yes (credit + link to license) | Default for most projects |
| CC BY-SA | REQUIRED | yes | yes, but derivatives share alike | Wikis, Wikipedia-adjacent use |
| CC BY-NC | REQUIRED | NO | yes | Personal, editorial, nonprofit only |
| CC BY-NC-SA | REQUIRED | NO | yes, share alike | Non-commercial communities |
| CC BY-ND | REQUIRED | yes | NO (no edits/crops that matter) | When the image is used untouched |
| CC BY-NC-ND | REQUIRED | NO | NO | Most restricted; rarely the right pick |

## Practical rules for agents

1. User says "commercial use" or "client work" → exclude NC licenses (pass
   `license='by'` or `'cc0'`, or filter results).
2. User says "no attribution" or "social media image dump" → `license='cc0'`
   (or `pdm`).
3. User will crop/edit → exclude ND.
4. Any SA license taints the derivative's license — say so before the user
   builds on it.
5. When unsure, surface the `license_url` and let the human decide.
