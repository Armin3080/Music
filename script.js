const localVideo = document.getElementById('localVideo');
const remoteVideo = document.getElementById('remoteVideo');
const startButton = document.getElementById('startButton');

let localStream;
let peerConnection;
const websocket = new WebSocket('ws://82.115.21.174:8080');  // آدرس IP سرور خود را جایگزین کنید

const config = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' }
    ]
};

websocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch(data.type) {
        case 'offer':
            handleOffer(data.offer);
            break;
        case 'answer':
            handleAnswer(data.answer);
            break;
        case 'candidate':
            handleCandidate(data.candidate);
            break;
    }
};

startButton.onclick = async () => {
    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    localVideo.srcObject = localStream;
    peerConnection = createPeerConnection();
    localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));
    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);
    websocket.send(JSON.stringify({ type: 'offer', offer: offer }));
};

function createPeerConnection() {
    const pc = new RTCPeerConnection(config);
    pc.onicecandidate = (event) => {
        if (event.candidate) {
            websocket.send(JSON.stringify({ type: 'candidate', candidate: event.candidate }));
        }
    };
    pc.ontrack = (event) => {
        remoteVideo.srcObject = event.streams[0];
    };
    return pc;
}

async function handleOffer(offer) {
    if (!peerConnection) {
        peerConnection = createPeerConnection();
        localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));
    }
    await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
    const answer = await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);
    websocket.send(JSON.stringify({ type: 'answer', answer: answer }));
}

async function handleAnswer(answer) {
    await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
}

function handleCandidate(candidate) {
    peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
}
