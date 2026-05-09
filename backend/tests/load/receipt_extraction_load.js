import http from 'k6/http';
import { check, sleep } from 'k6';
import { FormData } from 'https://jslib.k6.io/formdata/0.0.2/index.js';

export const options = {
  vus: 5,
  duration: '60s',
  thresholds: {
    http_req_failed: ['rate<0.01'], // less than 1% errors
    http_req_duration: ['p(95)<15000'], // 95% of requests must complete within 15 seconds
  },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000/api/v1';
const TOKEN = __ENV.ACCESS_TOKEN || 'test_token_here';

const binFile = new Uint8Array([255, 216, 255, 224, 0, 16, 74, 70, 73, 70, 0, 1, 1, 1, 0, 72, 0, 72, 0, 0, 255, 217]).buffer;

export default function () {
  const fd = new FormData();
  fd.append('file', http.file(binFile, 'test-receipt.jpg', 'image/jpeg'));

  const params = {
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': `multipart/form-data; boundary=${fd.boundary}`
    },
  };

  const uploadRes = http.post(`${BASE_URL}/receipts/upload`, fd.body(), params);
  
  check(uploadRes, {
    'upload status is 201': (r) => r.status === 201,
    'has receipt id': (r) => r.json('id') !== undefined,
  });

  if (uploadRes.status === 201) {
    const receiptId = uploadRes.json('id');
    
    // Trigger Extraction
    const extractRes = http.post(`${BASE_URL}/receipts/${receiptId}/extract`, null, {
      headers: {
        'Authorization': `Bearer ${TOKEN}`
      }
    });
    
    check(extractRes, {
      'extract status is 202 or 200': (r) => [200, 202].includes(r.status),
    });
  }

  sleep(1);
}
