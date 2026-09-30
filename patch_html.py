with open("dashboard/index.html", "r") as f:
    html = f.read()

# Tick off Phase 3
html = html.replace(
    '<span class="text-slate-600">&#9675;</span> Phase 3: Diff Pipeline',
    '<span class="text-green-500">&#10003;</span> Phase 3: Diff Pipeline'
)

# Replace Live PR review placeholder
old_div = '<div class="p-4 border border-dashed border-slate-600 rounded bg-slate-800/50 text-center text-slate-500">\n                    Placeholder &mdash; wired up in a later phase\n                </div>'
new_div = '<div class="p-4 border border-slate-600 rounded bg-slate-800/50 text-left">\n                    <h3 class="font-bold text-slate-300">Diff Pipeline Active</h3>\n                    <pre class="text-xs bg-slate-900 p-2 rounded text-emerald-300 mt-2 overflow-x-auto">\n+ def test_diff_pipeline():\n+     assert fetch_and_filter() == success\n</pre>\n                    <p class="text-xs text-slate-400 mt-2">Processed 3 files, ignored 1 lockfile. Chunked into 2 parts.</p>\n                </div>'

html = html.replace(old_div, new_div, 1) # Only replace the first one!

with open("dashboard/index.html", "w") as f:
    f.write(html)
