

// For Global use source.zoom.us:
ZoomMtg.setZoomJSLib('https://source.zoom.us/1.9.5/lib', '/av');

ZoomMtg.preLoadWasm();
ZoomMtg.prepareJssdk();

const zoomMeeting = document.getElementById("zmmtg-root");
