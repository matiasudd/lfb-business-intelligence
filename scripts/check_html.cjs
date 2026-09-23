const { chromium } = require('C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
(async()=>{
 const root=path.resolve(__dirname,'..');
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 const page=await browser.newPage({viewport:{width:1366,height:1000}});
 await page.goto(pathToFileURL(path.join(root,'outputs/C1_LFB.html')).href);
 await page.screenshot({path:path.join(root,'.build/notebook-top.png')});
 const summary=page.locator('h2').filter({hasText:'tl;dr'});
 await summary.scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(root,'.build/notebook-summary.png')});
 const last=page.locator('h2').filter({hasText:'Takeaways'});
 await last.scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(root,'.build/notebook-takeaways.png')});
 console.log(JSON.stringify(await page.evaluate(()=>({images:document.images.length,brokenImages:[...document.images].filter(i=>!i.complete||i.naturalWidth===0).length,title:document.querySelector('h1')?.textContent}))))
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
