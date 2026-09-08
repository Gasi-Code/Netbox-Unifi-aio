"""
Django sucht Modelle standardmaessig unter <app>/models.py. Da wir die
Modelle bewusst nach Zustaendigkeit auf base/, network/, design/ aufgeteilt
haben (nicht alles in eine Datei), müssen sie hier re-exportiert werden -
sonst findet Django sie nicht und "python manage.py makemigrations" sieht
sie schlicht nicht.

Ausserdem braucht JEDES Modell unten in seiner Meta-Klasse
`app_label = 'netbox_unifi_aio'`, weil es sonst versucht, sich selbst
dem Package zuzuordnen, in dem die Datei liegt (also "base"/"network"/
"design" statt "netbox_unifi_aio") - das wuerde NetBox nicht finden.
"""
from .base.models import UCKConsole, SyncLog  # noqa: F401
from .network.models import UnifiDevice  # noqa: F401
from .design.models import UnifiFloorplanMap  # noqa: F401
