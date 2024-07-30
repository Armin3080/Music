const localVideo = document.getElementById('localVideo');
const remoteVideo = document.getElementById('remoteVideo');
const startButton = document.getElementById('startButton');

let localStream;
let peerConnection;
let socket;
const serverUrl = 'ws://82.115.21.174:8080';  // آدرس سرور WebSocket خود را وارد کنید

const servers = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' } // استفاده از STUN سرور گوگل
  ]
};

startButton.onclick = async () => {
  socket = new WebSocket(serverUrl);

  socket.onopen = async () => {
    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    localVideo.srcObject = localStream;

    peerConnection = new RTCPeerConnection(servers);
    peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        socket.send(JSON.stringify({ type: 'candidate', candidate: event.candidate }));
      }
    };
    peerConnection.ontrack = (event) => {
      remoteVideo.srcObject = event.streams[0];
    };

    localStream.getTracks().forEach((track) => {
      peerConnection.addTrack(track, localStream);
    });

    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);
    socket.send(JSON.stringify({ type: 'offer', offer }));
  };

  socket.onmessage = async (message) => {
    const data = JSON.parse(message.data);

    if (data.type === 'offer') {
      await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));
      const answer = await peerConnection.createAnswer();
      await peerConnection.setLocalDescription(answer);
      socket.send(JSON.stringify({ type: 'answer', answer }));
    } else if (data.type === 'answer') {
      await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
    } else if (data.type === 'candidate') {
      await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
    }
  };
};
