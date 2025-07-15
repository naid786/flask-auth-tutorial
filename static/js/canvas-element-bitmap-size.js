"use strict";

// Imported utilities (converted to vanilla JS)
function size(dimensions) {
    const width = dimensions.width;
    const height = dimensions.height;
    
    if (width < 0) throw new Error('Negative width is not allowed for Size');
    if (height < 0) throw new Error('Negative height is not allowed for Size');
    
    return { width, height };
}

function equalSizes(first, second) {
    return first.width === second.width && first.height === second.height;
}

class Observable {
    constructor(win) {
        this._resolutionListener = () => this._onResolutionChanged();
        this._resolutionMediaQueryList = null;
        this._observers = [];
        this._window = win;
        this._installResolutionListener();
    }

    dispose() {
        this._uninstallResolutionListener();
        this._window = null;
    }

    get value() {
        return this._window.devicePixelRatio;
    }

    subscribe(next) {
        const observer = { next };
        this._observers.push(observer);
        return {
            unsubscribe: () => {
                this._observers = this._observers.filter(o => o !== observer);
            }
        };
    }

    _installResolutionListener() {
        if (this._resolutionMediaQueryList !== null) {
            throw new Error('Resolution listener is already installed');
        }
        const dppx = this._window.devicePixelRatio;
        this._resolutionMediaQueryList = this._window.matchMedia(`all and (resolution: ${dppx}dppx)`);
        this._resolutionMediaQueryList.addListener(this._resolutionListener);
    }

    _uninstallResolutionListener() {
        if (this._resolutionMediaQueryList !== null) {
            this._resolutionMediaQueryList.removeListener(this._resolutionListener);
            this._resolutionMediaQueryList = null;
        }
    }

    _reinstallResolutionListener() {
        this._uninstallResolutionListener();
        this._installResolutionListener();
    }

    _onResolutionChanged() {
        this._observers.forEach(observer => observer.next(this._window.devicePixelRatio));
        this._reinstallResolutionListener();
    }
}

function createObservable(win) {
    return new Observable(win);
}

// Main DevicePixelContentBoxBinding class
class DevicePixelContentBoxBinding {
    constructor(canvasElement, transformBitmapSize, options) {
        this._canvasElement = null;
        this._bitmapSizeChangedListeners = [];
        this._suggestedBitmapSize = null;
        this._suggestedBitmapSizeChangedListeners = [];
        this._devicePixelRatioObservable = null;
        this._canvasElementResizeObserver = null;

        this._canvasElement = canvasElement;
        this._canvasElementClientSize = size({
            width: this._canvasElement.clientWidth,
            height: this._canvasElement.clientHeight,
        });
        this._transformBitmapSize = transformBitmapSize || (size => size);
        this._allowResizeObserver = options?.allowResizeObserver ?? true;
        this._chooseAndInitObserver();
    }

    dispose() {
        if (this._canvasElement === null) throw new Error('Object is disposed');
        
        this._canvasElementResizeObserver?.disconnect();
        this._canvasElementResizeObserver = null;
        this._devicePixelRatioObservable?.dispose();
        this._devicePixelRatioObservable = null;
        this._suggestedBitmapSizeChangedListeners = [];
        this._bitmapSizeChangedListeners = [];
        this._canvasElement = null;
    }

    get canvasElement() {
        if (this._canvasElement === null) throw new Error('Object is disposed');
        return this._canvasElement;
    }

    get canvasElementClientSize() {
        return this._canvasElementClientSize;
    }

    get bitmapSize() {
        return size({
            width: this.canvasElement.width,
            height: this.canvasElement.height,
        });
    }

    resizeCanvasElement(clientSize) {
        this._canvasElementClientSize = size(clientSize);
        this.canvasElement.style.width = `${this._canvasElementClientSize.width}px`;
        this.canvasElement.style.height = `${this._canvasElementClientSize.height}px`;
        this._invalidateBitmapSize();
    }

    subscribeBitmapSizeChanged(listener) {
        this._bitmapSizeChangedListeners.push(listener);
    }

    unsubscribeBitmapSizeChanged(listener) {
        this._bitmapSizeChangedListeners = this._bitmapSizeChangedListeners.filter(l => l !== listener);
    }

    get suggestedBitmapSize() {
        return this._suggestedBitmapSize;
    }

    subscribeSuggestedBitmapSizeChanged(listener) {
        this._suggestedBitmapSizeChangedListeners.push(listener);
    }

    unsubscribeSuggestedBitmapSizeChanged(listener) {
        this._suggestedBitmapSizeChangedListeners = this._suggestedBitmapSizeChangedListeners.filter(l => l !== listener);
    }

