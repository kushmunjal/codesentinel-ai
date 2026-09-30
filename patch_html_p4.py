with open("dashboard/index.html", "r") as f:
    html = f.read()

# Tick off Phase 4
html = html.replace(
    '<span class="text-slate-600">&#9675;</span> Phase 4: LLM Layer & Schemas',
    '<span class="text-green-500">&#10003;</span> Phase 4: LLM Layer & Schemas'
)

with open("dashboard/index.html", "w") as f:
    f.write(html)
