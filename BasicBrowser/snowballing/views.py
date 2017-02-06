from django.shortcuts import render
import os, time, math, itertools

# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.template import loader
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test

from .models import *


def super_check(user):
  return user.groups.filter(name__in=['superuser'])

########################################################
## Homepage - list the queries, form for adding new ones

@login_required
def index(request):
  template        = loader.get_template('snowballing/index.html')
  sb_sessions     = sb_SnowballingSession.objects.all().order_by('-id')
  sb_session_last = sb_sessions.last()
  context = {
    'sb_sessions': sb_sessions,
    'sb_session_last': sb_session_last
  }
  return HttpResponse(template.render(context, request))


#########################################################
## Start snowballing
import subprocess
import sys
@login_required
def start_snowballing(request):

  # Get information entered by user
  sbs_name = request.POST['sbs_name']
  sbs_IPs  = request.POST['sbs_initialpearls']

  cur_ts   = timezone.now()

  # create a new query record in the database
  q1 = sb_SnowballingSession(
    name          = sbs_name,
    intial_pearls = sbs_IPs,
    date          = cur_ts,
    step_count    = 1,
    users         = request.user,
    completed     = 0,
    steps         = [sb_Step.objects.get(stepid='1', date=cur_ts)]
  )
  q1.save()

  # crate first step
  q2 = sb_Step(
    stepid     = '1',
    date       = cur_ts,
    session    = sb_SnowballingSession.objects.get(name=sbs_name, date=cur_ts),
    users      = request.user,
    step_count = 1
  )
  q2.save()

  # create citation and reference queries
  q3_ref = sb_Query(
    title = 'sbs_'+sbs_name+'_Step1_ref',
    text  = sbs_IPs,
    date  = cur_ts,
    type  = sb_QueryType.objects.get(name='reference'),
    step  = sb_Step.objects.get(stepid='1', date=cur_ts)
  )
  q3_ref.save()
  q3_cit = sb_Query(
    title = 'sbs_'+sbs_name+'_Step1_cit',
    text  = sbs_IPs,
    date  = cur_ts,
    type  = sb_QueryType.objects.get(name='citation'),
    step  = sb_Step.objects.get(stepid='1', date=cur_ts)
  )
  q3_cit.save()

  # Start reference query

  # Start citation query 
  #subprocess.Popen(["scrapeQuery.py", fname])

  return HttpResponseRedirect(reverse('snowballing:do_snowballing', kwargs={'sbsid': q.id}))

#########################################################
## Perform snowballing
import subprocess
import sys
@login_required
def do_snowballing(request):

  # Load template 
  template = loader.get_template('snowballing/snowballing.html')

  # Get snowballing session information from database
  sbs = sb_SnowballingSession.objects.filter(id=sbsid,users=user)

  context = {
    'sbs': sbs
  }

  # Start reference query

  # Start citation query
  #subprocess.Popen(["scrapeQuery.py", fname])

  return HttpResponse(template.render(context, request))

#########################################################
## Do the query
import subprocess
import sys
@login_required
def doquery(request):

  qtitle = request.POST['qtitle']
  qtext  = request.POST['qtext']

    # create a new query record in the database
  q = sb_Query(
    title=qtitle,
    text=qtext,
    date=timezone.now()
  )
  q.save()

  # write the query into a text file
  fname = "queries/"+qtitle+".txt"
  with open(fname,"w") as qfile:
    qfile.write(qtext)

  # run "scrapeQuery.py" on the text file in the background
  subprocess.Popen(["scrapeQuery.py", fname])

  return HttpResponseRedirect(reverse('snowballing:querying', kwargs={'qid': q.id}))

#########################################################
## Add the documents to the database
@login_required
def dodocadd(request):
  qid = request.GET.get('qid',None)
  subprocess.Popen(["python3", "upload_docs_sb.py", qid])

  return HttpResponseRedirect(reverse('snowballing:querying', kwargs={'qid': qid}))

#########################################################
## Page views progress of query scraping

