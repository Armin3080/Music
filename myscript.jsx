var video = document.getElementById("myVideo");

video.addEventListener("click", function() {
  if (video.muted) {
    video.muted = false;
  }
});
