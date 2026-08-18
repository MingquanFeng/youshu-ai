// components/line-chart/line-chart.js — 近 30 天折线图
// props:
//   data: Array<{ date_short: string, total: number }>
//   height: Number, 容器高度 rpx, 默认 320
Component({
  options: { styleIsolation: 'apply-shared' },
  properties: {
    data: { type: Array, value: [] },
    height: { type: Number, value: 320 }
  },
  data: { canvasId: '' },
  lifetimes: {
    attached() {
      // canvas-id 必须唯一, 用随机后缀避免同页多实例冲突
      this.setData({
        canvasId: 'linechart-' + Date.now() + '-' + Math.floor(Math.random() * 1000)
      });
    },
    ready() {
      this.drawChart();
    }
  },
  observers: {
    data: function () {
      this.drawChart();
    }
  },
  methods: {
    drawChart() {
      const data = this.data.data || [];
      if (!data.length) return;
      const canvasId = this.data.canvasId;
      if (!canvasId) return;
      const query = wx.createSelectorQuery().in(this);
      query
        .select('#' + canvasId)
        .fields({ node: true, size: true })
        .exec((res) => {
          if (!res || !res[0] || !res[0].node) return;
          this._render(res[0].node, res[0].width, res[0].height);
        });
    },

    _getTokenColor(name) {
      // 从 page 继承 CSS 变量值 (canvas 不能直接用 var())
      // 通过 queryComputedStyle 读不到 wxss 变量, 用 wx.getSystemInfo/getApp 兜底
      // 简化为写死 light/dark 两套, 通过 wx.getSystemInfoSync().theme 判断
      const sys = wx.getSystemInfoSync();
      const dark = sys.theme === 'dark';
      const palette = {
        light: {
          line: '#10B981',
          lineSoft: 'rgba(16,185,129,0.10)',
          text: '#9CA3AF',
          grid: '#F4F1ED',
          dot: '#FFFFFF'
        },
        dark: {
          line: '#34D399',
          lineSoft: 'rgba(52,211,153,0.15)',
          text: '#787673',
          grid: '#2A2826',
          dot: '#161513'
        }
      }[dark ? 'dark' : 'light'];
      return palette[name];
    },

    _render(canvas, cssWidth, cssHeight) {
      const ctx = canvas.getContext('2d');
      const dpr = wx.getSystemInfoSync().pixelRatio || 1;
      canvas.width = cssWidth * dpr;
      canvas.height = cssHeight * dpr;
      ctx.scale(dpr, dpr);

      const data = this.data.data;
      const W = cssWidth;
      const H = cssHeight;

      // 边距 (留给 y 轴标签 + x 轴标签)
      const padL = 40,
        padR = 16,
        padT = 16,
        padB = 32;
      const chartW = W - padL - padR;
      const chartH = H - padT - padB;

      const values = data.map((d) => Number(d.total) || 0);
      const maxV = Math.max(...values, 1); // 至少 1, 避免除零
      const minV = 0;

      // 配色
      const COL = {
        line: this._getTokenColor('line'),
        lineSoft: this._getTokenColor('lineSoft'),
        text: this._getTokenColor('text'),
        grid: this._getTokenColor('grid'),
        dot: this._getTokenColor('dot')
      };

      // 清空
      ctx.clearRect(0, 0, W, H);

      // 网格 (4 条横线)
      ctx.strokeStyle = COL.grid;
      ctx.lineWidth = 1;
      const rows = 4;
      for (let i = 0; i <= rows; i++) {
        const y = padT + (chartH * i) / rows;
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(padL + chartW, y);
        ctx.stroke();
      }

      // y 轴标签 (max / mid / 0)
      ctx.fillStyle = COL.text;
      ctx.font = '10px -apple-system, sans-serif';
      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';
      const labels = [maxV, maxV / 2, 0];
      for (let i = 0; i < labels.length; i++) {
        const y = padT + (chartH * i) / 2;
        ctx.fillText('¥' + Math.round(labels[i]).toString(), padL - 6, y);
      }

      // x 轴标签 (取均匀分布的 ~5 个)
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      const xLabels = 5;
      for (let i = 0; i < xLabels; i++) {
        const idx = Math.round(((data.length - 1) * i) / (xLabels - 1));
        const x = padL + (chartW * i) / (xLabels - 1);
        ctx.fillText(data[idx].date_short, x, H - padB + 8);
      }

      // 计算点
      const points = data.map((d, i) => ({
        x: padL + (chartW * i) / (data.length - 1 || 1),
        y: padT + chartH - (chartH * (Number(d.total) || 0) - minV) / (maxV - minV || 1),
        v: Number(d.total) || 0
      }));

      // 折线下填充区 (从 line 到 x 轴)
      if (points.length > 1) {
        const grad = ctx.createLinearGradient(0, padT, 0, padT + chartH);
        grad.addColorStop(0, COL.lineSoft);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.moveTo(points[0].x, padT + chartH);
        points.forEach((p) => ctx.lineTo(p.x, p.y));
        ctx.lineTo(points[points.length - 1].x, padT + chartH);
        ctx.closePath();
        ctx.fill();
      }

      // 折线
      ctx.strokeStyle = COL.line;
      ctx.lineWidth = 2;
      ctx.lineJoin = 'round';
      ctx.lineCap = 'round';
      ctx.beginPath();
      points.forEach((p, i) => {
        if (i === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      });
      ctx.stroke();

      // 点 (圆)
      ctx.fillStyle = COL.dot;
      const r = 3;
      points.forEach((p) => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = COL.line;
        ctx.lineWidth = 2;
        ctx.stroke();
      });
    }
  }
});
