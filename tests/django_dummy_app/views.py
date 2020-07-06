from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

import dgeq
from . import models



@require_GET
def continent(request: HttpRequest):
    q = dgeq.GenericQuery(models.Continent, request.GET)
    return JsonResponse(q.evaluate())



@require_GET
def region(request: HttpRequest):
    q = dgeq.GenericQuery(models.Region, request.GET)
    return JsonResponse(q.evaluate())



@require_GET
def country(request: HttpRequest):
    q = dgeq.GenericQuery(models.Country, request.GET)
    return JsonResponse(q.evaluate())



@require_GET
def river(request: HttpRequest):
    q = dgeq.GenericQuery(models.River, request.GET)
    return JsonResponse(q.evaluate())



@require_GET
def mountain(request: HttpRequest):
    q = dgeq.GenericQuery(models.Mountain, request.GET)
    return JsonResponse(q.evaluate())



@require_GET
def forest(request: HttpRequest):
    q = dgeq.GenericQuery(models.Forest, request.GET)
    return JsonResponse(q.evaluate())



@require_GET
def disaster(request: HttpRequest):
    q = dgeq.GenericQuery(models.Disaster, request.GET)
    return JsonResponse(q.evaluate())
