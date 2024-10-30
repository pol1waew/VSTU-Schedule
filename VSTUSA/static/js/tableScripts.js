function changeVisibility(elementId = "", entryId) {
    var cds = document.getElementsByName(elementId + "d" + entryId);

    if (cds[0].style.visibility == "hidden") {
        cds.forEach((element) => {
            (element).style.visibility = "visible";
            (element).style.lineHeight = "normal";
        });
        document.getElementById(elementId + "h"  + entryId).style.width = "auto";
    }
    else {
        cds.forEach((element) => {
            (element).style.visibility = "hidden";
            (element).style.lineHeight = "0px";
        });
        document.getElementById(elementId + "h"  + entryId).style.width = "0%";
    }
}

function spanSameRows() {
    var tables = document.getElementsByTagName("table");

    for (var i = 0; i < tables.length; i++) {
        var rows = document.getElementsByName('r' + (i + 1));
        
        // If day contains only one lesson skip that day
        if (rows.length == 1) continue;

        // length - 1 because last entry cannot have lower neighbour
        for (var n = 0; n < rows.length - 1; n++) {
            if (rows[n].children[1].textContent == rows[n + 1].children[1].textContent) {
                rows[n + 1].deleteCell(3);
                rows[n].children[3].rowSpan = 2;
                rows[n + 1].deleteCell(2);
                rows[n].children[2].rowSpan = 2;
                rows[n + 1].deleteCell(1);
                rows[n].children[1].rowSpan = 2;
            }
            n++;
        }
    }
}