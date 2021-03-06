from turbogears import controllers, expose, redirect, flash, validate, error_handler
from turbogears import identity
from turbogears import widgets as w
from turbogears import validators as v

from model import Event, Venue, Artist, Attendance, UpdateLog, hub
from sqlobject import SQLObjectNotFound, LIKE, func, AND
from datetime import date, datetime, timedelta
import formencode

from bandradar import util
from bandradar.widgets import (BRAutoCompleteField, BRCalendarDatePicker,
                               artist_list, googlemap)

class EitherNameOrArtists(formencode.FancyValidator):
    def validate_python(self, field_dict, state):
        if not field_dict['name'] and not field_dict['artists']:
            raise formencode.Invalid("", field_dict, state,
                error_dict = {'name':"Please give either event name or artists"})


class HelpAboveTableForm(w.TableForm):
    template =  """
    <form xmlns:py="http://purl.org/kid/ns#"
        name="${name}"
        action="${action}"
        method="${method}"
        class="tableform"
        py:attrs="form_attrs"
        >
        <div py:for="field in hidden_fields" 
            py:replace="field.display(value_for(field), **params_for(field))" 
        />
        <table border="0" cellspacing="0" cellpadding="2" py:attrs="table_attrs">
            <tr py:for="i, field in enumerate(fields)" 
                class="${i%2 and 'odd' or 'even'}"
            >
                <th>
                    <label class="fieldlabel" for="${field.field_id}" py:content="field.label" />
                </th>
                <td>
                    <span py:if="field.help_text" class="fieldhelp" py:content="field.help_text" />
                    <br py:if="field.help_text" />
                    <span py:replace="field.display(value_for(field), **params_for(field))" />
                    <span py:if="error_for(field)" class="fielderror" py:content="error_for(field)" />
                </td>
            </tr>
            <tr>
                <td> </td>
                <td py:content="submit.display(submit_text)" />
            </tr>
        </table>
    </form>
    """
    

class EventWidgetList(w.WidgetsList):
    id = w.HiddenField(validator=v.Int)
    name = w.TextField(label="Event Name", help_text="If different from artists' names",
        validator=v.UnicodeString(strip=True), attrs=dict(size=40))
    artists = w.TextArea(help_text="Enter only artist names, one per line", rows=4, cols=40,
        validator=v.UnicodeString(strip=True))
    venue = BRAutoCompleteField("/venues/dynsearch", label="Venue", take_focus=False)
    date = BRCalendarDatePicker(not_empty=True)
    time = w.TextField(attrs=dict(maxlength=40))
    cost = w.TextField(attrs=dict(maxlength=120))
    ages = w.TextField(attrs=dict(maxlength=40))
    description = w.TextArea(rows=3, cols=40)
    url = w.TextField(label="Website", attrs=dict(size=50, maxlength=256),
        validator=v.Any(v.URL, v.Empty))

class EventSchema(v.Schema):
    chained_validators = [EitherNameOrArtists(strip=True)]

event_form = HelpAboveTableForm(fields=EventWidgetList(), name="event", submit_text="Save",
                         validator=EventSchema())

