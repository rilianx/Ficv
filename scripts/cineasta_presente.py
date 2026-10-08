#!/usr/bin/env python3
"""Detecta en el PDF del Programa oficial las funciones con el símbolo "Cineasta Presente".
Uso: python scripts/cineasta_presente.py fuentes/PROGRAMA-...pdf datos.json salida.json"""
import fitz, re, json, sys, unicodedata
doc=fitz.open(sys.argv[1]); datos=json.load(open(sys.argv[2]))
norm=lambda s:re.sub(r'[^a-z0-9 ]','',unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode().lower())
p0=doc[2]; lab=p0.search_for("Cineasta Presente")[0]
cab=[d for d in p0.get_drawings() if d['rect'].x1<=lab.x0+2 and d['rect'].x0>lab.x0-30 and len(d['items'])==22][0]
firma=[i[0] for i in cab['items']]
DIAS={"LUNES":12,"MARTES":13,"MIÉRCOLES":14,"MIERCOLES":14,"JUEVES":15,"VIERNES":16,"SÁBADO":17,"SABADO":17,"DOMINGO":18}
res=[]; problemas=[]
for pi,pg in enumerate(doc):
    t=pg.get_text()
    m=re.search(r'(LUNES|MARTES|MI[ÉE]RCOLES|JUEVES|VIERNES|S[ÁA]BADO|DOMINGO)\s*(1[2-8])',t)
    if not m: continue
    dia=f"2026-10-{int(m.group(2)):02d}"
    W=pg.get_text("words")
    nums=[w for w in W if re.fullmatch(r'\d/\d',w[4])]
    horas=[w for w in W if re.fullmatch(r'\d{1,2}:\d{2}',w[4])]
    for d in pg.get_drawings():
        if [i[0] for i in d['items']]!=firma: continue
        r=d['rect']
        if r.y1<100 and r.x0>pg.rect.width*0.85: continue          # leyenda
        cx,cy=(r.x0+r.x1)/2,(r.y0+r.y1)/2
        cand=[n for n in nums if abs((n[0]+n[2])/2-cx)<8 and 0<cy-n[3]<16]
        if not cand: problemas.append((dia,'sin número',round(cx),round(cy))); continue
        n=min(cand,key=lambda n:cy-n[3]); ny=(n[1]+n[3])/2
        hs=[h for h in horas if abs((h[1]+h[3])/2-ny)<4 and h[2]<n[0]]
        if not hs: problemas.append((dia,'sin hora',round(cx),round(cy))); continue
        h=max(hs,key=lambda h:h[0])
        tit=" ".join(w[4] for w in sorted([w for w in W if h[3]<w[1]<h[3]+14 and h[0]-30<w[0]<n[2]],key=lambda w:(round(w[1]),w[0])))
        hora=h[4].zfill(5)
        cands=[f for f in datos if f['dia']==dia and f['hora']==hora]
        # elegir por parecido de título (o sesión)
        def score(f):
            a=norm(tit); b=norm(f['titulo'])+" "+norm(f.get('sesion',''))
            return sum(1 for x in a.split() if len(x)>2 and x in b)
        best=max(cands,key=score) if cands else None
        res.append({"dia":dia,"hora":hora,"pdf":tit[:70],"id":best['id'] if best and score(best)>0 else None,
                    "titulo":best['titulo'] if best else None,"sala":best['sala'] if best else None,"score":score(best) if best else 0})
json.dump({"res":res,"problemas":problemas},open(sys.argv[3],'w'),ensure_ascii=False,indent=1)
print(len(res),'asignados,',len(problemas),'problemas')
for r in sorted(res,key=lambda r:(r['dia'],r['hora'])): print(r['dia'][8:],r['hora'],'|',r['pdf'][:45],'→',r['titulo'],'|',r['sala'],r['score'])
for p in problemas: print('PROBLEMA',p)
