# -*- coding: utf-8 -*-
"""
JLC 우선/ LCSC 보조 부품 매칭 및 3단계 자동화 스크립트 생성 파이프라인 (V6 - 인터랙티브 검색 지원 모듈)
"""
import os, re, csv, math, json, time, argparse, random, hashlib, string
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import requests
from slugify import slugify

# LCSC API 키 설정 (사용자 입력)
LCSC_API_KEY = ""
LCSC_API_SECRET = ""

# --- 데이터 모델 (변경 없음) ---
@dataclass
class PartRow:
    Designator: str; Qty: str; MPN: str; Value: str; Package: str; Footprint: str
    Voltage: str = ''; Power: str = ''; Tolerance: str = ''; Notes: str = ''
@dataclass
class Candidate:
    supplier: str; supplier_part: str; mpn: str; pkg: str; value: str; stock: int
    price: Optional[float] = None; maker: Optional[str] = ''; desc: Optional[str] = ''
@dataclass
class Net:
    pins: List[Dict[str, str]] = field(default_factory=list)

# --- 어댑터 (변경 없음) ---
class BaseAdapter:
    def __init__(self, supplier_name: str): self.supplier_name = supplier_name
    def search(self, query: str) -> List[Candidate]: raise NotImplementedError
class MockAdapter(BaseAdapter):
    def __init__(self, supplier_name: str, mock_csv: Optional[str] = None):
        super().__init__(supplier_name)
        self.mock_csv = mock_csv
    def search(self, query: str) -> List[Candidate]:
        if not self.mock_csv or not os.path.exists(self.mock_csv): return []
        df = pd.read_csv(self.mock_csv)
        query_parts = query.split()
        hits = []
        for _, r in df.iterrows():
            key_data = [str(r.get(k,'')) for k in ['mpn', 'value', 'pkg', 'supplier_part']]
            key = re.sub(r'[^A-Za-z0-9.+-]', '', "".join(key_data)).upper()
            if all(re.sub(r'[^A-Za-z0-9.+-]', '', k).upper() in key for k in query_parts):
                hits.append(Candidate(self.supplier_name, str(r.get('supplier_part','')), str(r.get('mpn','')), str(r.get('pkg','')), str(r.get('value','')), int(r.get('stock',0)), float(r.get('price',0) or 0.0), str(r.get('maker','')), str(r.get('desc',''))))
        return hits
class LCSCRealAdapter(BaseAdapter):
    BASE_URL = "https://api.lcsc.com/v2"
    def __init__(self, api_key: str, api_secret: str):
        super().__init__("LCSC")
        self.api_key, self.api_secret = api_key, api_secret
    def search(self, query: str) -> List[Candidate]:
        endpoint, timestamp, nonce = f"{self.BASE_URL}/products/search", str(int(time.time())), ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
        sign_str = f"key={self.api_key}&nonce={nonce}&secret={self.api_secret}&timestamp={timestamp}"
        signature = hashlib.sha1(sign_str.encode('utf-8')).hexdigest()
        try:
            r = requests.post(endpoint, headers={'Content-Type': 'application/json'}, json={"keyword": query, "key": self.api_key, "nonce": nonce, "timestamp": timestamp, "signature": signature})
            r.raise_for_status()
            data = r.json()
            if data.get("success") and data.get("result"):
                return [Candidate("LCSC", i.get('lcsc_part_number', ''), i.get('mpn', ''), i.get('package', ''), i.get('number', ''), i.get('stock', 0), (i.get('price_list', [{}])[0] or {}).get('price'), i.get('brand', ''), i.get('description', '')) for i in data["result"].get("list", [])]
            else: print(f"LCSC API Error: {data.get('message', 'Unknown error')}"); return []
        except requests.exceptions.RequestException as e: print(f"LCSC API Request Failed: {e}"); return []

# --- 매칭 및 파싱 로직 (변경 없음) ---
def parse_value(s: str) -> str: return (s or '').strip().upper().replace('OHM','Ω').replace('R','Ω').replace('UF','µF').replace('U','µ').replace('NF','nF').replace('PF','pF').replace(' ','')
def make_query(row: PartRow) -> str:
    if row.MPN: return re.sub(r'[^A-Za-z0-9.+-]', '', row.MPN).upper()
    return " ".join([parse_value(row.Value), re.sub(r'[^A-Za-z0-9.+-]', '', row.Package or row.Footprint).upper()]).strip()
