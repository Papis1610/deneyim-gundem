import unittest, pathlib, sys, xml.etree.ElementTree as ET
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import pipeline as p
S={'name':'TCMB','host':'www.tcmb.gov.tr','url':'https://www.tcmb.gov.tr/rss','category':'Ekonomi'}
class Tests(unittest.TestCase):
 def test_turkish_dates(self):
  self.assertEqual(p.date_value('1 Eki 2026 00:00:00'),'2026-10-01')
  self.assertEqual(p.date_value('9 Ekim 2026'),'2026-10-09')
  self.assertEqual(p.date_value('31 Şubat 2026'),'')
 def test_feed_https_and_publication_date(self):
  xml=b'<feed><entry><title>A &amp; B</title><link rel="alternate" href="http://www.tcmb.gov.tr/a"/><published>1 Eki 2026 00:00:00</published><updated>9 Eki 2026</updated></entry></feed>'
  x=p.parse_feed(xml,S)[0]
  self.assertEqual(x['url'],'https://www.tcmb.gov.tr/a');self.assertEqual(x['published_at'],'2026-10-01');self.assertIsNone(x['effective_at']);self.assertEqual(x['business_impact'],'');self.assertFalse(x['verified'])
 def test_untrusted_links(self):
  for u in ['https://example.com/a','https://www.tcmb.gov.tr@evil.com/a','javascript:alert(1)','https://www.tcmb.gov.tr:444/a']:
   with self.assertRaises(ValueError):p.safe_url(u,S['url'],S['host'])
 def test_no_modified_date_substitution(self):
  self.assertEqual(p.parse_feed(b'<feed><entry><title>A</title><link href="/a"/><updated>2026-10-01</updated></entry></feed>',S),[])
 def test_no_doctype(self):
  with self.assertRaises(ValueError):p.parse_feed(b'<!DOCTYPE feed><feed/>',S)
 def test_external_link_omitted(self):
  self.assertEqual(p.parse_feed(b'<feed><entry><title>A</title><link href="https://evil.com/a"/><published>2026-10-01</published></entry></feed>',S),[])
 def test_sgk(self):
  s={**S,'host':'www.sgk.gov.tr','url':'https://www.sgk.gov.tr/duyuru','category':'SGK'}
  raw='<a href="/duyuru/detay/a"><div class="date-day">9</div><div class="date-month">Ekim</div><div class="date-year">2026</div><div class="announcement-title">Duyuru &amp; Bilgi</div></a>'.encode()
  x=p.parse_sgk(raw,s)[0];self.assertEqual(x['title'],'Duyuru & Bilgi');self.assertEqual(x['published_at'],'2026-10-09')
 def test_changed_sgk_structure(self):
  with self.assertRaises(ValueError):p.parse_sgk(b'<html>Oops</html>',S)
 def test_future_omitted(self):self.assertIsNone(p.item(S,'A','/a','2099-01-01',''))
 def test_html_clean(self):self.assertEqual(p.plain('<p>Faiz &amp; fiyat</p>'),'Faiz & fiyat')
if __name__=='__main__':unittest.main()

class CollectionFailureTests(unittest.TestCase):
 def test_failures_preserve_items_and_fail_job(self):
  from unittest.mock import patch
  old={'updated_at':'2026-10-08T00:00:00+00:00','items':[{'id':'a','published_at':'2026-10-01','title':'old'}]}
  files={'news.json':old,'sources.json':{'sources':[S]}};writes={}
  with patch.object(p,'read',side_effect=lambda name,default:files.get(name,default)),patch.object(p,'write',side_effect=lambda name,obj:writes.update({name:obj})),patch.object(p,'fetch',side_effect=TimeoutError('timeout')):
   with self.assertRaises(SystemExit):p.collect()
  self.assertEqual(writes['news.json']['items'],old['items']);self.assertEqual(writes['news.json']['updated_at'],old['updated_at']);self.assertEqual(writes['news.json']['sources'][0]['status'],'error')
 def test_redirect_rejected_before_fetch(self):
  import urllib.request
  req=urllib.request.Request('https://www.tcmb.gov.tr/rss')
  with self.assertRaises(ValueError):p.SafeRedirect().redirect_request(req,None,302,'',{},'https://evil.com/')
