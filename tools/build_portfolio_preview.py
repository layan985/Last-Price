from __future__ import annotations

import urllib.request
from pathlib import Path

SOURCE = "https://layan-aloreidi-portfolio.vercel.app"
OUT = Path("portfolio-live-preview.html")

with urllib.request.urlopen(SOURCE, timeout=30) as response:
    html = response.read().decode("utf-8")

canonical = """<link rel=\"canonical\" href=\"https://layanaloreidi.online/\"><meta property=\"og:url\" content=\"https://layanaloreidi.online/\">"""
if 'rel="canonical"' not in html:
    html = html.replace("</head>", canonical + "</head>", 1)

last_price = r'''
<section class="section dark" id="last-price">
  <div class="shell">
    <div class="head">
      <div>
        <div class="kicker">05 / APPLIED ML · SQL · MLOPS</div>
        <h2>Last Price.</h2>
      </div>
      <p>A marketplace machine-learning system built around a bargaining experiment: SQL analytics, leakage-safe temporal evaluation, classification and conditional-price regression, decision-policy scoring, FastAPI serving, Docker, CI, model-run logging and drift monitoring.</p>
    </div>
    <div class="bench">
      <article><small>AGREEMENT MODEL · HELD-OUT</small><h3>0.789</h3><p>ROC-AUC versus a 0.500 dummy baseline. Brier score improves from 0.196 to 0.164.</p></article>
      <article><small>CONDITIONAL PRICE · HELD-OUT</small><h3>3.33</h3><p>RMSE versus 28.79 for the median baseline. MAE: 2.54 versus 23.72.</p></article>
      <article><small>LEAKAGE CONTROL</small><h3>0</h3><p>Scenario IDs shared across train and test. The newest 125 scenarios form the held-out period.</p></article>
      <article><small>ENGINEERING GATE</small><h3>6 / 6</h3><p>Tests pass in CI alongside a deterministic rebuild, data-quality gate, leakage audit and Ruff.</p></article>
    </div>
    <div class="challenge">
      <div>
        <div class="kicker">EVIDENCE BOUNDARY</div>
        <h3>Production-style engineering. Synthetic evidence.</h3>
        <p>The shipped negotiations use deterministic mechanical policies. The repository does not present these results as commercial production impact or evidence about real commercial LLMs. The next credibility gate is independent reproduction.</p>
      </div>
      <div class="actions">
        <a class="btn hot" href="https://github.com/layan985/Last-Price">OPEN REPOSITORY ↗</a>
        <a class="btn" style="color:white;border-color:#777" href="https://github.com/layan985/Last-Price/issues/3">REPRODUCE IT ↗</a>
        <a class="btn" style="color:white;border-color:#777" href="https://last-price-live-exec.vercel.app">EXECUTION ENDPOINT ↗</a>
      </div>
    </div>
  </div>
</section>
'''

# Insert before the profile section in the currently deployed portfolio.
needle = '<section class="section shell"><div class="kicker">PROFILE</div>'
if needle not in html:
    raise SystemExit("Profile insertion point not found; refusing to publish an unverified mutation.")
html = html.replace(needle, last_price + needle, 1)

# Update the footer identity without fabricating a deployment claim.
html = html.replace("RESEARCH / CODE / EVIDENCE</span>", "RESEARCH / CODE / EVIDENCE · LAYANALOREIDI.ONLINE</span>", 1)

OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
