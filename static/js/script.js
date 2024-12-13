document.addEventListener("DOMContentLoaded", function() {
    const brushWidth = 7; 

    const canvas = document.getElementById("drawingCanvas");
    const context = canvas.getContext("2d");
    const eraserButton = document.getElementById("eraserButton");
    const deleteButton = document.getElementById("deleteButton");
    const createjpgButton = document.getElementById("createjpgButton");

    let isDrawing = false;
    let useEraser = false;
    let drawingStack = [];
    let currentStroke = [];
    let allStrokes = [];
    
    context.fillStyle = 'white'; 
    context.fillRect(0, 0, canvas.width, canvas.height);

    function stopDrawing() {
        if (!isDrawing) return;
        isDrawing = false;
        context.beginPath();
        saveCanvasState();
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

    function toggleEraserState() {
        useEraser = !useEraser;
    }

    function saveCanvasState() {
        const canvasState = context.getImageData(0, 0, canvas.width, canvas.height);
        drawingStack.push(canvasState);
    }

    function undo() {
        if (allStrokes.length > 0) {
            allStrokes.pop();
            restoreCanvasState();
        }
    }

    function restoreCanvasState() {
        context.clearRect(0, 0, canvas.width, canvas.height); 
        context.fillStyle = 'white';
        context.fillRect(0, 0, canvas.width, canvas.height); 
    
        allStrokes.forEach(stroke => {
            context.beginPath();
            stroke.forEach((point, index) => {
                const [x, y] = point;
                if (index === 0) {
                    context.moveTo(x, y);
                } else {
                    context.lineTo(x, y);
                }
            });
            context.stroke(); 
        });
    }

    createjpgButton.onclick = function sendVectorDataForPrediction() {
        if (allStrokes.length === 0) {
            alert('Please draw something before predicting.');
            return;
        }
        console.log('allStrokes: ', allStrokes)
        console.log('json: ', JSON.stringify({ strokes: allStrokes }))
        try {
            fetch('http://localhost:5000/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ strokes: allStrokes })
            })
            .then(response => response.json())
            .then(data => {
                const predictedClass = data.prediction;
                console.log('Prediction:', data);
                document.getElementById('predictionResult').textContent = 'Predicted class: ' + predictedClass;
                document.getElementById('confidenceResult').textContent = 'Confidence: ' + data.confidence.toFixed(2) + '%';
                resultImage.setAttribute('src', "data:image/png;base64," + data.resultImage);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        } catch (error) {
            console.error('Error:', error);
        }
    };

    canvas.addEventListener("mouseup", stopDrawing);
    canvas.addEventListener("mousemove", draw);
    canvas.addEventListener("mouseout", stopDrawing);

    eraserButton.addEventListener("click", function() {
        toggleEraserState();
        eraserButton.textContent = useEraser ? "Disable Eraser" : "Enable Eraser";
    });

    deleteButton.addEventListener("click", function() {
        allStrokes = [];
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.fillStyle = 'white';
        context.fillRect(0, 0, canvas.width, canvas.height);
    });

    document.addEventListener("keydown", function(e) {
        if (e.key === "Shift") {
            toggleEraserState();
        }
        if (e.ctrlKey && e.key === "z") {
            undo();
        }
    });

    document.addEventListener("keyup", function(e) {
        if (e.key === "Shift") {
            toggleEraserState();
        }
    });

    canvas.addEventListener('mousedown', function(e) {
        isDrawing = true;
        currentStroke = [];
        const point = getMousePos(canvas, e);
        currentStroke.push([Math.round(point.x),Math.round(point.y)]);
    });

    canvas.addEventListener('mousemove', function(e) {
        if (!isDrawing) return;
        const point = getMousePos(canvas, e);
        currentStroke.push([Math.round(point.x), Math.round(point.y)]);
        drawLine(context, point.x, point.y);
    });

    canvas.addEventListener('mouseup', function() {
        if (currentStroke.length > 0) {
            allStrokes.push(currentStroke);
        }
        isDrawing = false;
    });

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

    function sendData() {
        fetch('http://localhost:5000/preprocess', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ vector_images: allStrokes })
        })
            .then(response => response.json())
            .then(data => console.log(data));
    }

});
