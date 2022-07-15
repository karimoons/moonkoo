from django.db import models
from django.contrib.auth.models import User

class Family(models.Model):
    name = models.CharField(max_length=30, verbose_name='가족이름', unique=True)
    member = models.ManyToManyField(User)

    def __str__(self):
        return self.name

class Account(models.Model):
    ACCOUNT_CHOICES = [
        ('A', '자산'),
        ('L', '부채'),
        ('C', '자본'),
        ('I', '수익'),
        ('E', '비용'),
    ]

    CLASSIFICATION_CHOICES = [
        ('C', '유동'),
        ('NC', '비유동'),
        ('R', '실현'),
        ('UR', '미실현'),
        ('O', '경상'),
        ('NO', '비경상'),
    ]

    family = models.ForeignKey(Family, on_delete=models.CASCADE, verbose_name='가족')
    code = models.IntegerField(verbose_name='계정코드')
    account = models.CharField(max_length=2, verbose_name='계정', choices=ACCOUNT_CHOICES)
    classification = models.CharField(max_length=2, verbose_name='분류', choices=CLASSIFICATION_CHOICES)
    title = models.CharField(max_length=30, verbose_name='계정과목')

    modified_date = models.DateTimeField(auto_now=True, editable=False, null=True, verbose_name='최종수정일시')
    modified_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='최종수정자')

    def __str__(self):
        return self.title
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields = ['family', 'code'],
                name = 'one code per one family',
            ),
            models.UniqueConstraint(
                fields = ['family', 'title'],
                name = 'one title per one family',
            )
        ]

class Slit(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, verbose_name='가족')
    date = models.DateField(verbose_name='날짜')
    memo = models.CharField(max_length=50, verbose_name='적요')

    modified_date = models.DateTimeField(auto_now=True, editable=False, null=True, verbose_name='최종수정일시')
    modified_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='최종수정자')

    def __str__(self):
        return '{}/{}/{}'.format(self.family, self.date, self.memo)

class Tag(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, verbose_name='가족')
    name = models.CharField(max_length=30, verbose_name='꼬리표')

    modified_date = models.DateTimeField(auto_now=True, editable=False, null=True, verbose_name='최종수정일시')
    modified_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='최종수정자')

    def __str__(self):
        return self.name
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields = ['family', 'name'],
                name = 'one name per one family',
            )
        ]

class Ledger(models.Model):
    slit = models.ForeignKey(Slit, on_delete=models.CASCADE, verbose_name='전표')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, verbose_name='계정과목')
    tag = models.ForeignKey(Tag, on_delete=models.PROTECT, verbose_name='꼬리표')
    amount = models.DecimalField(max_digits=13, decimal_places=0, verbose_name='금액')
    opposite_account = models.ForeignKey(Account, on_delete=models.PROTECT, verbose_name='상대계정과목', related_name='opposite_ledger')
    opposite_tag = models.ForeignKey(Tag, on_delete=models.PROTECT, verbose_name='상대계정꼬리표', related_name='opposite_ledger')

    def __str__(self):
        return '{}/{}/{}/{}'.format(self.slit, self.account, self.tag, self.amount)