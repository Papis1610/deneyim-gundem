"""Verify live Pages with isolated Chromium contexts at phone and desktop sizes."""
import json, os, pathlib, sys
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect
url=sys.argv[1]
artifacts=pathlib.Path('verification');artifacts.mkdir(exist_ok=True)
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch()
 for width,height in [(390,844),(1280,900)]:
  context=browser.new_context(viewport={'width':width,'height':height})
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  response=page.goto(url,wait_until='networkidle');assert response.status==200
  cards=page.locator('.card');expect(cards.first).to_be_visible()
  total=cards.count();assert total>0
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),'Horizontal overflow'
  assert page.locator('#freshness').is_hidden(),'Stale or unavailable live feed'
  assert page.locator('.source .state.ok').count()>=2
  page.locator('.headline').first.click();expect(page.locator('#detail')).to_be_visible()
  assert 'Belirtilmedi' in page.locator('#detail').inner_text()
  assert page.locator('#detail-body a').get_attribute('href').startswith('https://')
  page.locator('#close-detail').click()
  page.locator('.save').first.click();page.locator('#saved-only').check();assert cards.count()==1
  page.reload(wait_until='networkidle');page.locator('#saved-only').check();assert cards.count()==1
  page.locator('#saved-only').uncheck()
  page.locator('#search').fill('e-Borcu');assert cards.count()==1
  page.locator('#search').fill('')
  page.get_by_role('button',name='SGK',exact=True).click()
  assert 'SGK' not in page.locator('.card .tag').all_text_contents()
  page.get_by_role('button',name='SGK',exact=True).click();assert cards.count()==total
  page.locator('#refresh').click();expect(page.locator('#refresh')).to_be_enabled()
  assert cards.count()==total
  links=page.locator('.card-bottom a').evaluate_all('(els)=>els.map(e=>e.href)')
  assert all(urlparse(l).scheme=='https' and urlparse(l).hostname in {'www.tcmb.gov.tr','www.sgk.gov.tr','www.gib.gov.tr','www.resmigazete.gov.tr'} for l in links)
  page.screenshot(path=str(artifacts/f'live-{width}.png'),full_page=False)
  assert not errors,errors
  results.append({'width':width,'height':height,'cards':total,'horizontal_overflow':False,'details':True,'search':True,'category_filter':True,'saved_persistence':True,'refresh':True,'console_errors':errors})
  context.close()
 browser.close()
(artifacts/'results.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results))
