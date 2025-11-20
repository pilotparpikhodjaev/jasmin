import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: __ENV.K6_VUS ? parseInt(__ENV.K6_VUS) : 50,
  duration: __ENV.K6_DURATION || '2m',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<800'],
  },
};

const API_BASE = __ENV.API_BASE || 'http://localhost:8080/v1';
const API_KEY = __ENV.API_KEY || 'replace-me';

export default function () {
  const payload = JSON.stringify({
    to: '+99890123' + Math.floor(Math.random() * 10000).toString().padStart(4, '0'),
    message: `${Math.floor(Math.random() * 900000 + 100000)} is your OTP.`,
    sender: 'LOADTEST',
  });

  const res = http.post(`${API_BASE}/otp/send`, payload, {
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
    },
  });

  check(res, {
    'status is 201': (r) => r.status === 201,
    'has message_id': (r) => r.json('message_id') !== undefined,
  });

  sleep(1);
}

