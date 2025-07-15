"use strict";

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
        // Use deprecated addListener/removeListener for IE/Edge compatibility
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

// For Node.js/CommonJS environment
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createObservable
    };
}