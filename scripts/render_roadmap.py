import yaml, pathlib
from jinja2 import Template
ROOT = pathlib.Path(__file__).resolve().parents[1]
rf = ROOT/'docs'/'roadmap'/'roadmap.yaml'
if not rf.exists(): raise SystemExit(0)
roadmap = yaml.safe_load(open(rf))
md = Template("# ROADMAP\n{% for i in roadmap %}## {{i.id}} — {{i.title}}\n- **Owner:** {{i.owner}}\n- **Start:** {{i.start}}\n- **Target:** {{i.target}}\n- **Status:** {{i.status}}\n- **KPIs:** {% for k in i.kpis %}`{{k}}`{% if not loop.last %}, {% endif %}{% endfor %}\n- **Links:** {% for k,v in i.links.items() %}[{{k}}]({{v}}){% if not loop.last %}, {% endif %}{% endfor %}\n{% endfor %}").render(roadmap=roadmap)
open(ROOT/'docs'/'ROADMAP.md','w').write(md)
print("Rendered docs/ROADMAP.md")
