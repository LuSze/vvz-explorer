from django.db import models


class StudyTrack(models.Model):
    name = models.CharField(max_length=255, unique=True)
    short_name = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'study_tracks'

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255)
    level = models.IntegerField(choices=[(1, 'Level 1'), (2, 'Level 2'), (3, 'Level 3')])
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    vvz_id = models.IntegerField(unique=True, null=True, blank=True)

    class Meta:
        db_table = 'categories'
        ordering = ['level', 'name']

    def __str__(self):
        return f"{'  ' * (self.level - 1)}{self.name}"


class Lecturer(models.Model):
    name = models.CharField(max_length=255, unique=True)
    email = models.EmailField(blank=True)
    department = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'lecturers'
        ordering = ['name']

    def __str__(self):
        return self.name


class Lecture(models.Model):
    number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=500)
    type = models.CharField(max_length=100, blank=True)
    ects = models.CharField(max_length=20, blank=True)
    language = models.CharField(max_length=50, blank=True)
    semester = models.CharField(max_length=20)
    detail_url = models.URLField(blank=True)

    abstract = models.TextField(blank=True)
    content = models.TextField(blank=True)
    learning_objective = models.TextField(blank=True)
    lecture_notes = models.TextField(blank=True)
    literature = models.TextField(blank=True)
    performance_assessment = models.TextField(blank=True)

    lecturers = models.ManyToManyField(Lecturer, related_name='lectures', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lectures'
        ordering = ['semester', 'number']
        indexes = [
            models.Index(fields=['semester']),
            models.Index(fields=['number']),
        ]

    def __str__(self):
        return f"{self.number}: {self.title}"


class LectureCategoryLink(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='category_links')
    category_l1 = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='lecture_links_l1', null=True, blank=True)
    category_l2 = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='lecture_links_l2', null=True, blank=True)
    category_l3 = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='lecture_links_l3', null=True, blank=True)
    study_track = models.ForeignKey(StudyTrack, on_delete=models.CASCADE, related_name='lecture_links', null=True, blank=True)

    class Meta:
        db_table = 'lecture_category_links'
        unique_together = ['lecture', 'study_track']

    def __str__(self):
        return f"{self.lecture.number} -> {self.category_l1 or '—'} > {self.category_l2 or '—'} > {self.category_l3 or '—'}"


class LectureEmbedding(models.Model):
    """Vector embeddings for semantic search."""
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='embeddings')
    field_name = models.CharField(max_length=50, choices=[
        ('title', 'Title'),
        ('abstract', 'Abstract'),
        ('content', 'Content'),
        ('learning_objective', 'Learning Objective'),
        ('lecture_notes', 'Lecture Notes'),
        ('literature', 'Literature'),
    ])
    vector = models.BinaryField()  # Stored as binary blob

    class Meta:
        db_table = 'lecture_embeddings'
        unique_together = ['lecture', 'field_name']
        indexes = [
            models.Index(fields=['field_name']),
        ]

    def __str__(self):
        return f"{self.lecture.number} - {self.field_name}"