@login_required
def querying(request, qid):

  template = loader.get_template('snowballing/query_progress.html')

  query = sb_Query.objects.get(pk=qid)
  logfile = "queries/"+query.title+".log"

  wait = True
  # wait up to 15 seconds for the log file, then go to a page which displays its contents
  for i in range(15):
    try:
      with open(logfile,"r") as lfile:
        log = lfile.readlines()
      break
    except:
      log = ["oops, there seems to be some kind of problem, I can't find the log file"]
      time.sleep(1)

  finished = False
  if "done!" in log[-1]:
    finished = True

  # How many docs are there?
  docs = sb_Doc.objects.filter(query__id=qid)
  doclength = len(docs)

  context = {
    'log': log,
    'finished': finished,
    'docs': docs,
    'doclength': doclength,
    'query': query
  }

  return HttpResponse(template.render(context, request))

############################################################
## Query homepage - manage tags and user-doc assignments

@login_required
def query(request,qid):
  template = loader.get_template('snowballing/query.html')
  query = sb_Query.objects.get(pk=qid)

  tags = sb_Tag.objects.filter(query=query)

  tags = tags.values()

  for tag in tags:
    tag['docs']   = sb_Doc.objects.filter(tag=tag['id']).count()
    tag['a_docs'] = sb_DocOwnership.objects.filter(sb_doc__tag=tag['id'],).count()
    if tag['a_docs'] == 0:
      tag['a_docs'] = False
    else:
      tag['a_docs'] = sb_Doc.objects.filter(sb_docownership__tag=tag['id'],sb_docownership__isnull=False).distinct().count()
      tag['seen_docs']  = sb_DocOwnership.objects.filter(sb_doc__tag=tag['id'],relevant__gt=0).count()
      tag['rel_docs']   = sb_DocOwnership.objects.filter(sb_doc__tag=tag['id'],relevant=1).count()
      tag['irrel_docs'] = sb_DocOwnership.objects.filter(sb_doc__tag=tag['id'],relevant=2).count()
      try:
        tag['relevance'] = round(tag['rel_docs']/(tag['rel_docs']+tag['irrel_docs'])*100)
      except:
        tag['relevance'] = 0

  fields = ['id','title','text']

  untagged = sb_Doc.objects.filter(query=query,sb_tag__isnull=True).count()

  users = User.objects.all()

  proj_users = users.query

  user_list = []

  for u in users:
    user_docs = {}
    tdocs = sb_DocOwnership.objects.filter(query=query,user=u)
    user_docs['tdocs'] = tdocs.count()
    if user_docs['tdocs']==0:
      user_docs['tdocs'] = False
    else:
      user_docs['reldocs']   = tdocs.filter(relevant=1).count()
      user_docs['irreldocs'] = tdocs.filter(relevant=2).count()
      user_docs['maybedocs'] = tdocs.filter(relevant=3).count()
      user_docs['yesbuts']   = tdocs.filter(relevant=4).count()
      user_docs['checked_percent'] = round((user_docs['reldocs'] + user_docs['irreldocs'] + user_docs['maybedocs']) / user_docs['tdocs'] * 100)
    if query in u.query_set.all():
      user_list.append({
        'username': u.username,
        'email': u.email,
        'onproject': True,
        'user_docs': user_docs
      })
    else:
      user_list.append({
        'username': u.username,
        'email': u.email,
        'onproject': False,
        'user_docs': user_docs
      })

  context = {
    'query': query,
    'tags': list(tags),
    'fields': fields,
    'untagged': untagged,
    'users': user_list,
    'user': request.user
  }

  #add_manually()

  return HttpResponse(template.render(context, request))


##################################################
## User home page