def score(csv_part: PartRow, cand: Candidate, prefer_jlc=True) -> float:
    s = 0.0; norm_re = r'[^A-Za-z0-9.+-]'
    if cand.stock > 0: s += 5.0
    if prefer_jlc and cand.supplier == "JLC": s += 1.0
    if csv_part.MPN and re.sub(norm_re, '', csv_part.MPN).upper() == re.sub(norm_re, '', cand.mpn).upper(): s += 4.0
    pkg_csv = re.sub(norm_re, '', csv_part.Package or csv_part.Footprint).upper()
    pkg_api = re.sub(norm_re, '', cand.pkg).upper()
    if pkg_csv and pkg_api and (pkg_csv == pkg_api or pkg_csv in pkg_api or pkg_api in pkg_csv): s += 3.0
    v_csv = re.sub(norm_re, '', parse_value(csv_part.Value)).upper()
    v_api = re.sub(norm_re, '', parse_value(cand.value)).upper()
    if v_csv and v_api and v_csv == v_api: s += 1.5
    return s
def pick_best(csv_part: PartRow, cands: List[Candidate], prefer_jlc=True) -> Optional[Candidate]:
    if not cands: return None
    scored_cands = sorted([(c, score(csv_part, c, prefer_jlc)) for c in cands], key=lambda x: x[1], reverse=True)
    return scored_cands[0][0] if scored_cands and scored_cands[0][1] > 0 else None
