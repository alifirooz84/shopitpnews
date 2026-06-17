from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from engagement.models import FavoriteListing

from .forms import ListingForm
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
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = FavoriteListing.objects.filter(user=request.user, listing=listing).exists()
    return render(request, "listings/ad_detail.html", {"listing": listing, "is_favorited": is_favorited})


@login_required
def my_listings(request):
    listings = request.user.listings.all().order_by("-created_at")
    return render(request, "listings/my_listings.html", {"listings": listings})


@login_required
def listing_create(request):
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            listing.seller_name = request.user.get_full_name() or str(request.user)
            listing.seller_title = request.user.get_role_display() if request.user.role else "فروشنده جوجه بازار"
            listing.is_verified = request.user.is_phone_verified
            listing.save()
            messages.success(request, "آگهی شما ثبت شد و در لیست آگهی‌ها نمایش داده می‌شود.")
            return redirect(listing.get_absolute_url())
    else:
        initial = {
            "province": request.user.province,
            "city": request.user.city,
            "health_status": "واکسینه شده",
            "parent_flock_age": "۳۷-۵۰",
            "vaccination_status": "کامل",
        }
        form = ListingForm(initial=initial)
    return render(request, "listings/ad_form.html", {"form": form, "mode": "create"})


@login_required
def listing_update(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    if listing.status == Listing.Status.SOLD:
        messages.error(request, "آگهی فروخته شده قابل ویرایش نیست.")
        return redirect("listings:mine")
    if request.method == "POST":
        form = ListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.seller_name = request.user.get_full_name() or str(request.user)
            updated.seller_title = request.user.get_role_display() if request.user.role else updated.seller_title
            updated.save()
            messages.success(request, "آگهی با موفقیت ویرایش شد.")
            return redirect(updated.get_absolute_url())
    else:
        form = ListingForm(instance=listing)
    return render(request, "listings/ad_form.html", {"form": form, "listing": listing, "mode": "edit"})


@login_required
def listing_delete(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    if request.method == "POST":
        listing.status = Listing.Status.INACTIVE
        listing.is_featured = False
        listing.save(update_fields=["status", "is_featured", "updated_at"])
        messages.success(request, "آگهی از نمایش عمومی حذف شد.")
        return redirect("listings:mine")
    return render(request, "listings/ad_confirm_delete.html", {"listing": listing})
