import { defineStore } from 'pinia'
import { login } from '@/api/bill'
import { setToken, getToken } from '@/utils/request'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken() || '',
    userId: 0,
    nickname: ''
  }),
  actions: {
    async loginWechat(code: string) {
      const res = await login(code)
      this.token = res.token
      this.userId = res.user_id
      setToken(res.token)
      return res
    },
    logout() {
      this.token = ''
      this.userId = 0
      uni.removeStorageSync('token')
    }
  }
})
