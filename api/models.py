import json
from django.db import models


class SafeJSONField(models.JSONField):
    """
    JSONField that safely handles both string and already-deserialized values
    from the database (e.g. PostgreSQL drivers may return dicts directly).
    """
    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        if not isinstance(value, (str, bytes)):
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []


class Source(models.Model):
    spider_id   = models.AutoField(primary_key=True)
    spider_name = models.CharField(max_length=255, unique=True)
    spider_domain = models.CharField(max_length=255)

    class Meta:
        db_table = "source_table"

    def __str__(self):
        return self.spider_name


class History(models.Model):
    history_id = models.AutoField(primary_key=True)
    site_id    = models.ForeignKey(
        Source,
        on_delete=models.CASCADE,
        db_column="site_id",
        related_name="histories",
    )
    isbn            = models.CharField(max_length=255)
    available_books = models.IntegerField(default=0)
    sold_books      = models.IntegerField(default=0)

    class Meta:
        db_table = "history_table"
        constraints = [
            models.UniqueConstraint(fields=["site_id", "isbn"], name="uq_siteid_isbn")
        ]

    def __str__(self):
        return f"{self.isbn} - {self.site_id}"


class Detail(models.Model):
    # ── Interest flag ──────────────────────────────────────────────────────
    PENDING        = "pending"
    INTERESTED     = "interested"
    NOT_INTERESTED = "not_interested"

    INTEREST_CHOICES = [
        (PENDING,        "Pending"),
        (INTERESTED,     "Interested"),
        (NOT_INTERESTED, "Not Interested"),
    ]
    # ───────────────────────────────────────────────────────────────────────

    detail_id   = models.AutoField(primary_key=True)
    history     = models.ForeignKey(
        History,
        on_delete=models.CASCADE,
        db_column="history_id",
        related_name="details",
    )
    isbn         = models.CharField(max_length=255)
    date_scraped = models.DateField(auto_now_add=True)
    first_seen   = models.DateField(auto_now_add=True)
    site_id      = models.IntegerField(null=True, blank=True)
    name         = models.TextField()
    price        = models.FloatField()
    seller       = models.TextField()
    condition    = models.TextField()
    editorial    = models.TextField()
    images       = SafeJSONField()
    url          = models.TextField(unique=True)
    availability = models.BooleanField(default=True)
    interest = models.CharField(max_length=20, choices=INTEREST_CHOICES, default=PENDING, db_index=True,)
    contact = models.BooleanField(default=False)

    class Meta:
        db_table = "details_table"

    def __str__(self):
        return self.name