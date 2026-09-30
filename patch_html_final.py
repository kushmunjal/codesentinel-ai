with open("dashboard/index.html", "r") as f:
    html = f.read()

for i in range(7, 11):
    html = html.replace(
        f'<span class="text-slate-600">&#9675;</span> Phase {i}',
        f'<span class="text-green-500">&#10003;</span> Phase {i}'
    )

with open("dashboard/index.html", "w") as f:
    f.write(html)
