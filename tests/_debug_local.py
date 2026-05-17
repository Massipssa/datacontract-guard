from pathlib import Path
import sys
proj='e:/DEV/devops/docker/dev/tools/data-contract-agent'
if proj not in sys.path:
    sys.path.insert(0,proj)
from contract_agent.adapters.mcp_adapter import LocalMCPAdapter
base = Path(proj)/'tests'/'mocks'/'data'
print('base',base)
print('exists base', base.exists())
la=LocalMCPAdapter(str(base))
print('la.base_dir', la.base_dir)
part='example.yaml'
candidate=Path(la.base_dir)/'contracts'/part
print('candidate',candidate, 'exists', candidate.exists())
if candidate.exists():
    print(candidate.read_text(encoding='utf-8')[:200])
else:
    print('not found')
print('done')
