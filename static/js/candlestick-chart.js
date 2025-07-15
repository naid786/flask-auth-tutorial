class DrawLineSeriesPaneRenderer {
    constructor(series, options) {
        this._series = series;
        this._options = options;
    }

    draw(target) {
        target.useBitmapCoordinateSpace(scope => {
            if (
                this._series === null ||
                this._series.p1.x === null ||
                this._series.p1.y === null ||
                this._series.p2.x === null ||
                this._series.p2.y === null
            )
                return;

            this._drawLine(scope, this._series.p1.x, this._series.p1.y, this._series.p2.x, this._series.p2.y)
            return
            // this._series.map((series, index) => {
            //     if (
            //         series.p1.x === null ||
            //         series.p1.y === null ||
            //         series.p2.x === null ||
            //         series.p2.y === null
            //     )
            //         return;
            //     this._drawLine(scope, series.p1.x, series.p1.y, series.p2.x, series.p2.y)
            // })

        })
    }

    _drawLine(scope, x1, y1, x2, y2, color = 'black', width = 1) {
        // Get the 2D drawing context
        const ctx = scope.context;

        // Begin a new path
        ctx.beginPath();

        // Set line style
        ctx.strokeStyle = this._options;
        ctx.lineWidth = width;

        // Move to starting point
        ctx.moveTo(x1, y1);

        // Draw line to ending point
        ctx.lineTo(x2, y2);

        // Stroke the line
        ctx.stroke();
    }

}

class DrawLineSeriesPaneView {
    constructor(source, line) {
        this._source = source;
        this._line = line;
        this._series = [{
            p1: { x: null, y: null },
            p2: { x: null, y: null }
        }];
    }

    update() {
        // this._source._data.map((data => {
        const series = this._source._series;
        const y1 = series.priceToCoordinate(this._line.p1.price);
        const y2 = series.priceToCoordinate(this._line.p2.price);
        const timeScale = this._source._chart.timeScale();
        const x1 = timeScale.timeToCoordinate(this._line.p1.time);
        const x2 = timeScale.timeToCoordinate(this._line.p2.time);
        this._series.p1 = { x: x1, y: y1 };
        this._series.p2 = { x: x2, y: y2 };
        // }))

    }

    renderer() {
        return new DrawLineSeriesPaneRenderer(
            this._series,
            this._source._options
        );
    }

}

class LineSeries {
    constructor(chart, series, data,color='black') {
        this._chart = chart;
        this._series = series;
        this._data = data;
        this._options=color
        // this._minPrice = Math.min(this._p1.price, this._p2.price);
        // this._maxPrice = Math.max(this._p1.price, this._p2.price);

        this._paneViews = data.map((line) => { return new DrawLineSeriesPaneView(this, line) });
    }
    updateAllViews() {
        this._paneViews.forEach(pw => pw.update());
    }

    paneViews() {
        return this._paneViews;
    }

}

// Rectangle Primitive Class
class RectanglePrimitive {
    constructor(top, bottom, leftTime, rightTime, color) {
        this.top = top;
        this.bottom = bottom;
        this.leftTime = leftTime;
        this.rightTime = rightTime;
        this.color = color || 'rgba(100, 149, 237, 0.2)';
        this.paneViews = [new RectanglePaneView(this)];
    }

    attached(series) {
        this.series = series;
        this.chart = series.chart();
    }

    detached() {
        // Cleanup if needed
    }

    paneViews() {
        return this.paneViews;
    }

    updateAllViews() {
        this.paneViews.forEach(pw => pw.update());
    }
}

class RectangleSeriesPrimitive {
    constructor(chart, series, data) {
        this._chart = chart;
        this._series = series;
        this.data = data
        console.table(data)
        this._paneViews = data.map((rect) => { return new RectanglePaneView(this, rect) });
    }

    paneViews() {
        return this._paneViews;
    }

    updateAllViews() {
        this._paneViews.forEach(pw => pw.update());
    }
}


// Rectangle Pane View for drawing
class RectanglePaneView {
    constructor(source, rects) {
        this.source = source;
        this.rects = rects
    }

    update() {
        // Update logic if needed
    }

