import json, pathlib, unittest, sys
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import pipeline
class PipelineV4Tests(unittest.TestCase):
 def test_categories(self):
  self.assertEqual(len(pipeline.CATS),5)
 def test_sanitize(self):
  self.assertNotIn('<b>',pipeline.plain('<b>Örnek</b>'))
 def test_sources_https(self):
  for s in pipeline.read('sources.json',{})['sources']:
   from urllib.parse import urlparse
   self.assertEqual(urlparse(s['url']).scheme,'https')
   self.assertEqual(urlparse(s['url']).hostname,s['host'])
 def test_news_structure(self):
  self.assertIsInstance(pipeline.read('news.json',{'items':[]})['items'],list)
if __name__=='__main__':unittest.main()
