# admin panel map builder canvas

**Sumber:** claude-code  
**Tanggal:** 2026-04-16  
**Tags:** admin-panel, canvas-2d, map-builder, world-json, buildings, sprint-9G  

## Konteks

Bagaimana membuat Map Builder visual 2D di admin panel untuk memvisualisasikan layout buildings dari config/world.json?

## Pengetahuan

Pattern di admin-panel/index.html Sprint 9G Map Builder tab: (1) Load data dari `GET /api/world` yang return full world.json; (2) Canvas 2D plot: ambil `buildings[k].position.{x,z}`, normalize ke canvas koordinat dengan pad+range formula — `toCanvasX(wx) = pad + ((wx-minX)/rangeX)*(W-pad*2)`; (3) Background grid: lines tiap 1/10 range dengan axis labels; (4) Origin crosshair: dashed line di x=0, z=0; (5) Building card: rounded rect (ctx.roundRect fallback ke ctx.rect), shadow, fill+stroke dengan per-building color, dot at center, label name + floors info; (6) Hitboxes array untuk hover/click detection: `{x1,y1,x2,y2,data,col}` — check `mx >= hb.x1 && mx <= hb.x2 && my >= hb.y1 && my <= hb.y2`; (7) Hover tooltip: `position:fixed` div, CSS `pointer-events:none`, update style.left/top dari `e.clientX/e.clientY`; (8) Click → `showBuildingRooms(buildingId)`: filter rooms where `building.floors.indexOf(room.floor) >= 0`, group by floor, render grid cards; (9) Floor filter dropdown: populated from unique `room.floor` values; (10) KPI row: buildings count, rooms count, total agents in rooms, distinct floors count.

---
*Diambil dari SIDIX MCP Knowledge Base*