    renderer() {
        const data = this.rects;
        return {
            draw: (target) => {
                target.useBitmapCoordinateSpace(scope => {
                    const topY = this.source._series.priceToCoordinate(data.top);
                    const bottomY = this.source._series.priceToCoordinate(data.bottom);

                    const timeScale = this.source._chart.timeScale();
                    const leftX = timeScale.timeToCoordinate(data.leftTime);
                    const rightX = timeScale.timeToCoordinate(data.rightTime);

                    if (topY === null || bottomY === null || leftX === null || rightX === null) return;

                    const ctx = scope.context;
                    ctx.globalAlpha = 0.5;
                    ctx.fillStyle = data.color;
                    ctx.strokeStyle = data.color.replace('0.2', '0.8');
                    ctx.lineWidth = 1;

                    ctx.beginPath();
                    ctx.rect(leftX, topY, rightX - leftX, bottomY - topY);
                    ctx.fill();
                    ctx.stroke();

                })

            },
        };
    }
}


class CandlestickChart extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.chart = null;
        this.series = null;
        this.trend = null;
        this.BOS = null;
        this.Gap = null;
        this.isPlot = null;
        this.crosshair = null
        this.data = [];
    }

    connectedCallback() {
        this.render();
        this.initChart();
        this.setupEventListeners();
    }

    static get observedAttributes() {
        return ['data', 'width', 'height', 'theme'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'data' && newValue) {
            this.data = JSON.parse(newValue);
            this.updateChart();
            // } else if ((name === 'width' || name === 'height') && this.chart) {
            //     this.chart.applyOptions({
            //         width: this.getAttribute('width') ? parseInt(this.getAttribute('width')) : undefined,
            //         height: this.getAttribute('height') ? parseInt(this.getAttribute('height')) : undefined
            //     });
        } else if (name === 'theme' && this.chart) {
            this.chart.applyOptions({
                layout: {
                    textColor: this.getAttribute('theme') === 'dark' ? 'white' : 'black',
                    background: {
                        color: this.getAttribute('theme') === 'dark' ? '#1e222d' : 'white'
                    }
                }
            });
        }
    }

    render() {
        this.shadowRoot.innerHTML = ` 
            <style>
                :host {
                    height: 100%;
                    width: 100%;
                    display: block;

                }
                .chart-container {
                    width: 100%;
                    height: 100%;
                    position: relative;
                    
    }
            </style>            
            <div class="chart-container" id="chart"></div>
        `
    }

    initChart() {
        const container = this.shadowRoot.getElementById('chart');
        if (!container) {
            console.error('Chart container not found');
            return;
        }

        // Verify library is loaded
        if (typeof LightweightCharts === 'undefined') {
            console.error('LightweightCharts library not loaded');
            return;
        }
        try {
            //     // Set default width/height if not specified
            const width = container.clientWidth; //this.getAttribute('width') || '600';
            const height = container.clientHeight; //this.getAttribute('height') || '300';
            // console.log(container, width, height);
            this.chart = LightweightCharts.createChart(container, {
                width: width,
                height: height,
                // layout: {
                //     textColor: this.getAttribute('theme') === 'dark' ? 'white' : 'black',
                //     background: {
                //         color: this.getAttribute('theme') === 'dark' ? '#1e222d' : 'white'
                //     }
                // },
                layout: {
                    textColor: 'black',
                    // background: {
                    //     color: this.getAttribute('theme') === 'dark' ? '#1e222d' : 'white'
                    // }
                },
                grid: {
                    vertLines: {
                        color: this.getAttribute('theme') === 'dark' ? '#2B2B43' : '#F0F3FA',
                    },
                    horzLines: {
                        color: this.getAttribute('theme') === 'dark' ? '#2B2B43' : '#F0F3FA',
                    },
                },
                rightPriceScale: {
                    borderVisible: true,
                },
                timeScale: {
                    borderVisible: false,
                    timeVisible: true,
                    secondsVisible: false,
                },
                crosshair: {
                    mode: 0,
                },
            });

            if (!this.chart || typeof this.chart.addSeries !== 'function') {
                throw new Error('Chart initialization failed');
            }

            this.series = this.chart.addSeries(LightweightCharts.CandlestickSeries, {
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
            });



            if (this.getAttribute('data')) {
                this.data = JSON.parse(JSON.parse(this.getAttribute('data')));
                this.data = this.data.map(item => {
                    return {
                        ...item,
                        // time: new Date(item.time / 1000)
                        time: item.time / 1000
                    };
                });

                console.log(this.data)
                this.updateChart();
            }
            if (this.getAttribute('symbol')) {
                const symbolName = this.getAttribute('symbol');

                const legend = document.createElement('div');
                legend.style = `position: absolute; left: 12px; top: 12px; z-index: 1; font-size: 14px; font-family: sans-serif; line-height: 18px; font-weight: 300;`;
                container.appendChild(legend);

                const firstRow = document.createElement('div');
                firstRow.innerHTML = symbolName;
                firstRow.style.color = 'Black';
                legend.appendChild(firstRow);

                this.chart.subscribeCrosshairMove(param => {
                    this.crosshair = param.seriesData.get(this.series)
                    if (param.time) {
                        const data = param.seriesData.get(this.series);
                        const close = data.close;
                        const open = data.open;
                        const high = data.high;
                        const low = data.low;
                        firstRow.innerHTML = `<div style={display:'block'}>${new Date(data.time * 1000)}</div>${symbolName}  <strong>O: ${open}</strong> <strong>H: ${high}</strong>  <strong>L: ${low}</strong> <strong>C: ${close}</strong>`;
                    }
                    else {
                        firstRow.innerHTML = symbolName;
                    }
                    // firstRow.innerHTML = `${symbolName} <strong>O:${open}</strong> <strong>H:${high}</strong>  <strong>L:${low}</strong> <strong>C:${close}</strong>`;
                });
            }

            const observeChartResize = new ResizeObserver(entries => {
                for (let entry of entries) {
                    const { width, height } = entry.contentRect;
                    this.chart.resize(width, height);
                    this.chart.timeScale().fitContent();
                }
            }
            );
            observeChartResize.observe(container);

            window.addEventListener("DOMContentLoaded", () => {
                this.chart.resize(this.shadowRoot.getElementById('chart').clientWidth, this.shadowRoot.getElementById('chart').clientHeight);
                this.chart.timeScale().fitContent();
            });

            this.chart.onMousedown = (e) => this.handlePointerDown(e);

        } catch (error) {
            console.error('Failed to initialize chart:', error);
        }
    }

    setupEventListeners() {
        // Mouse and touch events for drawing
        const canvas = this.shadowRoot.getElementById('chart');

        // Mouse events
        canvas.addEventListener('click', (e) => this.handlePointerDown(e));
        canvas.addEventListener('mousemove', (e) => this.handlePointerMove(e));
        // canvas.addEventListener('mouseup', () => this.handlePointerUp());
        // canvas.addEventListener('mouseleave', () => this.handlePointerUp());
    }

    postSwingData() {
        return fetch('/swings', {  // Note the 'return' here
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ data: this.data })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(result => {
                return result;
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error: ' + error.message);
                throw error;
            });
    }

    postBOSData() {
        return fetch('/BOS', {  // Note the 'return' here
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ data: this.data })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(result => {
                return result;
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error: ' + error.message);
                throw error;
            });
    }

    postGapData() {
        return fetch('/getGap', {  // Note the 'return' here
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ data: this.data })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(result => {
                return result;
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error: ' + error.message);
                throw error;
            });
    }

    plotCandlestickMarkers(
        markerData,
        {
            defaultShape = 'circle',
            defaultSize = 1,
            upColor = '#26a69a',
            downColor = '#ef5350',
            autoPosition = true
        } = {}) {
        if (!this.series || !markerData || !Array.isArray(markerData)) {
            console.error('Invalid inputs for plotCandlestickMarkers');
            return;
        }

        const markers = markerData.map(item => {
            // Determine position based on candle type if autoPosition is enabled
            let position = item.position;
            if (autoPosition && !position) {
                //   const candle = this.series.dataByTime(item.time);
                if (item.isBull) {
                    position = 'aboveBar';
                }
                else {
                    position = 'belowBar';
                }

            }

            return {
                time: item.time,
                position: position || 'inBar',
                shape: item.shape || defaultShape,
                color: item.color || (item.direction === 'up' ? upColor : downColor),
                size: item.size || defaultSize,
                text: item.text || '',
                id: item.id
            };
        });
        // console.log(this.series)
        const seriesMarkers = LightweightCharts.createSeriesMarkers(this.series);
        // and then you can modify the markers
        // set it to empty array to remove all markers
        seriesMarkers.setMarkers(markers);
        //   setMarkers(markers);
    }

    plotBOS(data,isBull=true) {
        if (!data || !Array.isArray(data)) {
            console.error('Invalid inputs for plotCandlestickMarkers');
            return;
        }
        if (isBull){
            this.BOS = new LineSeries(this.chart, this.series, data,'#26a69a');
        }
        else{
            this.BOS = new LineSeries(this.chart, this.series, data,'#ef5350');
        }
        
        this.series.attachPrimitive(this.BOS);
        return

    }

    plotGap(data) {
        if (!data || !Array.isArray(data)) {
            console.error('Invalid inputs for plotCandlestickMarkers');
            return;
        }
        const Gaps = data.map((x) => {
            if (x.isBuy) {
                return {
                    'leftTime': x.index,
                    'rightTime': x.end,
                    'top': x.Post,
                    'bottom': x.Pre,
                    'color': '#26a69a'
                }
            }
            else {
                return {
                    'leftTime': x.index,
                    'rightTime': x.end,
                    'bottom': x.Post,
                    'top': x.Pre,
                    'color': '#ef5350'
                }
            }
        })
        this.Gap = new RectangleSeriesPrimitive(this.chart, this.series, Gaps);
        this.series.attachPrimitive(this.Gap);
        return

    }
    handlePointerDown(e) {
        // console.log(e);
        if (!this.drawingMode) return;


        if (this.isPlot) {
            this.isPlot = null;
        } else {
            console.log(this.isPlot)
            this.isPlot = true;

            const price = this.series.coordinateToPrice(e.clientY);
            const time = this.crosshair.time

            this.currentShape = {
                type: this.drawingMode,
                start: {
                    price: price,
                    time: time,
                },
                end: {
                    price: price,
                    time: time,
                },
                color: this.getRandomColor()
            };

            this.trend = new TrendLine(this.chart, this.series, this.currentShape.start, this.currentShape.end);
            this.series.attachPrimitive(this.trend);
            return
        }

        // console.log(this.currentShape)
    }

    handlePointerMove(e) {
        // e.preventDefault();
        if (!this.drawingMode || !this.currentShape) return;

        if (this.isPlot) {
            const price = this.series.coordinateToPrice(e.clientY);
            const time = this.chart.timeScale().coordinateToTime(e.clientX);

            this.currentShape.end.price = price;
            this.currentShape.end.time = time;
        }

        // console.log(this.series)
        // this.drawAllShapes();
    }

    handlePointerUp() {
        // if (!this.drawingMode || !this.currentShape) return;

        // this.drawnShapes.push({ ...this.currentShape });
        // this.currentShape = null;
        // this.drawAllShapes();
    }

    getRandomColor() {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }

    setDrawingMode(mode) {
        // Set active state for clicked button
        if (mode) {
            this.drawingMode = mode;
        } else {
            this.drawingMode = null;
        }
    }

    updateChart() {
        if (this.series && this.data) {
            this.series.setData(this.data);

            // Auto-fit time scale to data
            if (this.data.length > 0) {
                const firstTime = this.data[0].time;
                const lastTime = this.data[this.data.length - 1].time;
                this.chart.timeScale().setVisibleRange({
                    from: firstTime,
                    to: lastTime
                });
            }

        }
    }
    // Public method to update data
    updateData(newData) {
        this.data = newData;
        this.setAttribute('data', JSON.stringify(newData));
    }

    addDraggableWidget(widgetContent, widgetStyles = {}) {
        // Get the canvas element
        const canvas = this.shadowRoot.getElementById('chart');
        if (!canvas) {
            console.error('Canvas element not found');
            return;
        }

        // Create the widget container
        const widget = document.createElement('div');
        widget.className = 'draggable-widget';

        // Apply default styles and any custom styles
        const defaultStyles = {
            position: 'absolute',
            width: '200px',
            height: '150px',
            backgroundColor: '#f0f0f0',
            border: '1px solid #ccc',
            borderRadius: '5px',
            padding: '10px',
            cursor: 'move',
            zIndex: '1000',
            userSelect: 'none'
        };

        Object.assign(widget.style, defaultStyles, widgetStyles);

        // Add content to the widget
        widget.innerHTML = widgetContent;

        // Add the widget to the canvas
        canvas.appendChild(widget);

        // Make the widget draggable
        let isDragging = false;
        let offsetX, offsetY;

        widget.addEventListener('mousedown', (e) => {
            if (e.target === widget || e.target.parentNode === widget) {
                isDragging = true;

                // Calculate the offset between mouse position and widget position
                offsetX = e.clientX - widget.getBoundingClientRect().left;
                offsetY = e.clientY - widget.getBoundingClientRect().top;

                // Bring widget to front
                widget.style.zIndex = '1001';

                e.preventDefault();
            }
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;

            // Calculate new position
            const x = e.clientX - offsetX - canvas.getBoundingClientRect().left;
            const y = e.clientY - offsetY - canvas.getBoundingClientRect().top;

            // Set new position
            widget.style.left = `${x}px`;
            widget.style.top = `${y}px`;
        });

        document.addEventListener('mouseup', () => {
            isDragging = false;
            widget.style.zIndex = '1000';
        });

        return widget;
    }
}



customElements.define('candlestick-chart', CandlestickChart);