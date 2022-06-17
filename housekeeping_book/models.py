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

    family = models.ForeignKey(Family, on_delete=models.CASCADE, verbose_name='가족')
    code = models.IntegerField(verbose_name='계정코드')
    account = models.CharField(max_length=2, verbose_name='계정', choices=ACCOUNT_CHOICES)
    title = models.CharField(max_length=30, verbose_name='계정과목')

    def __str__(self):
        return self.title

class Slit(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, verbose_name='가족')
    date = models.DateField(verbose_name='날짜')
    memo = models.CharField(max_length=50, verbose_name='적요')

    def __str__(self):
        return '{}/{}/{}'.format(self.family, self.date, self.memo)

class Tag(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, verbose_name='가족')
    name = models.CharField(max_length=30, verbose_name='꼬리표')

    def __str__(self):
        return self.name

class Ledger(models.Model):
    slit = models.ForeignKey(Slit, on_delete=models.CASCADE, verbose_name='전표')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, verbose_name='계정과목')
    tag = models.ForeignKey(Tag, on_delete=models.PROTECT, verbose_name='꼬리표')
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='금액')

    def __str__(self):
        return '{}/{}/{}/{}'.format(self.slit, self.account, self.tag, self.amount)