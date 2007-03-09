<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

<?python
    from bandradar.widgets import track_button
?>

<span xmlns:py="http://purl.org/kid/ns#"
    onclick="button_pushed('${action}', '${id}'); return false;"
    class="button ${track_button.track_str(tracked)}" id="item_${id}">
    <span py:if="not tracked">Untracked</span>
    <span py:if="tracked">Tracked</span>
</span>