@login_required
def userpage(request):
  template = loader.get_template('snowballing/user.html')
  queries  = sb_Query.objects.filter(users=request.user)

  query_list = []

  for q in queries:
    ndocs           = sb_Doc.objects.filter(query=q).count()
    revdocs         = sb_DocOwnership.objects.filter(query=q,user=request.user).count()
    reviewed_docs   = sb_DocOwnership.objects.filter(query=q,user=request.user,relevant__gt=0).count()
    unreviewed_docs = revdocs - reviewed_docs
    reldocs         = sb_DocOwnership.objects.filter(query=q,user=request.user,relevant=1).count()
    irreldocs       = sb_DocOwnership.objects.filter(query=q,user=request.user,relevant=2).count()
    maybedocs       = sb_DocOwnership.objects.filter(query=q,user=request.user,relevant=3).count()
    yesbuts         = sb_DocOwnership.objects.filter(query=q,user=request.user,relevant=4).count()
    try:
      relevance = round(reldocs/(reldocs+irreldocs)*100)
    except:
      relevance = 0

    query_list.append({
      'id': q.id,
      'title': q.title,
      'ndocs': ndocs,
      'revdocs': revdocs,
      'revieweddocs': reviewed_docs,
      'unreviewed_docs': unreviewed_docs,
      'reldocs': reldocs,
            'maybedocs': maybedocs,
            'yesbuts': yesbuts,
            'relevance': relevance
        })

  query = queries.last()

  context = {
    'user': request.user,
    'queries': query_list,
    'query': query
  }

  return HttpResponse(template.render(context, request))



##################################################
## View all docs
@login_required
def doclist(request,qid):

  template = loader.get_template('snowballing/docs.html')

  if qid == 0 or qid=='0':
    qid = sb_Query.objects.all().last().id

  query = sb_Query.objects.get(pk=qid)
  qdocs = sb_Doc.objects.filter(query__id=qid)
  all_docs = qdocs
  ndocs = all_docs.count()

  docs = list(all_docs[:100].values('sb_wosarticle__ti','sb_wosarticle__ab','sb_wosarticle__py'))

  fields = []

  for f in sb_WoSArticle._meta.get_fields():
    path = "sb_wosarticle__"+f.name
    if f.name !="doc":
      fields.append({"path": path, "name": f.verbose_name})

  for u in User.objects.all():
    path = "sb_docownership__"+u.username
    fields.append({"path": path, "name": u.username})

  for f in sb_DocAuthInst._meta.get_fields():
    path = "sb_docauthinst__"+f.name
    if f.name !="doc" and f.name !="query":
      fields.append({"path": path, "name": f.verbose_name})

  basic_fields = ['Title', 'Abstract', 'Year']

  context = {
    'query': query,
    'docs': docs,
    'fields': fields,
    'basic_fields': basic_fields,
    'ndocs': ndocs
  }

  return HttpResponse(template.render(context, request))



from django.db.models.aggregates import Aggregate
class StringAgg(Aggregate):
  function = 'STRING_AGG'
  template = "%(function)s(%(expressions)s, '%(delimiter)s')"

  def __init__(self, expression, delimiter, **extra):
    super(StringAgg, self).__init__(expression, delimiter=delimiter, **extra)

  def convert_value(self, value, expression, connection, context):
    if not value:
      return ''
    return value



