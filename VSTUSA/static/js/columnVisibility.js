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