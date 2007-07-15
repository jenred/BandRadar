from turbogears import widgets as w
from turbogears import validators as v
from cgi import escape
from bandradar.imports import google

w.register_static_directory("br", "bandradar/widgets")

class ExtJSLink(w.JSLink):
    def update_params(self, d):
        super(ExtJSLink, self).update_params(d)
        d["link"] = self.name

class GoogleMapWidget(w.Widget):
    template = """
    <div xmlns:py="http://purl.org/kid/ns#" py:if="venue.geocode_lat" id="map" style="width: ${width}px; height: ${height}px">
        <script type="text/javascript">
            var map_lat = ${venue.geocode_lat}
            var map_lon = ${venue.geocode_lon}
            addLoadEvent(gmap_load)
            window.onunload = GUnload()
        </script>
    </div>"""
    javascript = [w.mochikit]
    params = ["venue", "key", "width", "height"]

    def __init__(self, width=500, height=350, **kw):
        key = kw.pop("key", "abcdef")
        js1 = ExtJSLink(None, "http://maps.google.com/maps?file=api&v=2&key=%s" % key)
        js2 = w.JSLink("br", 'javascript/googlemap.js')
        self.javascript.append(js1)
        self.javascript.append(js2)
        self.width = width
        self.height = height

googlemap = GoogleMapWidget(key=google.key, width=350, height=300)

class ButtonWidget(w.Widget):
    template = "bandradar.widgets.templates.button"
    params = ['label', 'action']

class ArtistListWidget(w.Widget):
    template = "bandradar.widgets.templates.artistlist"
    params = ['artists', 'emph_new']

    emph_new = False

    def get_list(self, artists, emph_new):
        artists = artists.orderBy('name')
        if not artists.count():
            artisthtml = "None"
        else:
            app_htmlstr = "<a href=\"/artists/%s\">%s</a>"
            if emph_new:
                unapp_htmlstr = "<strong>%s</strong>"
            else:
                unapp_htmlstr = "%s"
            artist_html_list = []
            artist_html_list.extend([ app_htmlstr % (a.id, escape(a.name)) for a in artists if a.approved])
            artist_html_list.extend([ unapp_htmlstr % escape(a.name) for a in artists if not a.approved])
            artisthtml = ", ".join(artist_html_list)
        return artisthtml

artist_list = ArtistListWidget()

class TrackButtonWidget(w.Widget):
    template = "bandradar.widgets.templates.trackbutton"
    javascript = [w.mochikit, w.JSLink("br", 'javascript/trackbutton.js')]
    params = ["id", "action", "tracked", "text"]
    text = dict(off="Track", on="Untrack")

    def track_str(self, tracked):
        if tracked:
            return "tracked"
        return ""

track_button = TrackButtonWidget()

class AutoCompleteValidator(v.Schema):
    def _to_python(self, value, state):
        text = value['text']
        value['text'] = v.NotEmpty(strip=True).to_python(text)
        return value

class BRAutoCompleteField(w.AutoCompleteField):
    def __init__(self, search_controller, label="", **kw):
        super(w.AutoCompleteField, self).__init__(
            label=label,
            search_controller=search_controller,
            search_param="name",
            result_name="results",
            only_suggest=True,
            validator=AutoCompleteValidator(),
            attrs=dict(size=20), **kw)

# Fix TG CalendarDatePicker, which returns a datetime, not a date
class BRCalendarDatePicker(w.CalendarDatePicker):
    def __init__(self, **kw):
        super(BRCalendarDatePicker, self).__init__(**kw)
        self.validator = v.DateConverter(format=self.format,
            not_empty=self.not_empty)

