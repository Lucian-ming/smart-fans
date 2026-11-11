import requests,pathlib,json,hashlib,zipfile,io
root=pathlib.Path('tools/eda_gateway');root.mkdir(parents=True,exist_ok=True)
repo='easyeda/eext-run-api-gateway'; rel=requests.get('https://api.github.com/repos/'+repo+'/releases').json()[0]
(root/'release_metadata.json').write_text(json.dumps(rel,ensure_ascii=False,indent=2),encoding='utf8')
asset=next(a for a in rel['assets'] if 'zh-cn' in a['name']); r=requests.get(asset['browser_download_url']);r.raise_for_status(); data=r.content
assert 'sha256:'+hashlib.sha256(data).hexdigest()==asset['digest']; target=root/asset['name'];target.write_bytes(data);print('ASSET',target.resolve(),len(data),asset['digest'])
with zipfile.ZipFile(io.BytesIO(data)) as z:
 print('EXTENSION_FILES',z.namelist());print(z.read('extension.json').decode())
commit='8aa6c74b99bdfcbc9f8900e9cec07f1c70cfff14'
r=requests.get('https://api.github.com/repos/easyeda/easyeda-api-skill/zipball/'+commit);r.raise_for_status();data=r.content
(root/'easyeda-api-skill-pinned.zip').write_bytes(data)
dest=root/'easyeda-api-skill'
with zipfile.ZipFile(io.BytesIO(data)) as z:
 for info in z.infolist():
  parts=pathlib.PurePosixPath(info.filename).parts[1:]
  if not parts or info.is_dir():continue
  assert '..' not in parts
  p=dest.joinpath(*parts);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(info))
print('SKILL',dest.resolve(),'ZIP_SHA256',hashlib.sha256(data).hexdigest());print((dest/'package.json').read_text());print((dest/'package-lock.json').read_text()[:14000])
