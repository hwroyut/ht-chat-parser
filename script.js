let isConnected = false;

document.addEventListener('DOMContentLoaded', async () => {
    const statusText = document.querySelector('span.status-text');
    let dotCount = 1;
    while (!isConnected) {
        statusText.textContent = `서버 연결중${'.'.repeat(dotCount)}`;
        if (dotCount < 3) {
            dotCount++;
        } else {
            dotCount = 1;
        }
        await new Promise((resolve) => setTimeout(resolve, 500));
    }
});

const socket = new WebSocket('/ws');

socket.addEventListener('open', () => {
    console.log('WebSocket connection established');
    isConnected = true;
    const statusSymbol = document.querySelector('span.status-symbol');
    statusSymbol.classList.remove('orange');
    statusSymbol.classList.remove('red');
    statusSymbol.classList.add('green');
    const statusText = document.querySelector('span.status-text');
    statusText.textContent = '서버 연결됨';
});
socket.addEventListener('close', () => {
    console.log('WebSocket connection closed');
    isConnected = true;
    const statusSymbol = document.querySelector('span.status-symbol');
    statusSymbol.classList.remove('green');
    statusSymbol.classList.remove('orange');
    statusSymbol.classList.add('red');
    const statusText = document.querySelector('span.status-text');
    statusText.textContent = '서버 연결 끊김';
});
socket.addEventListener('error', (error) => {
    console.error('WebSocket error:', error);
    isConnected = true;
    const statusSymbol = document.querySelector('span.status-symbol');
    statusSymbol.classList.remove('green');
    statusSymbol.classList.remove('orange');
    statusSymbol.classList.add('red');
    const statusText = document.querySelector('span.status-text');
    statusText.textContent = '서버 연결 오류';
});
socket.addEventListener('message', (event) => {
    console.log('Received message:', event.data);
});
