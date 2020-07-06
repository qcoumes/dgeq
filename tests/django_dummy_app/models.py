from django.db import models



class Continent(models.Model):
    name = models.CharField(max_length=255, unique=True)
    
    
    def __str__(self):
        return f"{self.name}"



class Region(models.Model):
    name = models.CharField(max_length=255, unique=True)
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE, related_name="regions")
    
    
    def __str__(self):
        return f"{self.name}"



class Country(models.Model):
    name = models.CharField(max_length=255, unique=True)
    area = models.BigIntegerField()
    population = models.BigIntegerField()
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="countries")
    
    
    class Meta:
        verbose_name_plural = "Countries"
    
    
    def __str__(self):
        return f"{self.name}"



class River(models.Model):
    name = models.CharField(max_length=255, unique=True)
    discharge = models.IntegerField(null=True)
    length = models.IntegerField()
    countries = models.ManyToManyField(Country, related_name="rivers")
    
    
    def __str__(self):
        return f"{self.name}"



class Forest(models.Model):
    name = models.CharField(max_length=255, unique=True)
    area = models.BigIntegerField()
    countries = models.ManyToManyField(Country, related_name="forests")
    
    
    def __str__(self):
        return f"{self.name}"



class Mountain(models.Model):
    name = models.CharField(max_length=255, unique=True)
    height = models.IntegerField()
    countries = models.ManyToManyField(Country, related_name="mountains")
    
    
    def __str__(self):
        return f"{self.name}"



class Disaster(models.Model):
    event = models.CharField(max_length=255)
    date = models.DateTimeField()
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="disasters")
    source = models.TextField()
    comment = models.TextField()
    
    
    def __str__(self):
        s = f"{self.event} - {self.country} - {self.date.strftime('%Y-%m-%d')}"
        return s