##################################################
## Ajax function, to return sorted docs
@login_required
def sortdocs(request):

  qid         = request.GET.get('qid',None)
  fields      = request.GET.getlist('fields[]',None)
  field       = request.GET.get('field',None)
  sortdir     = request.GET.get('sortdir',None)
  extra_field = request.GET.get('extra_field',None)

  f_fields    = request.GET.getlist('f_fields[]',None)
  f_operators = request.GET.getlist('f_operators[]',None)
  f_text      = request.GET.getlist('f_text[]',None)
  f_join      = request.GET.getlist('f_join[]',None)

  sort_dirs   = request.GET.getlist('sort_dirs[]',None)
  sort_fields = request.GET.getlist('sort_fields[]',None)

  tag_title   = request.GET.get('tag_title',None)

  # get the query
  query = sb_Query.objects.get(pk=qid)

  # filter the docs according to the query
  all_docs  = sb_Doc.objects.filter(query__id=qid)
  filt_docs = sb_Doc.objects.filter(query__id=qid)

  tag_text = ""

  # filter the docs according to the currently active filter
  for i in range(len(f_fields)):
    if i==0:
      joiner = "AND"
      text_joiner = ""
    else:
      joiner = f_join[i-1]
      text_joiner = f_join[i-1]

    if f_operators[i] == "noticontains":
      op = "icontains"
      exclude = True
    else:
      op =  f_operators[i]
      exclude = False

    try:
      kwargs = {
        '{0}__{1}'.format(f_fields[i],op): f_text[i]
      }
      if joiner=="AND":
        if exclude:
          filt_docs = filt_docs.exclude(**kwargs)
        else:
          filt_docs = filt_docs.filter(**kwargs)
      else:
        if exclude:
          filt_docs = filt_docs | all_docs.exclude(**kwargs)
        else:
          filt_docs = filt_docs | all_docs.filter(**kwargs)
      tag_text+= '{0} {1} {2} {3}'.format(text_joiner, f_fields[i], f_operators[i], f_text[i])
    except:
      break

  if tag_title is not None:
    t       = sb_Tag(title=tag_title)
    t.text  = tag_text
    t.query = query
    t.save()
    for doc in filt_docs:
      doc.tag.add(t)
    return(JsonResponse("",safe=False))

  if sortdir=="+":
    sortdir = ""

  fields = tuple(fields)

  single_fields = ['UT']
  mult_fields = []
  users = []
  for f in fields:
    if "sb_docauthinst" in f:
      mult_fields.append(f)
    elif "sb_docownership" in f:
      users.append(f)
    else:
      single_fields.append(f)
  single_fields = tuple(single_fields)
  mult_fields_tuple = tuple(mult_fields)

  if len(users) > 0:
    uname = users[0].split("__")[1]
    user  = User.objects.get(username=uname)
    null_filter = 'sb_docownership__relevant__isnull'
    reldocs   = filt_docs.filter(sb_docownership__user=user,sb_docownership__query=query).values("UT")
    filt_docs = filt_docs.filter(UT__in=reldocs)

    #print(len(filt_docs))

  if sort_dirs is not None:
    order_by = ('-PY','UT')
    if len(sort_dirs) > 0:
      order_by = []
    for s in range(len(sort_dirs)):
      sortdir = sort_dirs[s]
      field = sort_fields[s]
      if sortdir=="+":
        sortdir=""
      null_filter = field+'__isnull'
      order_by.append(sortdir+field)
      filt_docs = filt_docs.filter(**{null_filter:False})

    docs = filt_docs.order_by(*order_by).values(*single_fields)[:100]

    if len(mult_fields) > 0:
      for d in docs:
        for m in range(len(mult_fields)):
          f = (mult_fields_tuple[m],)
          adoc = sb_Doc.objects.filter(UT=d['UT']).values_list(*f).order_by('sb_docauthinst__position')
          
          d[mult_fields[m]] = "; <br/>".join(str(x) for x in (list(itertools.chain(*adoc))))

  for d in docs:
    if len(users) > 0:
      for u in users:
        uname = u.split("__")[1]
        print(uname)
        doc = sb_Doc.objects.get(UT=d['UT'])
        print(d['UT'])
        do = sb_DocOwnership.objects.filter(doc_id=d['UT'],user__username=uname)
        if do.count() > 0:
          d[u] = do.first().relevant
          tag = str(do.first().tag.id)
          user = str(User.objects.filter(username=uname).first().id)
          d[u] = '<span class="relevant_cycle" data-user='+user+' data-tag='+tag+' data-id='+d['UT']+' onclick="cyclescore(this)">'+str(d[u])+'</span>'
    try:
      d['sb_wosarticle__di'] = '<a target="_blank" href="http://dx.doi.org/'+d['sb_wosarticle__di']+'">'+d['sb_wosarticle__di']+'</a>'
    except:
      pass

  response = {
    'data': list(docs),
    'n_docs': filt_docs.count()
  }

  template = loader.get_template('snowballing/doc.html')
  context = {}

  return JsonResponse(response,safe=False)

