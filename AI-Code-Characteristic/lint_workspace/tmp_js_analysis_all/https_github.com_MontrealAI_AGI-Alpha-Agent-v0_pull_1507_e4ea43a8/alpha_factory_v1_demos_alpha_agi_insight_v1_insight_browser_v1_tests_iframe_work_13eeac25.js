import test from 'node:test';
import assert from 'node:assert/strict';

// Minimal DOM stubs
let added = 0;
let removed = 0;
let lastHandler;

const windowMock = {
  addEventListener(type, handler) {
    if (type === 'message') {
      added += 1;
      lastHandler = handler;
    }
  },
  removeEventListener(type, handler) {
    if (type === 'message' && handler === lastHandler) {
      removed += 1;
    }
  },
};

const iframeMock = {
  sandbox: '',
  style: {},
  src: '',
  contentWindow: { postMessage() {} },
  remove() {},
};

const documentMock = {
  createElement() {
    return iframeMock;
  },
  body: { appendChild() {} },
};

const URLMock = {
  createObjectURL() {
    return 'blob:xyz';
  },
  revokeObjectURL() {},
};

// Inject mocks
global.window = windowMock;
global.document = documentMock;
global.URL = URLMock;

async function createIframeWorker(url) {
  return new Promise((resolve) => {
    const html = "<script>let w;window.addEventListener('message',e=>{if(e.data.type==='start'){w=new Worker(e.data.url,{type:'module'});w.onmessage=d=>parent.postMessage(d.data,'*')}else if(w){w.postMessage(e.data)}});<\\/script>";
    const iframe = document.createElement('iframe');
    iframe.sandbox = 'allow-scripts';
    iframe.style.display = 'none';
    iframe.src = URL.createObjectURL(new Blob([html], { type: 'text/html' }));
    document.body.appendChild(iframe);
    const obj = {
      postMessage: (m) => iframe.contentWindow.postMessage(m, '*'),
      terminate() {
        iframe.remove();
        URL.revokeObjectURL(iframe.src);
        window.removeEventListener('message', handler);
      },
      onmessage: null,
    };
    const handler = (e) => {
      if (e.source === iframe.contentWindow && obj.onmessage) obj.onmessage(e);
    };
    window.addEventListener('message', handler);
    iframe.onload = () => {
      iframe.contentWindow.postMessage({ type: 'start', url }, '*');
      resolve(obj);
    };
    // immediately simulate load
    iframe.onload();
  });
}

test('terminate removes message listener', async () => {
  const w = await createIframeWorker('x.js');
  assert.equal(added, 1);
  w.terminate();
  assert.equal(removed, 1);
});

