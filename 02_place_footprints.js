/* 2. PCB FOOTPRINT PLACEMENT SCRIPT */
(function() {
    console.log("Arranging footprints on PCB...");
    const pcbJson = api('getSource', {type: 'json'});
    if (!pcbJson.FOOTPRINT) { alert("No footprints found. Did you 'Update PCB from Schematic' first?"); return; }

    const footprints = Object.values(pcbJson.FOOTPRINT);
    console.log(`Found ${footprints.length} footprints to arrange.`);

    let x = 1000, y = 1000, i = 0;
    const spacing = 400; // 400 pixels = 10.16mm

    footprints.forEach(fp => {
        const newX = x + (i % 5) * spacing;
        const newY = y + Math.floor(i / 5) * spacing;

        api('updateShape', {
            "shapeType": "FOOTPRINT",
            "jsonCache": { "gId": fp.gId, "x": newX, "y": newY, "rotation": 0 }
        });
        i++;
    });

    alert(`Placement of ${footprints.length} footprints finished!`);
})();