def load_input_csv(path: str) -> List[PartRow]: return [PartRow(**r) for _, r in pd.read_csv(path).fillna('').iterrows()]
def load_netlist_data(path: str) -> Dict[str, Net]:
    nets = {};
    with open(path, mode='r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            net_name = row['NetName']
            if net_name not in nets: nets[net_name] = Net()
            nets[net_name].pins.append({'ref': row['PartReference'], 'pin': row['PinNumber']})
    return nets

# ==============================================================================
#  새로운 독립 검색 함수 (GUI에서 호출용)
# ==============================================================================
def search_jlc(query: str) -> List[Candidate]:
    """Searches for parts using the JLC mock adapter."""
    adapter = MockAdapter("JLC", "jlc_inventory.csv")
    return adapter.search(query)

def search_lcsc(query: str) -> List[Candidate]:
    """Searches for parts using the LCSC real or mock adapter."""
    if LCSC_API_KEY and LCSC_API_SECRET:
        adapter = LCSCRealAdapter(LCSC_API_KEY, LCSC_API_SECRET)
    else:
        adapter = MockAdapter("LCSC", "lcsc_inventory.csv")
    return adapter.search(query)
# ==============================================================================

# --- 파이프라인 함수들 ---
def execute_design_pipeline(parts_data: List[Dict[str, str]], netlist_data: List[Dict[str, str]]) -> Tuple[str, str]:
    inputs = [PartRow(**p) for p in parts_data]
    nets = {}
    for row in netlist_data:
        net_name = row['NetName']
        if net_name not in nets: nets[net_name] = Net()
        nets[net_name].pins.append({'ref': row['PartReference'], 'pin': row['PinNumber']})

    jlc, lcsc = MockAdapter("JLC", "jlc_inventory.csv"), LCSCRealAdapter(LCSC_API_KEY, LCSC_API_SECRET) if LCSC_API_KEY and LCSC_API_SECRET else MockAdapter("LCSC", "lcsc_inventory.csv")

    parts_to_place = []
    for row in inputs:
        best = pick_best(row, jlc.search(make_query(row)) or lcsc.search(make_query(row)))
        if best:
            sp = f"C{best.supplier_part}" if best.supplier == "LCSC" and not str(best.supplier_part).upper().startswith('C') else best.supplier_part
            parts_to_place.append({"cnum": sp, "ref": row.Designator, "footprint": row.Footprint})

    sch_data = {"parts": parts_to_place, "netlist": {name: net.pins for name, net in nets.items()}}
    sch_template = f"""/* 1. SCHEMATIC SCRIPT */
(function() {{
    const data = {json.dumps(sch_data, indent=2)};
    let x=200, y=200, i=0;
    data.parts.forEach(p => {{ api('createShape', {{shapeType: 'schlib', from: 'LCSC', title: p.cnum, gId: `jules_${{p.ref}}`, x: x + (i++ % 4)*250, y: y + Math.floor(i/4)*200}}); }});
    setTimeout(() => {{
        const shapes = api('getSource', {{type: 'json'}});
        const pins = {{}};
        for (const gId in shapes.schlib) {{
            const c = shapes.schlib[gId];
            let ref = (c.head?.annotation?.find(a => a.type === 'prefix') || {{}}).text;
            if (ref && c.head.pin) {{
                for (const pId in c.head.pin) {{ const p = c.head.pin[pId]; pins[`${{ref}}_${{p.number}}`] = {{x: parseFloat(c.head.x) + parseFloat(p.x), y: parseFloat(c.head.y) + parseFloat(p.y)}}; }}
            }}
        }}
        for (const netName in data.netlist) {{
            const conns = data.netlist[netName];
            const isBus = conns.length > 2 || ['VCC', 'GND', 'VDD', 'VSS'].some(p => p in netName.toUpperCase());
            if (isBus) {{ conns.forEach(c => {{ const k = `${{c.ref}}_${{c.pin}}`; if(pins[k]) api('createShape', {{shapeType:'netlabel', jsonCache:{{x:pins[k].x, y:pins[k].y, text:netName, color:"#0000FF"}}}}); }});
            }} else if (conns.length === 2) {{
                const s = pins[`${{conns[0].ref}}_${{conns[0].pin}}`], e = pins[`${{conns[1].ref}}_${{conns[1].pin}}`];
                if (s && e) api('createShape', {{shapeType:'wire', jsonCache:{{points:[s,e], stroke:"#0000FF", "stroke-width":"1"}}}});
            }}
        }}
        alert('Schematic script finished!');
    }}, 2000);
}})();"""
    pcb_template = f"""/* 2. PCB PLACEMENT SCRIPT */
(function() {{
    const pcbJson = api('getSource', {{type: 'json'}});
    if (!pcbJson.FOOTPRINT) {{ alert("No footprints found. Did you 'Update PCB from Schematic' first?"); return; }}
    const footprints = Object.values(pcbJson.FOOTPRINT);
    let x = 1000, y = 1000, i = 0;
    footprints.forEach(fp => {{
        api('updateShape', {{"shapeType": "FOOTPRINT", "jsonCache": {{ "gId": fp.gId, "x": x + (i % 5) * 400, "y": y + Math.floor(i / 5) * 400, "rotation": 0 }}}});
        i++;
    }});
    alert(`Placement of ${{footprints.length}} footprints finished!`);
}})();"""
    return sch_template, pcb_template

def generate_manufacturing_script() -> str:
    return f"""/* 3. MANUFACTURING FILE GENERATION SCRIPT */
(function() {{
    if (typeof api('getManufactureData') === 'undefined') {{ alert('This feature requires EasyEDA Pro.'); return; }}
    const mfg = api('getManufactureData');
    try {{ mfg.getGerberFile('Gerber_AutoGenerated'); }} catch(e) {{ console.error("Gerber generation failed:", e); }}
    try {{ mfg.getBomFile('BOM_AutoGenerated', 'csv'); }} catch(e) {{ console.error("BOM generation failed:", e); }}
    alert("Manufacturing file generation commands sent. Check browser for downloads.");
}})();"""

# --- 커맨드라인 실행 부분 (변경 없음) ---
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="EasyEDA Automation Pipeline")
    ap.add_argument("command", choices=['design', 'mfg'], help="Command to execute: 'design' or 'mfg'")
    ap.add_argument("--parts_csv", default="input_parts.csv")
    ap.add_argument("--netlist_csv", default="netlist_data.csv")
    ap.add_argument("--out-sch", default="01_create_schematic.js")
    ap.add_argument("--out-pcb", default="02_place_footprints.js")
    ap.add_argument("--out-mfg", default="03_generate_manufacturing_files.js")
    args = ap.parse_args()
    if args.command == 'design':
        parts_data = [row for row in csv.DictReader(open(args.parts_csv, 'r', encoding='utf-8'))]
        netlist_data = [row for row in csv.DictReader(open(args.netlist_csv, 'r', encoding='utf-8'))]
        sch_script, pcb_script = execute_design_pipeline(parts_data, netlist_data)
        with open(args.out_sch, 'w', encoding='utf-8') as f: f.write(sch_script)
        with open(args.out_pcb, 'w', encoding='utf-8') as f: f.write(pcb_script)
    elif args.command == 'mfg':
        with open(args.out_mfg, 'w', encoding='utf-8') as f: f.write(generate_manufacturing_script())