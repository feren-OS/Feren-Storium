function gotopage(pagename) {
    window.location.href = (pagename);
}

function gotopackage(packagename) {
    window.location.href = ("packagepage.html?package="+packagename);
}

//FOR FEREN STORIUM DEMO
function mkbuttonapps(packagename) {
    //TODO: Stop this from running multiple times at once
    var newbutton = document.createElement("input");
    newbutton.type = "button";
    newbutton.value = packagename;

    newbutton.addEventListener ("click", function() {
        window.location.href = ("packagepage.html?package="+packagename);
    });

    document.getElementById("appslist").appendChild(newbutton);
}
function mkbuttonthemes(packagename) {
    //TODO: Stop this from running multiple times at once
    var newbutton = document.createElement("input");
    newbutton.type = "button";
    newbutton.value = packagename;

    newbutton.addEventListener ("click", function() {
        window.location.href = ("packagepage.html?package="+packagename);
    });

    document.getElementById("themeslist").appendChild(newbutton);
}
function mkbuttonwebsites(packagename) {
    //TODO: Stop this from running multiple times at once
    var newbutton = document.createElement("input");
    newbutton.type = "button";
    newbutton.value = packagename;

    newbutton.addEventListener ("click", function() {
        window.location.href = ("packagepage.html?package="+packagename);
    });

    document.getElementById("websiteslist").appendChild(newbutton);
}
