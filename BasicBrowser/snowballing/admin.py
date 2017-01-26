from django.contrib import admin
from .models import * 

# Register your models here.
admin.site.register(sb_Query)
admin.site.register(sb_Tag)
admin.site.register(sb_Doc)
admin.site.register(sb_DocOwnership)
admin.site.register(sb_DocAuthInst)
admin.site.register(sb_DocCites)
admin.site.register(sb_WoSArticle)
