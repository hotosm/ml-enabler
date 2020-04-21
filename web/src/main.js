import Vue from 'vue'
import App from './App.vue'

Vue.config.productionTip = false

window.api = window.location.pathname.replace(/\/admin\/.*/, '');

new Vue({
  render: h => h(App),
}).$mount('#app')
