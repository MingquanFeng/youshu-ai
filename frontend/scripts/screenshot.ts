import { chromium } from 'playwright'

async function main() {
  const URL = process.env.URL || 'http://localhost:5173/'
  const SCREENSHOT = process.env.SHOT || '/tmp/page.png'

  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 375, height: 812 },
    deviceScaleFactor: 2,
    hasTouch: true
  })
  const page = await context.newPage()

  const logs: string[] = []
  page.on('console', m => logs.push(`[${m.type()}] ${m.text()}`))
  page.on('pageerror', e => logs.push(`[pageerror] ${e.message}`))

  const token = process.env.TOKEN || ''
  if (token) {
    await context.addInitScript((t) => {
      localStorage.setItem('token', t)
    }, token)
  }

  try {
    await page.goto(URL, { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(2000)

    if (process.env.PULL_DOWN === '1') {
      // 在浏览器内定义 dispatch 函数，触发 touchstart + 一系列 touchmove
      await page.evaluate(`(function() {
        const startY = 120;
        const endY = 600;
        function dispatch(type, y) {
          const wrappers = document.querySelectorAll('uni-page-wrapper, uni-page-body, uni-page');
          const target = (wrappers[wrappers.length - 1]) || document.body;
          const t = new Touch({
            identifier: 1,
            target: target,
            clientX: 187, clientY: y, pageX: 187, pageY: y,
            screenX: 187, screenY: y, radiusX: 5, radiusY: 5,
            rotationAngle: 0, force: 1
          });
          const touches = type === 'touchend' ? [] : [t];
          const evt = new TouchEvent(type, {
            cancelable: true, bubbles: true,
            touches: touches, targetTouches: touches, changedTouches: [t]
          });
          target.dispatchEvent(evt);
        }
        dispatch('touchstart', startY);
        for (let y = startY; y <= endY; y += 20) {
          dispatch('touchmove', y);
        }
      })()`)
      // 不发送 touchend，保留下拉状态截图
      await page.waitForTimeout(500)
    }

    await page.screenshot({ path: SCREENSHOT, fullPage: false })
    const bodyText = await page.evaluate(() => document.body.innerText)
    console.log('===SHOT===')
    console.log(SCREENSHOT)
    console.log('===BODY===')
    console.log(bodyText.substring(0, 800))
    console.log('===LOGS===')
    logs.forEach(l => console.log(l))
  } catch (e: any) {
    console.error('NAV ERROR:', e.message)
    logs.forEach(l => console.log(l))
  }

  await browser.close()
}

main().catch(e => { console.error(e); process.exit(1) })
