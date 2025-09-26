(function(){
  const parts = [
    { cnum: 'C12345', x:200, y:200, ref:'R1'},
    { cnum: 'C10086', x:400, y:200, ref:'C1'},
    { cnum: 'C17414', x:600, y:200, ref:'R2'},
    { cnum: 'C967822', x:800, y:200, ref:'U1'},
  ];
  parts.forEach(p=>{ api('createShape', { shapeType: 'schlib', from: 'LCSC', title: p.cnum, x: p.x, y: p.y, gId: p.ref }); });
  alert('Placement draft done: ' + parts.length + ' parts.');
})();