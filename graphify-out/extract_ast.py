import sys, json
from graphify.extract import collect_files, extract
from pathlib import Path

code_files = []
detect_path = Path('graphify-out/.graphify_detect.json')
if not detect_path.exists():
    print("Error: detect.json missing")
    sys.exit(1)

detect = json.loads(detect_path.read_text(encoding='utf8'))
for f in detect.get('files', {}).get('code', []):
    p = Path(f)
    if p.is_dir():
        code_files.extend(collect_files(p))
    else:
        code_files.append(p)

if code_files:
    result = extract(code_files, cache_root=Path('.'))
    Path('graphify-out/.graphify_ast.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    print(f"AST: {len(result['nodes'])} nodes, {len(result['edges'])} edges")
else:
    Path('graphify-out/.graphify_ast.json').write_text(json.dumps({'nodes':[],'edges':[],'input_tokens':0,'output_tokens':0}), encoding='utf8')
    print('No code files - skipping AST extraction')
