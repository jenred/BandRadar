import cherrypy
import turbogears
from turbogears import controllers, expose, redirect
from turbogears import identity
from turbogears import widgets as w
from turbogears import validators as v
from model import Event, Venue, Artist, Source, hub
from sqlobject import SQLObjectNotFound
from datetime import date, datetime
from bandradar.widgets import artist_list
from bandradar.imports import MBL
from bandradar.imports import WWBL
from bandradar.imports import pollstar
from bandradar.imports import br_upcoming as br
from bandradar.imports import lastfm
from bandradar.imports import ticketswest


class Merc(w.WidgetsList):
    url = w.TextField(label="URL", attrs=dict(size=60),
        validator=v.All(v.NotEmpty, v.URL))

class WWeek(w.WidgetsList):
    thedate = w.CalendarDatePicker(label="Date")
    do_week = w.CheckBox(label="Import whole week")

merc_form = w.TableForm(fields=Merc(), name="merc", submit_text="Go")
wweek_form = w.TableForm(fields=WWeek(), name="wweek", submit_text="Go")


class Importers(controllers.Controller, identity.SecureResource):
    require = identity.in_group("admin")

    @expose(template=".templates.webimport")
    def webimport(self, tg_errors=None):
        if tg_errors:
            turbogears.flash("Entry error")
        return dict(merc_form=merc_form, wweek_form=wweek_form)

    @expose()
    @turbogears.validate(form=wweek_form)
    @turbogears.error_handler(webimport)
    def importwweek(self, thedate, do_week=False):
        if not do_week:
            gen = WWBL.day_events(thedate)
        else:
            gen = WWBL.week_events(thedate)
        self.generic_import("WWeek", gen)

    def generic_import(self, name, gen):
        not_added = 0
        review_count = 0
        nonreview_count = 0
        for event in gen:
            new_event, flagged = self.import_to_db(event)
            if not new_event:
                not_added += 1
            elif flagged:
                review_count += 1
            else:
                nonreview_count += 1
        turbogears.flash("%s added %d, %d flagged for review, %d skipped" % \
            (name, nonreview_count, review_count, not_added))
        redirect(turbogears.url("/importers/review"))

    @expose()
    def importpollstar(self):
        self.generic_import("Pollstar", pollstar.events())

    @expose()
    def importupcoming(self):
        self.generic_import("Upcoming", br.events())

    @expose()
    def importlastfm(self):
        self.generic_import("last.fm", lastfm.events())

    @expose()
    def importticketswest(self):
        self.generic_import("Ticketswest", ticketswest.events())

    def _set_optional_fields(self, obj, in_dict, field_list):
        model = obj.__class__
        for field in field_list:
            try:
                # truncate if too long
                field_len = getattr(model.q, field).column.length
                in_dict[field] = in_dict[field][:field_len]
                # only set if not set already
                if not getattr(obj, field, None) and len(in_dict[field]):
                    setattr(obj, field, in_dict[field])
            except (KeyError, TypeError):
                pass

    venue_fixup_dict = {
        "Ash Street Saloon":"Ash Street",
        "Abou Karim":"Abou Karim Restaurant",
        "Abu Karim Restaurant":"Abou Karim Restaurant",
        "Alberta St. Public House":"Alberta Street Public House",
        "Arlene Schnitzer Hall":"Arlene Schnitzer Concert Hall",
        "Bridgeport":"Bridgeport Brewpub",
        "Doug Fir Lounge":"Doug Fir",
        "Fez Ballroom and Lounge":"Fez Ballroom",
        "Jax Bar":"Jax",
        "Jimmy Macks":"Jimmy Mak's",
        "Kells Irish Pub":"Kells Irish Restautant & Pub",
        "Koji's":"Koji Osakaya",
        "Laurelthirst":"Laurelthirst Public House",
        "Macadams Bar & Grill":"Macadam's Bar & Grill",
        "Marriott Hotel":"Marriott-Waterfront",
        "Memorial Auditorium":"Memorial Coliseum",
        "Oregon Symphony":"Arlene Schnitzer Concert Hall",
        "Outlaws Bar Grill":"Outlaws Bar & Grill",
        "Rock N Roll Pizza":"Rock 'N' Roll Pizza",
        "Rose Garden Arena":"Rose Garden",
        "Roseland Grill":"Roseland",
        "Roseland Theater":"Roseland",
        "Roseland Theatre":"Roseland",
        "Sabala's at Mt. Tabor":"Sabala's at Mount Tabor",
        "Tom McCall Park":"Tom McCall Waterfront Park",
        "The Rose Garden Arena":"Rose Garden",        
        "The Satyricon":"Satyricon",
        "Washington Park Zoo Amphitheatre":"Oregon Zoo Amphitheatre",
        "White Eagle Saloon and Hotel":"White Eagle",
        "Wonder Cafe":"Cafe Wonder",
    }

    artist_fixup_dict = {
        "+44":"Plus 44",
        "DJ Van Gloryus":"DJ Van Glorious",
        "Van Gloryious":"DJ Van Glorious",
        "hosted by Cory":"Cory",
        "Tamara J. Brown Open Mic":"Tamara J. Brown",
        "DJ Lopez Pure Dance Mix":"DJ Lopez",
        "DJ My Friend Andy":"My Friend Andy",
        "DJ Moisti loves Mr. E":"DJ Moisti",
        "The Fabulous DJ Moisti":"DJ Moisti",
        "Mr. Roboto":"DJ Mr. Roboto",
        "DJ Mr Roboto":"DJ Mr. Roboto",
        "Blues Jam with JR Sims":"JR Sims",
        "DJ King Fader":"King Fader",
        "Open Mic with Chuck Warda":"Chuck Warda",
        "Suicide Club with DJ Nightschool":"DJ Nightschool",
        "Beat Around the Bush with Paula B":"Paula B",
        "Beat Around the Bush with Paula B.":"Paula B",
        "Blues Jam with Suburban Slim":"Suburban Slim",
        "Shut Up and Dance with DJ Gregarious":"DJ Gregarious",
        "Sinferno Caberet with Polly Panic":"Polly Panic",
    }

    def name_fix(self, name):
        return " ".join(name.strip().split())

    def venue_name_fix(self, venue_name):
        venue_name = self.name_fix(venue_name)
        return self.venue_fixup_dict.get(venue_name, venue_name)

    def event_name_fix(self, event_name):
        event_name = event_name.replace("(Boxxes)", "")
        event_name = event_name.replace('"', "")
        event_name = self.name_fix(event_name)
        return event_name

    def artist_name_fix(self, artist_name):
        artist_name = artist_name.replace("with guest", "")
        artist_name = artist_name.replace("and guests", "")
        artist_name = artist_name.replace("and guest", "")
        artist_name = artist_name.replace("and Friends", "")
        artist_name = artist_name.replace("and friends", "")
        artist_name = artist_name.replace("& more", "")
        artist_name = artist_name.replace("(noon)", "")
        artist_name = artist_name.replace("(CD release)", "")
        artist_name = artist_name.replace("(Red Cap Garage)", "")
        artist_name = artist_name.replace("(Boxxes)", "")
        artist_name = artist_name.replace("(Taverna)", "")
        artist_name = artist_name.replace("(Minoan Ballroom)", "")
        artist_name = artist_name.replace("(Saganaki Lounge)", "")
        artist_name = artist_name.replace("(Sideshow Lounge)", "")
        artist_name = artist_name.replace('"', "")
        artist_name = self.name_fix(artist_name)
        artist_name = self.artist_fixup_dict.get(artist_name, artist_name)
        return artist_name

    def artists_clean(self, artists):
        artists = [a for a in artists if a != "with guests"]
        artists = [a for a in artists if a != "and guests"]
        artists = [self.artist_name_fix(a) for a in artists]

        # break all "john foo & susan bar" into separate artists, if "john foo"
        # already exists in the db
        for artist in artists:
            if artist.find("&") != -1:
                artist1, artist2 = artist.split("&", 1)
                try:
                    if not len(artist1.strip()):
                        continue
                    a = Artist.byNameI(artist1)
                    yield artist1.strip()
                    yield artist2.strip()
                except SQLObjectNotFound:
                    yield artist
            else:
                yield artist

    # IMPORTERS MUST YIELD:
    #
    # event dict:
    #   name (req'd)
    #   date (req'd)
    #   source (req'd)
    #   time
    #   description
    #   cost
    #   ages
    #   url
    #   ticket_url
    #   artists = list(unicode) (req'd)
    #   venue = dict:
    #       name (req'd)
    #       url
    #       zip_code
    #       address
    #       phone
    #       description

    def import_to_db(self, event):
        flag_for_review = False
        venue_name = self.venue_name_fix(event['venue']['name'])
        try:
            v = Venue.byNameI(venue_name)
        except SQLObjectNotFound:
            v = Venue(name=venue_name, added_by=identity.current.user)
            flag_for_review = True
        self._set_optional_fields(v, event['venue'], ("address", "phone", "zip_code",
            "url", "description"))

        event_name = self.event_name_fix(event['name'])
        event_date = event["date"]
        event_time = event.get("time")
        if event_time:
            event_time = event_time.lower()
        db_events = Event.selectBy(date=event_date,
            time=event_time, venue=v)
        if db_events.count():
            e = db_events[0]
            new_event = False
        else:
            e = Event(venue=v, name=event_name,
                date=event_date, time=event_time,
                added_by=identity.current.user)
            new_event = True
            try:
                s = Source.byName(event["source"])
            except SQLObjectNotFound:
                s = Source(name=event["source"])
                flag_for_review = True
            e.addSource(s)
        self._set_optional_fields(e, event, ("cost", "ages", "url",
            "description", "ticket_url"))

        for artist in self.artists_clean(event['artists']):
            try:
                a = Artist.byNameI(artist)
            except SQLObjectNotFound:
                a = Artist(name=artist, added_by=identity.current.user)
                flag_for_review = True
            if not e.id in [existing.id for existing in a.events]:
                a.addEvent(e)
        if new_event and not flag_for_review:
            e.approved = datetime.now()
        return (new_event, flag_for_review)

    @expose(template=".templates.importreview")
    def review(self):
        try_to_show = 100
        result = Event.select(Event.q.approved == None, orderBy=(Event.q.cost, Event.q.name))
        total = result.count()
        shown = min(total, try_to_show)
        events = result[:shown]
        return dict(events=events, shown=shown, total=total)

    @expose()
    def reviewsubmit(self, submit, **kw):
        if submit == "Import Checked":
            self.review_import(**kw)
            turbogears.flash("Imported")
        else:
            self.review_delete(**kw)
            turbogears.flash("Deleted")
        redirect(turbogears.url("/importers/review"))

    def review_import(self, **kw):
        e_counter = 0
        now = datetime.now()
        while True:
            try:
                e_id = kw["eid"+str(e_counter)]
            except KeyError:
                break
            e_counter += 1
            if not kw.has_key("accept"+e_id):
                continue
            e = Event.get(e_id)
            e.approved = now
            v = e.venue
            v.approved = now
            for artist in e.artists:
                artist.approved = now

    def delete_event(self, event):
        for a in event.artists:
            event.removeArtist(a)
            a.destroy_if_unused()
        v = event.venue
        event.destroySelf()
        v.destroy_if_unused()

    def review_delete(self, **kw):
        e_counter = 0
        while True:
            try:
                e_id = kw["eid"+str(e_counter)]
            except KeyError:
                break
            e_counter += 1
            if not kw.has_key("accept"+e_id):
                continue
            e = Event.get(e_id)
            self.delete_event(e)

    @expose()
    def reviewpurge(self):
        new_events = Event.select(Event.q.approved == None)
        for event in new_events:
            self.delete_event(event)
        redirect(turbogears.url("/importers/review"))

    def events_likely_dupes(self, events):
        temp_artist_set = set()
        temp_event_set = set()
        for event in events:
            for artist in event.artists:
                if artist.name in temp_artist_set:
                    return True
                else:
                    temp_artist_set.add(artist.name)
            if event.name in temp_event_set:
                return True
            else:
                temp_event_set.add(event.name)
        return False

    @expose(template=".templates.reviewdupes")
    def reviewdupes(self):
        conn = hub.getConnection()
        dupe_results = conn.queryAll("""
            select date, venue_id, count(*)
            from event
            where date >= CURRENT_DATE
            group by venue_id, date
            having count(*) > 1
            """)
        dupe_groups = []
        limit = 5
        for date, venue_id, count in dupe_results:
            possible_dupes = Event.selectBy(date=date, venueID=venue_id)
            if self.events_likely_dupes(possible_dupes):
                dupes = []
                for dupe in possible_dupes:
                    others = set(possible_dupes)
                    others.remove(dupe)
                    dupes.append((dupe, others))
                dupe_groups.append(dupes)
                if len(dupe_groups) >= limit:
                    break
        return dict(dupes=dupe_groups, dupe_count=len(dupe_results),
            artist_list=artist_list)

    @expose()
    def merge_dupe(self, old_id, new_id):
        old = Event.get(old_id)
        new = Event.get(new_id)
        Event.merge(old, new)
        for artist in new.artists:
            if not artist.approved:
                artist.approved = datetime.now()
        redirect(turbogears.url("/importers/reviewdupes"))
