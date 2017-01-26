from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class sb_Snowball(models.Model):
  name       = models.TextField(null=True, unique=True, verbose_name="SB Name")
  iniPearls  = models.TextField(null=True,              verbose_name="SB Initial Pearls") 
  date       = models.DateTimeField(                    verbose_name="SB Date") 
  step_count = models.IntegerField(null=True,           verbose_name="SB Step Count")
  completed  = models.BooleanField(verbose_name="Is SB Completed?")
  users      = models.ManyToManyField(User)
  steps      = models.ManyToManyField('sb_Step')
  
  def __str__(self):
    return self.name

class sb_Step(models.Model):
  stepid     = models.TextField(null=True, unique=True, verbose_name="SB Step ID")
  date       = models.DateTimeField(                    verbose_name="SB Date")
  refS_count = models.IntegerField(null=True,           verbose_name="SB Reference search count")
  citS_count = models.IntegerField(null=True,           verbose_name="SB Citations search count")
  users      = models.ManyToManyField(User)

  def __str__(self):
    return self.stepid


class sb_Query(models.Model):
  title    = models.TextField(null=True, unique=True, verbose_name="Query Title")
  text     = models.TextField(null=True,              verbose_name="Query Text")
  date     = models.DateTimeField(                    verbose_name="Query Date")
  r_count  = models.IntegerField(null=True,           verbose_name="Query Results Count")
  users    = models.ManyToManyField(User)
  criteria = models.TextField(null=True)

  def __str__(self):           
    return self.title+' ('+self.date.strftime('%Y/%m/%d - %H:%M:%S')+'): '+self.text

class sb_Tag(models.Model):
  title = models.TextField(null=True,             verbose_name="Tag Title")
  text  = models.TextField(null=True,             verbose_name="Tag Text")
  query = models.ForeignKey('sb_Query',null=True, verbose_name="TagQuery")

  def __str__(self):
    return self.title

class sb_Doc(models.Model):
  UT      = models.CharField(max_length=30,db_index=True,primary_key=True)
  query   = models.ManyToManyField('sb_Query')
  tag     = models.ManyToManyField('sb_Tag')
  title   = models.TextField(null=True)
  content = models.TextField(null=True) 
  PY      = models.IntegerField(null=True,db_index=True)
  users   = models.ManyToManyField(User, through='sb_DocOwnership')
    
  def __str__(self):
    return self.UT

  def word_count(self):
    return len(str(self.content).split())

class sb_DocOwnership(models.Model):
  doc      = models.ForeignKey(sb_Doc,   on_delete=models.CASCADE)
  user     = models.ForeignKey(User,     on_delete=models.CASCADE, verbose_name="Reviewer")
  query    = models.ForeignKey(sb_Query, on_delete=models.CASCADE)
  tag      = models.ForeignKey(sb_Tag,   on_delete=models.CASCADE, null=True)
  relevant = models.IntegerField(default=0, db_index=True, verbose_name="Relevance")

  def __str__(self):
    return self.doc

class sb_DocAuthInst(models.Model):
  doc         = models.ForeignKey('sb_Doc',null=True, verbose_name="Author - Document")
  AU          = models.CharField(max_length=60, db_index=True, null=True, verbose_name="Author")
  AF          = models.CharField(max_length=60, db_index=True, null=True, verbose_name="Author Full Name")
  institution = models.CharField(max_length=150, db_index=True, verbose_name="Institution Name")
  position    = models.IntegerField(verbose_name="Author Position")

  def __str__(self):
    return self.doc

class sb_DocCites(models.Model):
  doc       = models.ForeignKey('sb_Doc',null=True, related_name='doc')
  reference = models.ForeignKey('sb_Doc',null=True, related_name='ref')

  def __str__(self):
    return self.doc

#class sb_DocIsCitedBy(models.Model):
#    doc      = models.ForeignKey('sb_Doc',null=True, related_name='doc')
#    citation = models.ForeignKey('sb_Doc',null=True, related_name='cit')

##############################################
## Article holds more WoS type information for each doc

class sb_WoSArticle(models.Model):
  doc = models.OneToOneField(
    'sb_Doc',
    on_delete=models.CASCADE,
    primary_key=True
  )
  ti = models.TextField(null=True, verbose_name="Title")
  ab = models.TextField(null=True, verbose_name="Abstract")   
  py = models.IntegerField(null=True, verbose_name="Year") 
  ar = models.CharField(null=True, max_length=100, verbose_name="Article Number") # Article number
  bn = models.CharField(null=True, max_length=100, verbose_name="ISBN") # ISBN
  bp = models.CharField(null=True, max_length=10, verbose_name="Beginning Page") # beginning page
  c1 = models.TextField(null=True, verbose_name="Author Address") # author address
  cl = models.TextField(null=True, verbose_name="Conference Location") # conf location
  ct = models.TextField(null=True, verbose_name="Conference Title") # conf title
  de = models.TextField(null=True, verbose_name="Author Keywords") # keywords - separate table?
  di = models.CharField(null=True, max_length=150, verbose_name="DOI") # DOI
  dt = models.CharField(null=True, max_length=50, verbose_name="Document Type") # doctype
  em = models.TextField(null=True, verbose_name="E-mail Address") #email 
  ep = models.CharField(null=True, max_length=10, verbose_name="Ending Page") # last page
  fn = models.CharField(null=True, max_length=150, verbose_name="File Name") # filename?
  fu = models.TextField(null=True, verbose_name="Funding Agency and Grant Number") #funding agency + grant number
  fx = models.TextField(null=True, verbose_name="Funding Text") # funding text
  ga = models.CharField(null=True, max_length=100, verbose_name="Document Delivery Number") # document delivery number
  ho = models.TextField(null=True, verbose_name="Conference Host") # conference host
  #ID = models.TextField() # keywords plus ??
  kwp = models.TextField(null=True, verbose_name="Keywords Plus")
  j9 = models.CharField(null=True, max_length=30, verbose_name="29-Character Source Abbreviation") # 29 char source abbreviation
  ji = models.CharField(null=True, max_length=100, verbose_name="ISO Source Abbreviation") # ISO source abbrev
  la = models.CharField(null=True, max_length=100, verbose_name="Language") # Language
  nr = models.IntegerField(null=True, verbose_name="Cited Reference Count") # number of references
  pa = models.TextField(null=True, verbose_name="Publisher Address") # pub address
  pd = models.CharField(null=True, max_length=10, verbose_name="Publication Date") # pub month
  pg = models.IntegerField(null=True, verbose_name="Page Count") # page count
  pi = models.TextField(null=True, verbose_name="Publisher City") # pub city
  pt = models.CharField(null=True, max_length=50, verbose_name="Publication Type") # pub type
  pu = models.TextField(null=True, verbose_name="Publisher") # publisher
  rp = models.TextField(null=True, verbose_name="Reprint Address") # reprint address
  sc = models.TextField(null=True, verbose_name="Subject Category") # subj category
  se = models.TextField(null=True, verbose_name="Book Series Title") # book series title
  si = models.TextField(null=True, verbose_name="Special Issue") # special issue
  sn = models.CharField(null=True, max_length=80, verbose_name="ISSN") # ISSN
  so = models.CharField(null=True, max_length=150, verbose_name="Publication Name") # publication name
  sp = models.TextField(null=True, verbose_name="Conference Sponsors") # conf sponsors
  su = models.TextField(null=True, verbose_name="Supplement") # supplement
  tc = models.IntegerField(null=True, verbose_name="Times Cited") # times cited
  vl = models.CharField(null=True, max_length=10, verbose_name="Volume")

  def __str__(self):
    return self.doc


