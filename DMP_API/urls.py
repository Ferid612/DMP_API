from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', include('DMP_APP.urls')),
    path('rfp/', include('DMP_APP.urls_rfp')),
    path('rfp_2/', include('DMP_APP.urls_rfp_2')),

    path('region/', include('DMP_APP.urls_region')),
    path('pricebook/', include('DMP_APP.urls_pricebook')),

]
    

urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)