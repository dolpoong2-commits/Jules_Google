
/******************************************************************************************
 * EASYEDA FULL AUTOMATION SCRIPT (PLACEMENT + ADVANCED WIRING)
 ******************************************************************************************/
(function() {
    console.log("Starting full automation script...");
    const data = {
    "parts": [
        {
            "cnum": "C12345",
            "ref": "R1"
        },
        {
            "cnum": "C10086",
            "ref": "C1"
        },
        {
            "cnum": "C17414",
            "ref": "R2"
        },
        {
            "cnum": "C967822",
            "ref": "U1"
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

    console.log("Placing components...");
    let x = 200, y = 200, i = 0;
    data.parts.forEach(p => {
        api('createShape', {
            shapeType: 'schlib', from: 'LCSC', title: p.cnum,
            gId: `jules_${p.ref}`, x: x + (i % 4) * 250, y: y + Math.floor(i / 4) * 200
        });
        i++;
    });

    setTimeout(() => {
        console.log("Starting wiring process...");
        const allShapes = api('getSource', {type: 'json'});
        const pinCoordsCache = {};

        for (const gId in allShapes.schlib) {
            const component = allShapes.schlib[gId];
            let componentRef = '';
            if(component.head && component.head.annotation){
                for(const annoId in component.head.annotation){
                    if(component.head.annotation[annoId].type === 'prefix'){
                        componentRef = component.head.annotation[annoId].text;
                        break;
                    }
                }
            }
            if (!componentRef || !component.head.pin) continue;
            const cx = parseFloat(component.head.x), cy = parseFloat(component.head.y);
            for (const pinId in component.head.pin) {
                const pin = component.head.pin[pinId];
                pinCoordsCache[`${componentRef}_${pin.number}`] = { x: cx + parseFloat(pin.x), y: cy + parseFloat(pin.y) };
            }
        }

        for (const netName in data.netlist) {
            const connections = data.netlist[netName];
            const isBusNet = connections.length > 2 || ['VCC', 'GND', 'VDD', 'VSS'].some(p => p in netName.toUpperCase());

            if (isBusNet) {
                // For bus nets, create net labels at each pin
                connections.forEach(conn => {
                    const pinKey = `${conn.ref}_${conn.pin}`;
                    const coords = pinCoordsCache[pinKey];
                    if(coords) {
                        api('createShape', {
                            shapeType: 'netlabel',
                            jsonCache: {
                                x: coords.x, y: coords.y,
                                text: netName,
                                color: "#0000FF"
                            }
                        });
                    } else { console.error(`NETLABEL: Could not find coords for ${pinKey}`); }
                });
            } else if (connections.length === 2) {
                // For simple nets, draw a direct wire
                const start = pinCoordsCache[`${connections[0].ref}_${connections[0].pin}`];
                const end = pinCoordsCache[`${connections[1].ref}_${connections[1].pin}`];
                if (start && end) {
                    api('createShape', {
                        shapeType: 'wire',
                        jsonCache: { points: [start, end], stroke: "#0000FF", "stroke-width": "1" }
                    });
                } else { console.error(`WIRE: Could not find coords for net ${netName}`); }
            }
        }
        alert('Full automation script with advanced wiring finished!');
        console.log("Script finished.");
    }, 2000);

})();
