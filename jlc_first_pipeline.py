# -*- coding: utf-8 -*-
"""
JLC 우선/ LCSC 보조 부품 매칭 및 배선 자동화 파이프라인
- 입력 CSV 1: input_parts.csv (부품 목록)
- 입력 CSV 2: netlist_data.csv (연결 정보)
- 출력:
  ... (기존 CSV 파일들)
  easyeda_full_script.js (배치 및 배선 통합 스크립트)
"""
import os, re, csv, math, json, time, argparse, random
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from slugify import slugify

# -----------------------------
# 데이터 모델
# -----------------------------
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

# -----------------------------
# 어댑터
# -----------------------------
class BaseAdapter:
    def __init__(self, supplier_name: str, mock_csv: Optional[str] = None):
        self.supplier_name = supplier_name
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

class JLCAdapter(BaseAdapter):
    def __init__(self, mock_csv: Optional[str] = None): super().__init__("JLC", mock_csv)

class LCSCAdapter(BaseAdapter):
    def __init__(self, mock_csv: Optional[str] = None): super().__init__("LCSC", mock_csv)

# -----------------------------
# 매칭 및 파싱 로직
# -----------------------------
def parse_value(s: str) -> str:
    return (s or '').strip().upper().replace('OHM','Ω').replace('R','Ω').replace('UF','µF').replace('U','µ').replace('NF','nF').replace('PF','pF').replace(' ','')

def make_query(row: PartRow) -> str:
    if row.MPN: return re.sub(r'[^A-Za-z0-9.+-]', '', row.MPN).upper()
    v = parse_value(row.Value)
    pkg = re.sub(r'[^A-Za-z0-9.+-]', '', row.Package or row.Footprint).upper()
    return " ".join([v, pkg]).strip()

def score(csv_part: PartRow, cand: Candidate, prefer_jlc=True, permissive=False) -> float:
    s = 0.0
    norm_re = r'[^A-Za-z0-9.+-]'
    if cand.stock > 0: s += 5.0
    if prefer_jlc and cand.supplier == "JLC": s += 1.0
    if csv_part.MPN and re.sub(norm_re, '', csv_part.MPN).upper() == re.sub(norm_re, '', cand.mpn).upper(): s += 4.0
    pkg_csv = re.sub(norm_re, '', csv_part.Package or csv_part.Footprint).upper()
    pkg_api = re.sub(norm_re, '', cand.pkg).upper()
    if pkg_csv and pkg_api:
        if pkg_csv == pkg_api: s += 3.0
        elif pkg_csv in pkg_api or pkg_api in pkg_csv: s += 1.5
    v_csv = re.sub(norm_re, '', parse_value(csv_part.Value)).upper()
    v_api = re.sub(norm_re, '', parse_value(cand.value)).upper()
    if v_csv and v_api and v_csv == v_api: s += 1.5
    return s

def pick_best(csv_part: PartRow, cands: List[Candidate], prefer_jlc=True, permissive=False) -> Tuple[Optional[Candidate], float, List[Candidate]]:
    if not cands: return None, -1.0, []
    scored_cands = sorted([(c, score(csv_part, c, prefer_jlc, permissive)) for c in cands], key=lambda x: x[1], reverse=True)
    best_cand, best_s = scored_cands[0]
    return best_cand, best_s, [c for c, s in scored_cands[:3]]

def load_input_csv(path: str) -> List[PartRow]:
    return [PartRow(**r) for _, r in pd.read_csv(path).fillna('').iterrows()]

