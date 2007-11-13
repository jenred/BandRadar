<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'../master.kid'">

<head>
    <title>BandRadar - Event List</title>
</head>

<body>

   <div id="help"><p>BandRadar sends you an email when your tracked events are upcoming.</p><p><img src="/static/images/date_add.png"/><a href="/events/edit">Add an Event</a></p></div>
        <ul id="bandnavlist">    
        <li id ="active"><a href="/events/list/today" id="current">Today</a></li>
        <li><a href="/events/list/tomorrow">Tomorrow</a></li>
        <li><a href="/events/list/yesterday">Yesterday</a></li>
        <li><a href="/events/list/week">Upcoming week</a></li>
        <li><a href="/events/list/all">All upcoming</a></li>
        <li>Events: ${listby} <big>(${count})</big></li>
        </ul>
       
        
  <div id="event">
    <table>
        <tr py:for="event_id, event_name, event_date, venue_name, is_tracked in events">
            <td>
                <a href="/events/${event_id}"><b>${event_name} </b>@${venue_name}</a>
            </td>
            <td>
                ${event_date}
            </td>
            <td>
                ${tg_track_button(tracked=is_tracked, id=event_id, action="/events/dyntrack")}
            </td>
        </tr>
    </table>
 </div>   

</body>
</html>
