import json

with open("dashboard/index.html", "r") as f:
    html = f.read()

# Tick off Phase 6
html = html.replace(
    '<span class="text-slate-600">&#9675;</span> Phase 6: Issue Triage Pipeline',
    '<span class="text-green-500">&#10003;</span> Phase 6: Issue Triage Pipeline'
)

# Load the real triage
try:
    with open("dashboard/latest_triage.json", "r") as f:
        data = json.load(f)
        
    labels_html = "".join([f'<span class="px-2 py-1 bg-blue-900/50 text-blue-400 border border-blue-800 rounded text-xs mr-2">{l}</span>' for l in data['labels']])
    
    triage_div = f"""
    <div class="p-4 border border-slate-600 rounded bg-slate-800/50 text-left">
        <h3 class="font-bold text-slate-300 mb-2">{data['title']}</h3>
        <div class="mb-4">{labels_html}</div>
        <div class="flex items-center gap-2 mb-2">
            <span class="text-sm text-slate-400">Priority:</span>
            <span class="px-2 py-1 bg-purple-900/50 text-purple-400 border border-purple-800 rounded text-xs">{data['priority'].upper()}</span>
        </div>
        <div class="flex items-center gap-2 mb-4">
            <span class="text-sm text-slate-400">Possible Duplicate:</span>
            <span class="px-2 py-1 {'bg-red-900/50 text-red-400 border-red-800' if data['duplicate_flag'] else 'bg-emerald-900/50 text-emerald-400 border-emerald-800'} rounded text-xs">
                {'YES' if data['duplicate_flag'] else 'NO'}
            </span>
        </div>
        <p class="text-xs text-slate-400 italic">"{data['comment']}"</p>
    </div>
    """
    
    old_div = '<div class="p-4 border border-dashed border-slate-600 rounded bg-slate-800/50 text-center text-slate-500">\n                    Placeholder &mdash; wired up in a later phase\n                </div>'
    
    html = html.replace(old_div, triage_div, 1) # Only replace the first one (Issue Triage)
except Exception as e:
    print("Error patching html:", e)

with open("dashboard/index.html", "w") as f:
    f.write(html)
