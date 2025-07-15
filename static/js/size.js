"use strict";

function size(dimensions) {
    var width = dimensions.width;
    var height = dimensions.height;
    
    if (width < 0) {
        throw new Error('Negative width is not allowed for Size');
    }
    if (height < 0) {
        throw new Error('Negative height is not allowed for Size');
    }
    
    return {
        width: width,
        height: height
    };
}

function equalSizes(first, second) {
    return (first.width === second.width) &&
           (first.height === second.height);
}

// For Node.js/CommonJS environment
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        size: size,
        equalSizes: equalSizes
    };
}