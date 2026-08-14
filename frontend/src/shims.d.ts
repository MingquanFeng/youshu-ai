/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare const uni: any

declare module '@dcloudio/uni-h5' {
  import type { Plugin } from 'vue'
  const plugin: Plugin
  export default plugin
}
