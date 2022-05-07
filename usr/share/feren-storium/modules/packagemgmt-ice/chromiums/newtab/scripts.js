var eng = {},
	current = {},
	fadeDur = 350,
    searchPrefix = "Search ",
    UA=navigator.userAgent;
    
var iceText = "YouTube",
    homeURL = "https://www.youtube.com/?feature=ytca",
    homeIcon = "https://www.gstatic.com/youtube/img/branding/favicon/favicon_192x192.png",
    iceBG = "https://images.unsplash.com/photo-1611162616475-46b635cb6868",
    iceBGCredit = "",
    iceBGURL = "";


//Flavour text
document.getElementById('iceid').innerHTML=iceText;
document.getElementById('icehomelink').href=homeURL;
document.getElementById('icehomebtn').href=homeURL;
document.getElementById('icehomeicon').src=homeIcon;

document.getElementById('title').innerHTML=iceText;
document.getElementById('pageicon').href=homeIcon;

if (!iceBGCredit) document.getElementById('bgurl').innerHTML=null;

document.getElementById('bgparallax').style.backgroundImage="url("+iceBG+")";
document.getElementById('bgcredit').innerHTML=iceBGCredit;
document.getElementById('bgurl').href=iceBGURL;
