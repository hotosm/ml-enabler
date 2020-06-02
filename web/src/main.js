import Vue from 'vue'
import App from './App.vue'
import router from './router'

Vue.config.productionTip = false

window.api = window.location.pathname.replace(/\/admin\/.*/, '');

new Vue({
    router,
    render: h => h(App)
}).$mount('#app')
