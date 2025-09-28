/* 1. SCHEMATIC AUTOMATION SCRIPT */
(function() {
    console.log("Placing components...");
    const data = {
    "parts": [
        {
            "cnum": "C12345",
            "ref": "R1",
            "footprint": "0805"
        },
        {
            "cnum": "C10086",
            "ref": "C1",
            "footprint": "0805"
        },
        {
            "cnum": "C17414",
            "ref": "R2",
            "footprint": "0603"
        },
        {
            "cnum": "C967822",
            "ref": "U1",
            "footprint": "ESP32-WROOM-32_FG"
        }
    ],
    "netlist": {
        "NET_VCC": [
            {
                "ref": "U1",
                "pin": "3V3"
            },
            {
                "ref": "C1",
                "pin": "1"
            }
        ],
        "NET_GND": [
            {
                "ref": "U1",
                "pin": "GND"
            },
            {
                "ref": "C1",
                "pin": "2"
            }
        ],
        "NET_LED_CTRL": [
            {
                "ref": "U1",
                "pin": "GPIO22"
            },
            {
                "ref": "R1",
                "pin": "1"
            }
        ],
        "NET_TO_R2": [
            {
                "ref": "R1",
                "pin": "2"
            },
            {
                "ref": "R2",
                "pin": "1"
            }
        ]
    }
};
    let x=200, y=200, i=0;
    data.parts.forEach(p => {
        api('createShape', {shapeType: 'schlib', from: 'LCSC', title: p.cnum, gId: `jules_${p.ref}`, x: x + (i++ % 4)*250, y: y + Math.floor(i/4)*200});
    });
    setTimeout(() => {
        console.log("Wiring...");
        const shapes = api('getSource', {type: 'json'});
        const pins = {};
        for (const gId in shapes.schlib) {
            const c = shapes.schlib[gId];
            let ref = (c.head?.annotation?.find(a => a.type === 'prefix') || {}).text;
            if (ref && c.head.pin) {
                for (const pId in c.head.pin) {
                    const p = c.head.pin[pId];
                    pins[`${ref}_${p.number}`] = {x: parseFloat(c.head.x) + parseFloat(p.x), y: parseFloat(c.head.y) + parseFloat(p.y)};
                }
            }
        }
        for (const netName in data.netlist) {
            const conns = data.netlist[netName];
            const isBus = conns.length > 2 || ['VCC', 'GND', 'VDD', 'VSS'].some(p => p in netName.toUpperCase());
            if (isBus) {
                conns.forEach(c => {
                    const k = `${c.ref}_${c.pin}`;
                    if(pins[k]) api('createShape', {shapeType:'netlabel', jsonCache:{x:pins[k].x, y:pins[k].y, text:netName, color:"#0000FF"}});
                });
            } else if (conns.length === 2) {
                const s = pins[`${conns[0].ref}_${conns[0].pin}`], e = pins[`${conns[1].ref}_${conns[1].pin}`];
                if (s && e) api('createShape', {shapeType:'wire', jsonCache:{points:[s,e], stroke:"#0000FF", "stroke-width":"1"}});
            }
        }
        alert('Schematic script finished!');
    }, 2000);
})();