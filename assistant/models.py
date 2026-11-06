from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class KnowledgeEntry(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDIENTE', 'Pendiente'
        PUBLISHED = 'PUBLICADA', 'Publicada'

    question = models.CharField('pregunta', max_length=400)
    answer = models.TextField('respuesta', blank=True)
    status = models.CharField('estado', max_length=10, choices=Status.choices, default=Status.PENDING)
    asked_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='usuario que consultó',
                                 on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField('fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('fecha de actualización', auto_now=True)
    question_key = models.CharField(max_length=64, unique=True, editable=False, blank=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        verbose_name = 'entrada de conocimiento'
        verbose_name_plural = 'base de conocimiento'

    def __str__(self):
        return self.question

    def clean(self):
        from .services import question_key

        super().clean()
        self.question = self.question.strip()
        self.answer = self.answer.strip()
        self.question_key = question_key(self.question)
        errors = {}
        if self.status == self.Status.PUBLISHED and not self.answer:
            errors['answer'] = 'Escribe una respuesta antes de publicar.'
        if KnowledgeEntry.objects.filter(question_key=self.question_key).exclude(pk=self.pk).exists():
            errors['question'] = 'Ya existe una entrada equivalente; edita esa entrada.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
