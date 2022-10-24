var eng = {},
	current = {},
	fadeDur = 350,
    searchPrefix = "Search ",
    UA=navigator.userAgent;
    
var iceText = "YouTube",
    homeURL = "https://www.youtube.com/?feature=ytca",
    homeIcon = "https://www.gstatic.com/youtube/img/branding/favicon/favicon_192x192.png",


//Flavour text
document.getElementById('iceid').innerHTML=iceText;
document.getElementById('icehomelink').href=homeURL;
document.getElementById('icehomebtn').href=homeURL;
document.getElementById('icehomeicon').src=homeIcon;

document.getElementById('title').innerHTML=iceText;
document.getElementById('pageicon').href=homeIcon;
