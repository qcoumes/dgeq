from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

import dgeq
from . import models



@require_GET
def continent(request: HttpRequest):
    q = dgeq.GenericQuery(request.user, models.Continent, request.GET)
    return JsonResponse(q.evaluate())



@require_GET
def region(request: HttpRequest):
    q = dgeq.GenericQuery(request.user, models.Region, request.GET)
    return JsonResponse(q.evaluate())



@require_GET
def country(request: HttpRequest):
    q = dgeq.GenericQuery(request.user, models.Country, request.GET)
    return JsonResponse(q.evaluate())



@require_GET
def river(request: HttpRequest):
    q = dgeq.GenericQuery(request.user, models.River, request.GET)
    return JsonResponse(q.evaluate())



@require_GET
def mountain(request: HttpRequest):
    q = dgeq.GenericQuery(request.user, models.Mountain, request.GET)
    return JsonResponse(q.evaluate())



@require_GET
def forest(request: HttpRequest):
    q = dgeq.GenericQuery(request.user, models.Forest, request.GET)
    return JsonResponse(q.evaluate())



@require_GET
def disaster(request: HttpRequest):
    q = dgeq.GenericQuery(request.user, models.Disaster, request.GET)
    return JsonResponse(q.evaluate())
