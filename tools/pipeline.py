#!/usr/bin/env python3
"""Official headline index. No generated legal summaries or inferred effective dates."""
import argparse, datetime as dt, hashlib, html, json, pathlib, re, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
CATS={'Vergi','SGK','Mevzuat','Ekonomi','İş Dünyası'}
MONTHS={'oca':1,'ocak':1,'şub':2,'şubat':2,'mar':3,'mart':3,'nis':4,'nisan':4,'may':5,'mayıs':5,'haz':6,'haziran':6,'tem':7,'temmuz':7,'ağu':8,'ağustos':8,'eyl':9,'eylül':9,'eki':10,'ekim':10,'kas':11,'kasım':11,'ara':12,'aralık':12}
def read(name,default):
 p=ROOT/name
 return json.loads(p.read_text()) if p.exists() else default
def write(name,obj):
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
def plain(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]*>',' ',s or ''))).strip()
def child_text(e,names):
 for c in e:
  if c.tag.rsplit('}',1)[-1] in names and c.text:return c.text.strip()
 return ''
def date_value(raw):
 raw=plain(raw)
 if not raw:return ''
 try:return dt.datetime.fromisoformat(raw.replace('Z','+00:00')).date().isoformat()
 except ValueError:pass
 m=re.match(r'^(\d{1,2})\s+([\wÇçĞğİıÖöŞşÜü]+)\s+(\d{4})(?:\s|$)',raw)
 if m:
  try:return dt.date(int(m[3]),MONTHS[m[2].lower()],int(m[1])).isoformat()
  except (ValueError,KeyError):return ''
 try:return parsedate_to_datetime(raw).date().isoformat()
 except (ValueError,TypeError):return ''
def safe_url(url,base,host):
 if not url or not url.strip():raise ValueError('Boş kaynak bağlantısı')
 p=urllib.parse.urlsplit(urllib.parse.urljoin(base,url))
 if p.hostname!=host or p.username or p.password or p.port not in (None,80,443) or p.scheme not in ('http','https'):raise ValueError('Kaynak dışı veya güvensiz bağlantı')
 return urllib.parse.urlunsplit(('https',host,p.path,p.query,''))
class SafeRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  a,b=urllib.parse.urlsplit(req.full_url),urllib.parse.urlsplit(newurl)
  if b.scheme!='https' or b.hostname!=a.hostname:raise ValueError('Kaynak dışı yönlendirme')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def fetch(url,host):
 safe_url(url,url,host)
 req=urllib.request.Request(url,headers={'User-Agent':'DeneyimGundem/1.0 official-headline-index','Accept':'application/xml,text/html,application/json'})
 with urllib.request.build_opener(SafeRedirect).open(req,timeout=20) as r:
  raw=r.read(2_000_001)
 if len(raw)>2_000_000:raise ValueError('Kaynak boyut sınırı aşıldı')
 return raw

def item(s,title,url,date,raw_date):
 url=safe_url(url,s['url'],s['host']);title=plain(title)
 if not title or not date or date>dt.datetime.now(dt.timezone.utc).date().isoformat():return None
 return {'id':hashlib.sha256(url.encode()).hexdigest()[:20],'category':s['category'],'title':title,'summary':'','source':s['name'],'url':url,'published_at':date,'published_at_raw':raw_date,'effective_at':None,'business_impact':'','content_type':'official_headline','review_status':'source_only','verified':False,'source_verified':True}
def parse_feed(raw,s):
 if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():raise ValueError('XML entity/DOCTYPE kabul edilmez')
 root=ET.fromstring(raw)
 if root.tag.rsplit('}',1)[-1] not in ('feed','rss','RDF'):raise ValueError('RSS/Atom bekleniyor')
 out=[]
 for e in root.iter():
  if e.tag.rsplit('}',1)[-1] not in ('entry','item'):continue
  link=child_text(e,{'link'})
  if not link:
   link=next((c.attrib['href'] for c in e if c.tag.rsplit('}',1)[-1]=='link' and c.attrib.get('href') and c.attrib.get('rel','alternate')=='alternate'),'')
  d=child_text(e,{'pubDate','published'}) # Do not substitute modification date for publication date.
  try:x=item(s,child_text(e,{'title'}),link,date_value(d),d)
  except ValueError:continue
  if x:out.append(x)
 return out

def parse_sgk(raw,s):
 text=raw.decode('utf-8');out=[]
 for link,body in re.findall(r'<a\b[^>]*href="([^"]*/duyuru/detay/[^"]+)"[^>]*>(.*?)</a>',text,re.S):
  def field(name):
   m=re.search(r'<div[^>]*class="[^"]*\b'+name+r'\b[^"]*"[^>]*>(.*?)</div>',body,re.S)
   return plain(m[1]) if m else ''
  d=' '.join(field(n) for n in ('date-day','date-month','date-year'))
  x=item(s,field('announcement-title'),link,date_value(d),d)
  if x:out.append(x)
 if not out:raise ValueError('SGK duyuru yapısı değişmiş veya tarihli kayıt yok')
 return out

def collect():
 now=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
 old=read('news.json',{'items':[]});prior_health={x['name']:x for x in old.get('sources',[])};all_items={x['id']:x for x in old['items']};health=[];success=0
 for s in read('sources.json',{})['sources']:
  state={'name':s['name'],'url':s['url'],'category':s['category'],'checked_at':now}
  if not s.get('enabled',True):
   health.append({**state,'status':'manual','message':s['note']});continue
  try:
   raw=fetch(s['url'],s['host'])
   records=(parse_sgk if s.get('adapter')=='sgk_html' else parse_feed)(raw,s)
   if not records:raise ValueError('Tarihi ve bağlantısı doğrulanabilir kayıt yok')
   for x in records:all_items[x['id']]=x
   success+=1;health.append({**state,'status':'ok','item_count':len(records),'last_success_at':now})
   print(s['name'],len(records),'başlık')
  except Exception as e:
   print(s['name'],'HATA',str(e));health.append({**state,'status':'error','message':str(e)[:200],'last_success_at':prior_health.get(s['name'],{}).get('last_success_at')})
 cutoff=(dt.datetime.now(dt.timezone.utc).date()-dt.timedelta(days=180)).isoformat()
 items=sorted((x for x in all_items.values() if x.get('published_at','')>=cutoff),key=lambda x:(x['published_at'],x['id']),reverse=True)[:300]
 write('news.json',{'schema_version':1,'updated_at':now if success else old.get('updated_at'),'last_attempt_at':now,'items':items,'sources':health})
 if not success:raise SystemExit('Tüm otomatik kaynaklar başarısız; son başarılı veri korundu')
def main():
 p=argparse.ArgumentParser();p.add_argument('cmd',choices=['collect']);p.parse_args();collect()
if __name__=='__main__':main()
