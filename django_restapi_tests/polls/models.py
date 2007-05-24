from django.db import models
from django.utils.translation import gettext_lazy as _

class Poll(models.Model):
    question = models.CharField(maxlength=200)
    pub_date = models.DateTimeField(_('date published'))
    class Admin:
        pass
    def __str__(self):
        return self.question

class Choice(models.Model):
    poll = models.ForeignKey(Poll)
    choice = models.CharField(maxlength=200)
    votes = models.IntegerField()
    class Admin:
        pass
    def __str__(self):
        return self.choice