def cycle_score(request):

  qid    = int(request.GET.get('qid',None))
  score  = int(request.GET.get('score',None))
  doc_id = request.GET.get('doc_id',None)
  user   = int(request.GET.get('user',None))
  tag    = int(request.GET.get('tag',None))


  if score == 4:
    new_score = 0
  else:
    new_score = score+1
  docown = sb_DocOwnership.objects.filter(sb_query__id=qid, sb_doc__UT=doc_id, user__id=user, sb_tag__id=tag).first()
  docown.relevant = new_score
  docown.save()

  return HttpResponse("")

@login_required
@user_passes_test(lambda u: u.is_superuser)
def activate_user(request):

  qid = request.GET.get('qid',None)
  checked = request.GET.get('checked',None)
  user = request.GET.get('user',None)

  query = sb_Query.objects.get(pk=qid)
  user = User.objects.get(username=user)

  if checked=="true":
    query.users.add(user)
    query.save()
    response=1
  else:
    response=-1
    query.users.remove(user)

  return JsonResponse(response,safe=False)

def update_criteria(request):
  qid      = request.GET.get('qid',None)
  criteria = request.POST['criteria']

  query = sb_Query.objects.get(pk=qid)
  query.criteria = criteria
  query.save()

  return HttpResponseRedirect(reverse('snowballing:query', kwargs={'qid': qid}))

def assign_docs(request):
  qid      = request.GET.get('qid',None)
  users    = request.GET.getlist('users[]',None)
  tags     = request.GET.getlist('tags[]',None)
  tagdocs  = request.GET.getlist('tagdocs[]',None)
  docsplit = request.GET.get('docsplit',None)

  print(docsplit)

  query = sb_Query.objects.get(pk=qid)

  user_list = []

  for user in users:
    user_list.append(User.objects.get(username=user))


  for tag in range(len(tags)):
    t      = sb_Tag.objects.get(pk=tags[tag])
    docs   = sb_Doc.objects.filter(query=query,tag=t)
    ssize  = int(tagdocs[tag])
    sample = docs.order_by('?')[:ssize]
    for s in range(ssize):
      doc = sample[s]
      if docsplit=="true":
        user   = user_list[s % len(user_list)]
        docown = sb_DocOwnership(doc=doc,query=query,user=user,tag=t)
        docown.save()
      else:
        for user in user_list:
          docown = sb_DocOwnership(doc=doc,query=query,user=user,tag=t)
          docown.save()

    return HttpResponse("bla")

import re

def check_docs(request,qid):

  query = sb_Query.objects.get(pk=qid)
  user  = request.user
  docs  = sb_DocOwnership.objects.filter(query=query,user=user.id,relevant=0)


  tdocs = sb_Doc.objects.filter(query=query,users=user.id).count()
  sdocs = sb_Doc.objects.filter(query=query,users=user.id, sb_docownership__relevant__gt=0).count()

  ndocs = docs.count()

  try:
    doc_id = docs.first().doc_id
  except:
    return HttpResponseRedirect(reverse('snowballing:userpage'))

  doc      = sb_Doc.objects.filter(UT=doc_id).first()
  authors  = sb_DocAuthInst.objects.filter(doc=doc)
  abstract = highlight_words(doc.content,query.text)
  title    = highlight_words(doc.wosarticle.ti,query.text)

  template = loader.get_template('snowballing/doc.html')
  context = {
    'query': query,
    'doc': doc,
    'ndocs': ndocs,
    'user': user,
    'authors': authors,
    'tdocs': tdocs,
    'sdocs': sdocs,
    'abstract': abstract,
    'title': title
  }
  
  return HttpResponse(template.render(context, request))

def back_review(request,qid):
  query = sb_Query.objects.get(pk=qid)
  user  = request.user
  docs  = sb_DocOwnership.objects.filter(sb_query=query,user=user.id,relevant__gt=0)
  tdocs = docs.count() - 1

  return HttpResponseRedirect(reverse('snowballing:review_docs', kwargs={'qid': qid,'d': tdocs}))

