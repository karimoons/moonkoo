from django.db import models
from django.contrib.auth.models import User

class Family(models.Model):
    name = models.CharField(max_length=30, verbose_name='가족이름')
    member = models.ManyToManyField(User)

    def __str__(self):
        return self.name