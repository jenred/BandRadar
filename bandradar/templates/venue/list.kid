<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">

<head>
    <title>BandRadar - Venue List</title>
</head>

<body>
    <div id="searchbox">
        <h2>Search all Venues</h2>
        <?python from bandradar.venues import venue_search_form ?>
        ${venue_search_form(action="/venues/search")}
    </div>

    <div id="list_title">
    </div>

    <h3>Venues with upcoming events
        <span py:if="'admin' in tg.identity.groups">
            ${tg_ButtonWidget(action="/venues/edit", label="Add a new venue")}
        </span>
    </h3>
    <p><em>You will receive a weekly email for upcoming events at any tracked venues.</em>
    </p>
    <br />
    <p py:for="v in venues">
        <p>
            ${track_button(tracked=v['id'] in tracked_venues, id=v['id'], action="/venues/dyntrack")}
            <a href="/venues/${v['id']}">${v['name']}</a>
            <span py:if="v['eventcount']"> (${v['eventcount']} upcoming)</span>
        </p>
    </p>
</body>
</html>
