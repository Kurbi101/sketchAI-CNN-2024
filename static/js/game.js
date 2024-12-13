function stopDrawing() {
    if (!isDrawing) return;
    isDrawing = false;
    context.beginPath();
}

function draw(e) {
    if (!isDrawing) return;
    const rect = canvas.getBoundingClientRect();

    context.lineWidth = brushWidth;
    context.lineCap = "round";
    context.strokeStyle = useEraser ? "#FFFFFF" : "#000000";

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    context.lineTo(x, y);
    context.stroke();
    context.beginPath();
    context.moveTo(x, y);
}

function stopDrawing() {
    if (!isDrawing) return;
    isDrawing = false;
    context.beginPath();
}
function toggleEraserState() {
    useEraser = !useEraser;
}
function getMousePos(canvas, evt) {
    var rect = canvas.getBoundingClientRect();
    return {
        x: evt.clientX - rect.left,
        y: evt.clientY - rect.top
    };
}
function drawLine(ctx, x, y) {
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x, y);
}