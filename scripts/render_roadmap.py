import pathlib

import yaml
from jinja2 import Template

ROOT = pathlib.Path(__file__).resolve().parents[1]
rf = ROOT / "docs" / "roadmap" / "roadmap.yaml"
if not rf.exists():
    raise SystemExit(0)
with open(rf) as f:
    roadmap = yaml.safe_load(f)
md = Template(
    "# ROADMAP\n{% for _i in roadmap %}## {{i.id}} — {{i.title}}\n- **Owner:** {{i.owner}}\n- **Start:** {{i.start}}\n- **Target:** {{i.target}}\n- **Status:** {{i.status}}\n- **KPIs:** {% for _k in i.kpis %}`{{k}}`{% if not loop.last %}, {% endif %}{% endfor %}\n- **Links:** {% for k,v in i.links.items() %}[{{k}}]({{v}}){% if not loop.last %}, {% endif %}{% endfor %}\n{% endfor %}"
).render(roadmap=roadmap)
with open(ROOT / "docs" / "ROADMAP.md", "w") as f:
    f.write(md)
print("Rendered docs/ROADMAP.md")
