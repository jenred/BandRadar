<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">

<head>
    <title>BandRadar - Review Duplicates</title>
</head>

<body>
    <table py:for="dupe_group in dupes">
    <tr py:for="dupe, others in dupe_group">
        <td>
            <a href="/events/${dupe.id}"><b py:strip="dupe.approved">${dupe.id} ${dupe.name}</b></a> <span style="font-size:xx-small">(${artist_list(artists=dupe.artists)})</span>
            <br />${dupe.date} ${dupe.time} <b>${dupe.cost}</b> ${dupe.ages} Created ${dupe.fcreated}
        </td>
        <td>
            <p py:for="other in others">
                ${tg_ButtonWidget(action="/importers/merge_dupe/%d/%d" % (other.id, dupe.id), label="Merge from %d" % other.id)}
            </p>
        </td>
    </tr>
    </table>
</body>
</html>