    applySuggestedBitmapSize() {
        if (this._suggestedBitmapSize === null) return;
        
        const oldSuggestedSize = this._suggestedBitmapSize;
        this._suggestedBitmapSize = null;
        this._resizeBitmap(oldSuggestedSize);
        this._emitSuggestedBitmapSizeChanged(oldSuggestedSize, this._suggestedBitmapSize);
    }

    _resizeBitmap(newSize) {
        const oldSize = this.bitmapSize;
        if (equalSizes(oldSize, newSize)) return;
        
        this.canvasElement.width = newSize.width;
        this.canvasElement.height = newSize.height;
        this._emitBitmapSizeChanged(oldSize, newSize);
    }

    _emitBitmapSizeChanged(oldSize, newSize) {
        this._bitmapSizeChangedListeners.forEach(listener => listener.call(this, oldSize, newSize));
    }

    _suggestNewBitmapSize(newSize) {
        const oldSuggestedSize = this._suggestedBitmapSize;
        const finalNewSize = size(this._transformBitmapSize(newSize, this._canvasElementClientSize));
        const newSuggestedSize = equalSizes(this.bitmapSize, finalNewSize) ? null : finalNewSize;
        
        if (oldSuggestedSize === null && newSuggestedSize === null) return;
        if (oldSuggestedSize !== null && newSuggestedSize !== null && equalSizes(oldSuggestedSize, newSuggestedSize)) return;
        
        this._suggestedBitmapSize = newSuggestedSize;
        this._emitSuggestedBitmapSizeChanged(oldSuggestedSize, newSuggestedSize);
    }

    _emitSuggestedBitmapSizeChanged(oldSize, newSize) {
        this._suggestedBitmapSizeChangedListeners.forEach(listener => listener.call(this, oldSize, newSize));
    }

    _chooseAndInitObserver() {
        if (!this._allowResizeObserver) {
            this._initDevicePixelRatioObservable();
            return;
        }
        
        isDevicePixelContentBoxSupported()
            .then(isSupported => isSupported ? 
                this._initResizeObserver() : 
                this._initDevicePixelRatioObservable());
    }

    _initDevicePixelRatioObservable() {
        if (this._canvasElement === null) return;
        
        const win = canvasElementWindow(this._canvasElement);
        if (win === null) throw new Error('No window is associated with the canvas');
        
        this._devicePixelRatioObservable = createObservable(win);
        this._devicePixelRatioObservable.subscribe(() => this._invalidateBitmapSize());
        this._invalidateBitmapSize();
    }

    _invalidateBitmapSize() {
        if (this._canvasElement === null) return;
        
        const win = canvasElementWindow(this._canvasElement);
        if (win === null) return;
        
        const ratio = this._devicePixelRatioObservable?.value ?? win.devicePixelRatio;
        const canvasRects = this._canvasElement.getClientRects();
        const newSize = canvasRects[0] !== undefined ?
            predictedBitmapSize(canvasRects[0], ratio) :
            size({
                width: this._canvasElementClientSize.width * ratio,
                height: this._canvasElementClientSize.height * ratio,
            });
        
        this._suggestNewBitmapSize(newSize);
    }

    _initResizeObserver() {
        if (this._canvasElement === null) return;
        
        this._canvasElementResizeObserver = new ResizeObserver(entries => {
            const entry = entries.find(entry => entry.target === this._canvasElement);
            if (!entry?.devicePixelContentBoxSize?.[0]) return;
            
            const entrySize = entry.devicePixelContentBoxSize[0];
            const newSize = size({
                width: entrySize.inlineSize,
                height: entrySize.blockSize,
            });
            
            this._suggestNewBitmapSize(newSize);
        });
        
        this._canvasElementResizeObserver.observe(this._canvasElement, { box: 'device-pixel-content-box' });
    }
}

// Helper functions
function bindTo(canvasElement, target) {
    if (target.type === 'device-pixel-content-box') {
        return new DevicePixelContentBoxBinding(canvasElement, target.transform, target.options);
    }
    throw new Error('Unsupported binding target');
}

function canvasElementWindow(canvasElement) {
    return canvasElement.ownerDocument.defaultView;
}

function isDevicePixelContentBoxSupported() {
    return new Promise(resolve => {
        const ro = new ResizeObserver(entries => {
            resolve(entries.every(entry => 'devicePixelContentBoxSize' in entry));
            ro.disconnect();
        });
        ro.observe(document.body, { box: 'device-pixel-content-box' });
    }).catch(() => false);
}

function predictedBitmapSize(canvasRect, ratio) {
    return size({
        width: Math.round(canvasRect.left * ratio + canvasRect.width * ratio) - Math.round(canvasRect.left * ratio),
        height: Math.round(canvasRect.top * ratio + canvasRect.height * ratio) - Math.round(canvasRect.top * ratio)
    });
}

// Export for Node.js/CommonJS environment
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        bindTo,
        size,
        equalSizes,
        createObservable
    };
}