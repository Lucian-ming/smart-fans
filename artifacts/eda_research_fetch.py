import requests,base64,json,pathlib
out=pathlib.Path('artifacts/eda_gateway_research');out.mkdir(parents=True,exist_ok=True)
for repo in ['easyeda/eext-run-api-gateway','easyeda/easyeda-api-skill','hyl64/jlcmcp']:
 name=repo.replace('/','__'); meta=requests.get('https://api.github.com/repos/'+repo).json(); (out/(name+'_meta.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
 r=requests.get('https://api.github.com/repos/'+repo+'/readme').json()
 text=base64.b64decode(r['content']).decode();(out/(name+'_README.md')).write_text(text,encoding='utf8');print('\nREPO',repo,'\n',text)
 tree=requests.get('https://api.github.com/repos/'+repo+'/git/trees/'+meta.get('default_branch','main')+'?recursive=1').json();(out/(name+'_tree.json')).write_text(json.dumps(tree,ensure_ascii=False,indent=2),encoding='utf8');print('FILES', '\n'.join(x['path'] for x in tree.get('tree',[]) if x['type']=='blob'))
