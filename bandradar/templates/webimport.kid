<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">

<head>
    <title>BandRadar - Import From Web</title>
</head>

<body>
   <div class="content">

    <h3>Import Mercury?</h3>

    ${mercury_form(action="/importers/importmercury")}

    <h3>Import Willamette Week?</h3>
    <p>Before importing, please verify
    <a href="http://localcut.wweek.com/calendar/wednesday/">this page</a>
    is current for today!</p> 

   <li> <form action="/importers/importwweek" method="post" class="tableform" name="wweek">        
        <input type="submit" class="submitbutton" value="Go" />
    </form></li>

    <h3>Import Pollstar?</h3>

   <li> <form action="/importers/importpollstar" method="post" class="tableform" name="pollstar">        
        <input type="submit" class="submitbutton" value="Go" />
    </form></li>

    <h3>Import Upcoming.org?</h3>

    <li><form action="/importers/importupcoming" method="post" class="tableform" name="upcoming">        
        <input type="submit" class="submitbutton" value="Go" />
    </form></li>

    <h3>Import last.fm?</h3>

    <li><form action="/importers/importlastfm" method="post" class="tableform" name="lastfm">        
        <input type="submit" class="submitbutton" value="Go" />
    </form>
</li>
    <h3>Import TicketsWest?</h3>

   <li> <form action="/importers/importticketswest" method="post" class="tableform" name="lastfm">        
        <input type="submit" class="submitbutton" value="Go" />
    </form></li>
    </div>

</body>
</html>
