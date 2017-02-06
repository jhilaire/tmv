from django.conf.urls import url


from . import views

app_name = 'scoping'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^user$', views.userpage, name='userpage'),
    url(r'^doquery$', views.doquery, name='doquery'),
    url(r'^update_criteria$', views.update_criteria, name='update_criteria'),
    url(r'^dodocadd$', views.dodocadd, name='dodocadd'),
    url(r'^querying/(?P<qid>[0-9]+)$', views.querying, name='querying'),
    url(r'^query/(?P<qid>[0-9]+)$', views.query, name='query'),
    url(r'^docs/(?P<qid>[0-9]+)$', views.doclist, name='doclist'),
    url(r'^sort_docs$', views.sortdocs, name='sortdocs'),
    url(r'^cycle_score$', views.cycle_score, name='cycle_score'),
    url(r'^activate_user$', views.activate_user, name='activate_user'),
 	url(r'^assign_docs$', views.assign_docs, name='assign_docs'),
 	url(r'^remove_assignments$', views.remove_assignments, name='remove_assignments'),
 	url(r'^do_review$', views.do_review, name='do_review'),
	url(r'^check/(?P<qid>[0-9]+)$', views.check_docs, name='check_docs'),
	url(r'^back_review/(?P<qid>[0-9]+)$', views.back_review, name='back_review'),	
	url(r'^review/(?P<qid>[0-9]+)$', views.review_docs, name='review_docs'),
	url(r'^review/(?P<qid>[0-9]+)/(?P<d>[0-9]+)$', views.review_docs, name='review_docs'),
	url(r'^maybe/(?P<qid>[0-9]+)/(?P<d>[0-9]+)$', views.maybe_docs, name='maybe_docs'),
]
