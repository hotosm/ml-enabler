const Assembly = require('@mapbox/assembly');

module.exports = {
    publicPath: './',
    chainWebpack: config => {
        Assembly.buildUserAssets('public/')
    }
}
