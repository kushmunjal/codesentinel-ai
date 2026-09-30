import json

with open("dashboard/index.html", "r") as f:
    html = f.read()

# Tick off Phase 5
html = html.replace(
    '<span class="text-slate-600">&#9675;</span> Phase 5: PR Review Pipeline',
    '<span class="text-green-500">&#10003;</span> Phase 5: PR Review Pipeline'
)

# Load the real review
try:
    with open("dashboard/latest_review.json", "r") as f:
        data = json.load(f)
        
    findings_html = ""
    for finding in data["findings"]:
        findings_html += f"""
        <div class="mb-4 border border-slate-700 bg-slate-800 rounded p-4 text-left">
            <div class="flex justify-between items-center mb-2">
                <span class="font-bold text-slate-300">{finding['file']}:{finding['line']}</span>
                <span class="px-2 py-1 rounded text-xs bg-red-900/50 text-red-400 border border-red-800">{finding['severity'].upper()} - {finding['category']}</span>
            </div>
            <p class="text-sm text-slate-400 mb-2">{finding['explanation']}</p>
            <pre class="bg-slate-900 p-2 rounded text-xs text-emerald-300 overflow-x-auto">{finding.get('suggested_fix', '')}</pre>
        </div>
        """
        
    diff_html = f"""<div class="mb-4"><h3 class="font-bold text-slate-300 text-left mb-2">PR Diff Snippet</h3><pre class="bg-slate-900 p-2 rounded text-xs text-blue-300 overflow-x-auto text-left">{data['diff'][:500]}...</pre></div>"""
    
    new_div = f'<div class="p-4 border border-slate-600 rounded bg-slate-800/50">{diff_html}{findings_html}</div>'
    
    # We replace the section that says "Diff Pipeline Active" from phase 3
    import re
    html = re.sub(r'<div class="p-4 border border-slate-600 rounded bg-slate-800/50 text-left">.*?</div>', new_div, html, count=1, flags=re.DOTALL)
except Exception as e:
    print("Error patching html:", e)

with open("dashboard/index.html", "w") as f:
    f.write(html)