class EventController(controllers.Controller, util.RestAdapter):

    @expose(template=".templates.event.list")
    def list(self, listby="today", orderby="alpha"):

        def events_in_period(day_delta, day_count=1):
            conn = hub.getConnection()

            start_date = date.today() + timedelta(day_delta)
            where_clause = AND(Event.q.date >= start_date, Event.q.approved != None)
            if day_count != 0:
                end_date = start_date + timedelta(day_count-1)
                where_clause = AND(where_clause, Event.q.date <= end_date)

            events = conn.queryAll("""
                select event.id, event.name, event.date, venue.name
                from event, venue
                where event.venue_id = venue.id
                    AND %s
                order by event.date, event.name
                """ % where_clause)

            day_result = {}
            if identity.current.user:
                tracked_event_ids = [a.id for a in identity.current.user.events]
            else:
                tracked_event_ids = []
            for event_id, event_name, event_date, venue_name in events:
                is_tracked = event_id in tracked_event_ids
                yield (event_id, event_name, event_date, venue_name, is_tracked)

        if listby == "today":
            result = events_in_period(0)
        elif listby == "tomorrow":
            result = events_in_period(1)
        elif listby == "yesterday":
            result = events_in_period(-1)
        elif listby == "week":
            result = events_in_period(0, 7)
        elif listby == "all":
            result = events_in_period(0, 0)
        result = list(result)

        return dict(events=result, count=len(result), listby=listby)

    @expose(template=".templates.event.show")
    def show(self, id):
        try:
            e = Event.get(id)
            is_tracked = identity.current.user and e in identity.current.user.events
        except SQLObjectNotFound:
            flash("Event not found")
            util.redirect("/events/list")
        return dict(event=e, artist_list=artist_list, googlemap=googlemap,
            description=util.desc_format(e.description), is_tracked=is_tracked)

    @expose()
    @identity.require(identity.not_anonymous())
    def edit(self, id=0, **kw):
        form_vals = {}
        template = ".templates.event.add"
        if id:
            try:
                e = Event.get(id)
                form_vals = util.so_to_dict(e)
                form_vals['artists'] = "\n".join([a.name for a in e.artists])
                form_vals['venue'] = dict(text=e.venue.name)
                template = ".templates.event.edit"
            except SQLObjectNotFound:
                pass
        else:
            form_vals = dict(id=id)
        try:
            a = Artist.get(int(kw['artist_prefill']))
            form_vals['artists'] = a.name
        except (SQLObjectNotFound, KeyError):
            pass
        try:
            v = Venue.get(int(kw['venue_prefill']))
            flash(form_vals)
            form_vals['venue'] = dict(text=v.name)
        except (SQLObjectNotFound, KeyError):
            pass

        return dict(tg_template=template, event_form=event_form, form_vals=form_vals)

    @expose()
    @validate(form=event_form)
    @error_handler(edit)
    @identity.require(identity.not_anonymous())
    def save(self, id, **kw):
        try:
            v = Venue.byName(kw['venue']['text'])
        except SQLObjectNotFound:
            v = Venue(name=kw['venue']['text'], added_by=identity.current.user)

        artists = kw.pop('artists')
        if not artists:
            artists = ""
        artist_name_list = [artist.strip() for artist in artists.split('\n')]
        # elim blank items in list
        artist_name_list = [artist for artist in artist_name_list if artist]
        if not kw.get('name'):
            kw['name'] = ", ".join(artist_name_list)

        # updating
        if id:
            try:
                e = Event.get(id)
                flash_msg = "updated"
            except SQLObjectNotFound:
                flash("Database error, please try again")
                redirect("/")
        # inserting
        else:
            e = Event(name=kw['name'], date=kw['date'], time=kw['time'], venue=v,
                added_by=identity.current.user)
            # mark user as going to all added events by default
            if not "admin" in identity.current.groups:
                att = Attendance(user=identity.current.user, event=e, planning_to_go=True)
            flash_msg = "added, will be reviewed and posted within 24 hrs"

        del kw['venue']
        e.set(**e.clean_dict(kw))
        old_venue = e.venue
        e.venue = v
        old_venue.destroy_if_unused()
        old_artists = set([a.name for a in e.artists])
        # add new artists
        artist_list = []
        for artist in artist_name_list:
            try:
                a = Artist.byNameI(artist)
                if not a in e.artists:
                    e.addArtist(a)
            except SQLObjectNotFound:
                a = Artist(name=artist, added_by=identity.current.user)
                e.addArtist(a)
            artist_list.append(a)
        # remove old artists
        for artist in e.artists:
            if artist not in artist_list:
                e.removeArtist(artist)
                artist.destroy_if_unused()
        new_artists = set([a.name for a in e.artists])
        # approve all artists at approved events
        if e.approved:
            for artist in e.artists:
                if not artist.approved:
                    artist.approved = datetime.now()
        # add entry to UpdateLog
        if old_artists != new_artists and e.approved:
            u = UpdateLog(
                changed_by=identity.current.user.id,
                table_name="artist_event",
                table_id=e.id,
                attrib_name="artists",
                attrib_old_value=old_artists,
                attrib_new_value=new_artists
                )
        flash("Event %s" % flash_msg)
        util.redirect("/events/%s" % e.id)

    @expose()
    @identity.require(identity.not_anonymous())
    def track(self, id, viewing="no", planning=False, went=False, comment=None):
        u = identity.current.user
        try:
            e = Event.get(id)
            try:
                att = Attendance.selectBy(user=u, event=e)[0]
            except IndexError:
                att = Attendance(user=u, event=e)
            att.planning_to_go = planning
            att.attended = went
            att.comment = comment
        except SQLObjectNotFound:
            flash("Event not found")
            redirect("/")
        if viewing == "no":
            util.redirect_previous()
        else:
            util.redirect("/events/%s" % e.id)

    @expose()
    @identity.require(identity.not_anonymous())
    def untrack(self, id, viewing="no"):
        u = identity.current.user
        try:
            e = Event.get(id)
            atts = Attendance.selectBy(user=u, event=e)
            for att in atts:
                att.destroySelf()
        except SQLObjectNotFound:
            flash("Event not found")
            redirect("/")
        if viewing == "no":
            util.redirect_previous()
        else:
            util.redirect("/events/%s" % e.id)

    @expose("json", fragment=True)
    @identity.require(identity.not_anonymous())
    def dyntrack(self, id, track):
        u = identity.current.user
        ret = "Error"
        try:
            e = Event.get(id)
            if track == "true" and e not in u.events:
                try:
                    att = Attendance.selectBy(user=u, event=e)[0]
                except IndexError:
                    att = Attendance(user=u, event=e)
                att.planning_to_go = True
                ret = "Tracked"
            if track == "false" and e in u.events:
                atts = Attendance.selectBy(user=u, event=e)
                for att in atts:
                    att.destroySelf()
                ret = "Untracked"
        except SQLObjectNotFound:
            pass
        return ret

    @expose()
    @identity.require(identity.in_group("admin"))
    def delete(self, id):
        try:
            e = Event.get(id)
            e.destroySelf()
            flash("Deleted")
        except SQLObjectNotFound:
            flash("Delete failed")
        util.redirect("/events/list")

