from django.db.models import Avg, Sum
from django.shortcuts import get_object_or_404, render

from .models import Listing, MarketPrice


def dashboard(request):
    active = Listing.objects.filter(status=Listing.Status.ACTIVE)
    context = {
        "market_prices": MarketPrice.objects.all(),
        "featured_listings": active.filter(is_featured=True)[:5],
        "recent_listings": active[:6],
        "today_volume": active.aggregate(total=Sum("quantity"))["total"] or 0,
        "average_price": int(active.aggregate(avg=Avg("price_per_chick"))["avg"] or 0),
    }
    return render(request, "dashboard/index.html", context)


def listing_list(request):
    listings = Listing.objects.filter(status=Listing.Status.ACTIVE).select_related("seller")
    breed = request.GET.get("breed")
    province = request.GET.get("province")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    delivery_date = request.GET.get("delivery_date")

    if breed:
        listings = listings.filter(breed__icontains=breed)
    if province:
        listings = listings.filter(province=province)
    if min_price:
        listings = listings.filter(price_per_chick__gte=min_price)
    if max_price:
        listings = listings.filter(price_per_chick__lte=max_price)
    if delivery_date:
        listings = listings.filter(delivery_date=delivery_date)

    context = {
        "listings": listings,
        "breeds": Listing.objects.values_list("breed", flat=True).distinct().order_by("breed"),
        "provinces": Listing.objects.values_list("province", flat=True).distinct().order_by("province"),
        "filters": request.GET,
    }
    return render(request, "listings/ad_list.html", context)


def listing_detail(request, pk):
    listing = get_object_or_404(Listing.objects.select_related("seller"), pk=pk)
    return render(request, "listings/ad_detail.html", {"listing": listing})
