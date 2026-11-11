import requests,base64,pathlib,concurrent.futures
out=pathlib.Path('artifacts/eda_gateway_research')
files={'easyeda/eext-run-api-gateway':['extension.json','package.json','src/index.ts','CHANGELOG.md'],'easyeda/easyeda-api-skill':['package.json','scripts/bridge-server.mjs','references/classes/PCB_Drc.md','references/classes/SCH_Drc.md','references/classes/SCH_SimulationEngine.md','references/enums/ESCH_SpiceSimulationEnginePullEventType.md','references/enums/ESCH_SpiceSimulationEnginePushEventType.md','references/classes/SCH_ManufactureData.md'],'hyl64/jlcmcp':['package.json','scripts/bridge-server.mjs','src/gateway-client.ts','src/codegen/generated.ts','src/codegen.ts','src/tools/state.ts','src/tools/schematic.ts','src/tools/pro.ts','src/agent.ts']}
def fetch(a):
 repo,p=a;r=requests.get('https://api.github.com/repos/'+repo+'/contents/'+p).json()
 if 'content' not in r:return str(r)
 dest=out/(repo.replace('/','__')+'__'+p.replace('/','__'));dest.write_bytes(base64.b64decode(r['content']));return str(dest)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
 for v in ex.map(fetch,[(r,p) for r,ps in files.items() for p in ps]):print(v)
