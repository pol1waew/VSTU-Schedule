function changeVisibility(id = "") {
    var cds = document.getElementsByName(id + "d");

    if (cds[0].style.visibility == "hidden") {
        cds.forEach((element) => {
            (element).style.visibility = "visible";
            (element).style.lineHeight = "normal";
        });
        document.getElementById(id + "h").style.width = "auto";
    }
    else {
        cds.forEach((element) => {
            (element).style.visibility = "hidden";
            (element).style.lineHeight = "0px";
        });
        document.getElementById(id + "h").style.width = "0%";
    }
}