def load_netlist_data(path: str) -> Dict[str, Net]:
    nets = {}
    with open(path, mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            net_name = row['NetName']
            if net_name not in nets:
                nets[net_name] = Net()
            nets[net_name].pins.append({'ref': row['PartReference'], 'pin': row['PinNumber']})
    return nets

# -----------------------------
# 파이프라인
# -----------------------------
def run_pipeline(parts_csv: str, netlist_csv: str, jlc_mock: str, lcsc_mock: str, out_js: str):
    jlc, lcsc, inputs, nets = JLCAdapter(jlc_mock), LCSCAdapter(lcsc_mock), load_input_csv(parts_csv), load_netlist_data(netlist_csv)

    parts_to_place = []
    for row in inputs:
        query = make_query(row)
        cands = jlc.search(query) or lcsc.search(query)
        best, score_best, _ = pick_best(row, cands)
        if best and score_best > 0:
            sp = f"C{best.supplier_part}" if best.supplier == "LCSC" and not str(best.supplier_part).upper().startswith('C') else best.supplier_part
            parts_to_place.append({
                "cnum": sp,
                "ref": slugify(row.Designator, separator="_").upper()
            })

    # --- Generate JavaScript ---
    js_data = {
        "parts": parts_to_place,
        "netlist": {name: net.pins for name, net in nets.items() if len(net.pins) > 1}
    }

    js_template = f"""
/******************************************************************************************
 * EASYEDA FULL AUTOMATION SCRIPT (PLACEMENT + WIRING)
 * Generated by Jules' Python Pipeline
 ******************************************************************************************/
(function() {{
    console.log("Starting full automation script...");
    const data = {json.dumps(js_data, indent=4)};
    const componentGIds = {{}}; // Map for ref -> gId

    // 1. Place all components
    console.log("Placing components...");
    let x = 200, y = 200, i = 0;
    data.parts.forEach(p => {{
        const gId = `jules_${{p.ref}}_${{new Date().getTime()}}`; // Ensure unique gId
        componentGIds[p.ref] = gId;
        api('createShape', {{
            shapeType: 'schlib', from: 'LCSC', title: p.cnum,
            gId: gId, x: x + (i % 4) * 250, y: y + Math.floor(i / 4) * 200
        }});
        i++;
    }});

    // Delay to allow UI to update with placed components
    setTimeout(() => {{
        console.log("Starting wiring process...");
        const allShapes = api('getSource', {{type: 'json'}});
        const pinCoordsCache = {{}}; // Cache for pin coordinates: 'U1_1': {{x: 123, y: 456}}

        // Pre-process and cache all pin coordinates
        for (const gId in allShapes.schlib) {{
            const component = allShapes.schlib[gId];
            const componentRef = component.head?.annotation?.find(a => a.type === 'prefix')?.text;
            if (!componentRef || !component.head.pin) continue;

            const cx = parseFloat(component.head.x);
            const cy = parseFloat(component.head.y);

            for (const pinId in component.head.pin) {{
                const pin = component.head.pin[pinId];
                const pinKey = `${{componentRef}}_${{pin.number}}`;
                pinCoordsCache[pinKey] = {{ x: cx + parseFloat(pin.x), y: cy + parseFloat(pin.y) }};
            }}
        }}

        // 2. Draw wires for all nets
        for (const netName in data.netlist) {{
            const connections = data.netlist[netName];
            const points = [];
            connections.forEach(conn => {{
                const pinKey = `${{conn.ref}}_${{conn.pin}}`;
                if (pinCoordsCache[pinKey]) {{
                    points.push(pinCoordsCache[pinKey]);
                }} else {{
                    console.error(`Could not find coordinates for pin: ${{pinKey}}`);
                }}
            }});

            if (points.length < 2) continue;

            // Simple daisy-chain wiring
            for (let i = 0; i < points.length - 1; i++) {{
                const start = points[i];
                const end = points[i + 1];
                api('createShape', {{
                    shapeType: 'wire',
                    jsonCache: {{
                        points: [{{x: start.x, y: start.y}}, {{x: end.x, y: end.y}}],
                        stroke: "#0000FF", "stroke-width": "1"
                    }}
                }});
            }}
        }}
        alert('Full automation script finished!');
        console.log("Script finished.");
    }}, 2000); // Increased delay for stability

}})();
"""
    with open(out_js, 'w', encoding='utf-8') as f:
        f.write(js_template)
    print(f"[OK] Generated full automation script: {out_js}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("parts_csv", help="입력 부품 목록 CSV")
    ap.add_argument("netlist_csv", help="입력 넷리스트 CSV")
    ap.add_argument("--jlc-mock", default="jlc_inventory.csv")
    ap.add_argument("--lcsc-mock", default="lcsc_inventory.csv")
    ap.add_argument("--out-js", default="easyeda_full_script.js")
    args = ap.parse_args()
    run_pipeline(args.parts_csv, args.netlist_csv, args.jlc_mock, args.lcsc_mock, args.out_js)