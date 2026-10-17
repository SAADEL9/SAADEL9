"""Generate animated contribution-snake SVGs (dark + light) from live GitHub data.
Standard library only. Usage: GITHUB_USER=name python scripts/generate_snake.py
"""
import datetime, os, re, sys, urllib.request

USER = os.environ.get("GITHUB_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "SAADEL9"
OUT = os.environ.get("OUT_DIR", ".")
D, A, B = 30, 0.16, 0.88  # loop seconds, snake start/end (fraction of loop)

def fetch():
    local = os.environ.get("CONTRIB_HTML")
    if local:
        return open(local, encoding="utf-8").read()
    req = urllib.request.Request(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")

def parse(h):
    cells = {}
    for m in re.finditer(r'<td[^>]*?data-date="([^"]+)"[^>]*?id="contribution-day-component-(\d+)-(\d+)"[^>]*?data-level="(\d)"', h):
        d, r, c, l = m.groups()
        cells[(int(c), int(r))] = (d, int(l))
    t = re.search(r'([\d,]+)\s+contributions\s+in the last year', h)
    if not cells or not t:
        sys.exit("Could not parse contribution data; leaving existing files untouched.")
    return cells, t.group(1)

PALETTES = {
    "dark": dict(e="#161b22", lv=["#0e4429", "#006d32", "#26a641", "#39d353"], lbl="#7d8590", tot="#e6edf3", sn="#a78bfa", sh="#22d3ee"),
    "light": dict(e="#ebedf0", lv=["#9be9a8", "#40c463", "#30a14e", "#216e39"], lbl="#57606a", tot="#1f2328", sn="#7c3aed", sh="#2563EB"),
}

def build(cells, tot):
    W = max(c for c, _ in cells) + 1
    order = []
    for c in range(W):
        rs = [r for r in range(7) if (c, r) in cells]
        order += [(c, r) for r in (rs if c % 2 == 0 else rs[::-1])]
    N = len(order); idx = {k: i for i, k in enumerate(order)}
    lag = (B - A) / (N - 1)
    months, last = [], None
    for c in range(W):
        d = next(datetime.date.fromisoformat(cells[(c, r)][0]) for r in range(7) if (c, r) in cells)
        if d.month != last:
            months.append((c, d.strftime("%b"))); last = d.month
    if len(months) > 1 and months[1][0] - months[0][0] < 3:
        months.pop(0)
    width = 34 + 16 * W + 6
    path = "M" + " L".join(f"{34+16*c+6.5:g} {24+16*r+6.5:g}" for c, r in order)
    for n, p in PALETTES.items():
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="158" viewBox="0 0 {width} 158" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif" role="img" aria-label="Animated GitHub contribution graph: {tot} contributions in the last year, eaten by a snake">',
             f'<style>text.lbl{{fill:{p["lbl"]};font-size:13px;font-weight:600}}text.total{{fill:{p["tot"]};font-size:15px;font-weight:700}}</style>']
        for c, mn in months:
            o.append(f'<text class="lbl" x="{34+16*c}" y="16">{mn}</text>')
        for r, l in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
            o.append(f'<text class="lbl" x="2" y="{24+16*r+11}">{l}</text>')
        for (c, r), (d, l) in sorted(cells.items()):
            col = p["e"] if l == 0 else p["lv"][l - 1]
            pp = .005 + c * .0022 + r * .0008
            a = f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{pp:.4f};{pp+.015:.4f};0.95;1" dur="{D}s" repeatCount="indefinite"/>'
            if l > 0:
                t = A + (B - A) * idx[(c, r)] / (N - 1)
                a += f'<animate attributeName="fill" calcMode="discrete" values="{col};{p["e"]};{col}" keyTimes="0;{t:.4f};0.97" dur="{D}s" repeatCount="indefinite"/>'
            o.append(f'<rect x="{34+16*c}" y="{24+16*r}" width="13" height="13" rx="2.5" fill="{col}" opacity="0">{a}</rect>')
        for k in range(6):
            a0, b0 = A + k * lag, B + k * lag
            s = 11 - k * .8; col = p["sh"] if k == 0 else p["sn"]
            o.append(f'<rect x="{-s/2:.1f}" y="{-s/2:.1f}" width="{s:.1f}" height="{s:.1f}" rx="3" fill="{col}" opacity="0"><animateMotion dur="{D}s" repeatCount="indefinite" path="{path}" calcMode="linear" keyPoints="0;0;1;1" keyTimes="0;{a0:.4f};{b0:.4f};1"/><animate attributeName="opacity" calcMode="discrete" values="0;1;0" keyTimes="0;{a0:.4f};{b0:.4f}" dur="{D}s" repeatCount="indefinite"/></rect>')
        o.append(f'<text class="total" x="34" y="152">{tot} contributions in the last year</text></svg>')
        with open(os.path.join(OUT, f"snake-{n}.svg"), "w", encoding="utf-8") as f:
            f.write("\n".join(o))
    print(f"{USER}: {tot} contributions, {N} days -> snake-dark.svg, snake-light.svg")

if __name__ == "__main__":
    cells, tot = parse(fetch())
    build(cells, tot)
