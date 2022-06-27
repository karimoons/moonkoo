from django.contrib import admin
from .models import Family, Account, Tag, Slit, Ledger

admin.site.register(Family)

class AccountAdmin(admin.ModelAdmin):
    list_display = ('family', 'code', 'account', 'title')
admin.site.register(Account, AccountAdmin)

class TagAdmin(admin.ModelAdmin):
    list_display = ('family', 'name')
admin.site.register(Tag, TagAdmin)

class LedgerInline(admin.StackedInline):
    model = Ledger
    extra = 2

class SlitAdmin(admin.ModelAdmin):
    inlines = [LedgerInline]
admin.site.register(Slit, SlitAdmin)