def review_docs(request,qid,d=0):
  d     = int(d)
  query = sb_Query.objects.get(pk=qid)
  user  = request.user

  docs = sb_DocOwnership.objects.filter(query=query,user=user.id,relevant__gt=0)

  tdocs = docs.count()
  sdocs = d

  ndocs = docs.count()
  try:
    doc_id = docs[d].doc_id
  except:
    return HttpResponseRedirect(reverse('snowballing:userpage'))

  doc      = sb_Doc.objects.filter(UT=doc_id).first()
  authors  = sb_DocAuthInst.objects.filter(doc=doc)
  abstract = highlight_words(doc.content,query.text)
  title    = highlight_words(doc.wosarticle.ti,query.text)

  template = loader.get_template('snowballing/doc.html')
  context = {
    'query': query,
    'doc': doc,
    'ndocs': ndocs,
    'user': user,
    'authors': authors,
    'tdocs': tdocs,
    'sdocs': sdocs,
    'abstract': abstract,
    'title': title
  }

  return HttpResponse(template.render(context, request))


def maybe_docs(request,qid,d=0):
  d     = int(d)
  query = sb_Query.objects.get(pk=qid)
  user  = request.user

  docs = sb_DocOwnership.objects.filter(query=query,user=user.id,relevant=3)

  tdocs = docs.count()
  sdocs = d

  ndocs    = docs.count()
  doc_id   = docs[d].doc_id
  doc      = sb_Doc.objects.filter(UT=doc_id).first()
  authors  = sb_DocAuthInst.objects.filter(doc=doc)
  abstract = highlight_words(doc.content,query.text)
  title    = highlight_words(doc.wosarticle.ti,query.text)

  template = loader.get_template('snowballing/doc.html')
  context = {
    'query': query,
    'doc': doc,
    'ndocs': ndocs,
    'user': user,
    'authors': authors,
    'tdocs': tdocs,
    'sdocs': sdocs,
    'abstract': abstract,
    'title': title
  }

  return HttpResponse(template.render(context, request))

def do_review(request):

  qid    = request.GET.get('query',None)
  doc_id = request.GET.get('doc',None)
  d      = request.GET.get('d',None)

  doc   = sb_Doc.objects.get(pk=doc_id)
  query = sb_Query.objects.get(pk=qid)
  user  = request.user

  docown = sb_DocOwnership.objects.filter(doc=doc,query=query,user=user).order_by("relevant").first()

  docown.relevant=d
  docown.save()

  time.sleep(1)

  return HttpResponse("")

def remove_assignments(request):
  qid = request.GET.get('qid',None)
  query = sb_Query.objects.get(pk=qid)
  todelete = sb_DocOwnership.objects.filter(query=query)
  sb_DocOwnership.objects.filter(query=int(qid)).delete()

  return HttpResponse("")


from django.contrib.auth import logout
def logout_view(request):
  logout(request)
  # Redirect to a success page.
  #return HttpResponse("logout")
  return HttpResponseRedirect(reverse('snowballing:index'))

def add_manually():
  qid = 48
  tag = 18
  user = User.objects.get(username="fuss")
  sb_DocOwnership.objects.filter(user=user).delete()
  query = sb_Query.objects.get(id=qid)
  t = sb_Tag.objects.get(pk=tag)
  docs = sb_Doc.objects.filter(sb_docownership__query=query,sb_docownership__tag=t).distinct()
  for doc in docs:
    docown = sb_DocOwnership(sb_doc=doc,sb_query=query,user=user,sb_tag=t)
    docown.save()

  return HttpResponse("")

def highlight_words(s,query):
  qwords = re.findall('\w+',query)
  nots = ["TS","AND","NOT","NEAR","OR","and"]
  qwords = set([x for x in qwords if x not in nots])
  abstract = []
  for word in s.split(" "):
    if word in qwords:
      abstract.append('<span class="t1">'+word+'</span>')
    else:
      abstract.append(word)

  return(" ".join(abstract))





